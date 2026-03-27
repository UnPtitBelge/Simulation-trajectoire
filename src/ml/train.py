"""Logique d'entraînement pour les deux modèles step.

Entraînement synthétique : lit les chunks .npz un par un, libère la RAM
entre chaque chunk. Les scalers sont fittés sur le premier chunk puis
gardés fixes pour tout l'entraînement.

Entraînement réel : charge le CSV de tracking, convertit en polaire,
extrait les paires (état_t, état_{t+1}).
"""

import gc
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from ml.models import LinearStepModel, MLPStepModel, state_to_features

log = logging.getLogger(__name__)


# ── Utilitaires ───────────────────────────────────────────────────────────────


def _chunk_to_pairs(chunk_path: Path):
    """Charge un chunk .npz et retourne (X_features, y_features)."""
    data = np.load(chunk_path)
    X = state_to_features(data["X"].astype(np.float32))
    y = state_to_features(data["y"].astype(np.float32))
    return X, y


def _train_lr_context(
    chunk_paths: list[Path],
    models_dir: Path,
    context_name: str,
) -> str:
    """Entraîne LinearStepModel sur les chunks donnés. Retourne le nom du fichier sauvegardé.

    Défini au niveau module pour être picklable par ProcessPoolExecutor.
    """
    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger(__name__)
    _log.info("LR [%s] : %d chunks", context_name, len(chunk_paths))

    lr_model = LinearStepModel()
    for i, path in enumerate(chunk_paths):
        X, y = _chunk_to_pairs(path)
        lr_model.partial_fit(X, y)
        del X, y
        gc.collect()
        if (i + 1) % 10 == 0:
            _log.info("  LR [%s] — chunk %d/%d", context_name, i + 1, len(chunk_paths))

    name = f"synth_linear_{context_name}.pkl"
    lr_model.save(models_dir / name)
    _log.info("  LinearStepModel [%s] sauvegardé", context_name)
    return name


def _train_mlp_context(
    chunk_paths: list[Path],
    models_dir: Path,
    context_name: str,
) -> str:
    """Entraîne MLPStepModel sur les chunks donnés. Retourne le nom du fichier sauvegardé.

    Défini au niveau module pour être picklable par ProcessPoolExecutor.
    """
    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger(__name__)
    _log.info("MLP [%s] : %d chunks", context_name, len(chunk_paths))

    mlp_model = MLPStepModel()
    for i, path in enumerate(chunk_paths):
        X, y = _chunk_to_pairs(path)
        mlp_model.partial_fit(X, y)
        del X, y
        gc.collect()
        if (i + 1) % 10 == 0:
            _log.info("  MLP [%s] — chunk %d/%d", context_name, i + 1, len(chunk_paths))

    name = f"synth_mlp_{context_name}.pkl"
    mlp_model.save(models_dir / name)
    _log.info("  MLPStepModel [%s] sauvegardé", context_name)
    return name


# ── API publique ───────────────────────────────────────────────────────────────


def train_synth(
    data_dir: Path,
    models_dir: Path,
    contexts: dict,
    n_workers: int = 1,
) -> None:
    """Entraîne 2 × len(contexts) modèles sur les données synthétiques.

    contexts  = {"10pct": 0.10, "50pct": 0.50, "100pct": 1.00}
    n_workers = 1 → séquentiel ; > 1 → ProcessPoolExecutor (LR et MLP en parallèle).

    Avec n_workers = 6, les 6 modèles (3 contextes × 2 algos) tournent simultanément.
    Chaque worker ne charge qu'un chunk à la fois → RAM proportionnelle à n_workers.
    """
    all_chunks = sorted(data_dir.glob("chunk_*.npz"))
    if not all_chunks:
        raise FileNotFoundError(f"Aucun chunk trouvé dans {data_dir}")

    models_dir.mkdir(parents=True, exist_ok=True)
    n_total = len(all_chunks)

    # Construction de la liste des tâches (fn, chunk_paths, models_dir, context_name)
    tasks: list[tuple] = []
    for name, fraction in contexts.items():
        n_chunks = max(1, int(n_total * fraction))
        paths = all_chunks[:n_chunks]
        tasks.append((_train_lr_context,  paths, models_dir, name))
        tasks.append((_train_mlp_context, paths, models_dir, name))

    log.info("%d modèles à entraîner, %d worker(s)", len(tasks), n_workers)

    if n_workers == 1:
        for fn, *args in tasks:
            fn(*args)
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {
                executor.submit(fn, *args): f"{fn.__name__}_{args[2]}"
                for fn, *args in tasks
            }
            for future in as_completed(futures):
                label = futures[future]
                try:
                    saved = future.result()
                    log.info("✓ %s", saved)
                except Exception as exc:
                    log.error("✗ Erreur [%s] : %s", label, exc)
                    raise


def _iter_real_pairs(csv_path: Path, tracking_cfg: dict):
    """Génère (X_feat, y_feat) expérience par expérience sans tout charger en RAM."""
    df = pd.read_csv(csv_path, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()

    cx  = tracking_cfg["center_x"]
    cy  = tracking_cfg["center_y"]
    ppm = tracking_cfg["px_per_meter"]

    for _, group in df.groupby("expID"):
        group = group.sort_values("temps")
        xm  = (group["x"].values - cx) / ppm
        ym  = (group["y"].values - cy) / ppm
        vxm = group["speedX"].values / ppm
        vym = group["speedY"].values / ppm

        r      = np.sqrt(xm**2 + ym**2)
        theta  = np.arctan2(ym, xm)
        vr     = (xm * vxm + ym * vym) / np.maximum(r, 1e-6)
        vtheta = (xm * vym - ym * vxm) / np.maximum(r, 1e-6)

        states = np.column_stack([r, theta, vr, vtheta]).astype(np.float32)
        if len(states) < 2:
            continue
        yield state_to_features(states[:-1]), state_to_features(states[1:])


def train_real(csv_path: Path, tracking_cfg: dict, n_passes: int = 3) -> tuple:
    """Charge le CSV de tracking, entraîne LR + MLP, retourne (lr_model, mlp_model).

    Entraîne les deux modèles dans le même pass (une seule lecture du CSV par pass).
    Les modèles sont retournés en mémoire (pas sauvegardés sur disque).
    """
    lr_model  = LinearStepModel()
    mlp_model = MLPStepModel()

    for pass_idx in range(n_passes):
        log.info("Entraînement réel — pass %d/%d", pass_idx + 1, n_passes)
        for X_feat, y_feat in _iter_real_pairs(csv_path, tracking_cfg):
            lr_model.partial_fit(X_feat, y_feat)
            mlp_model.partial_fit(X_feat, y_feat)
        gc.collect()

    return lr_model, mlp_model
