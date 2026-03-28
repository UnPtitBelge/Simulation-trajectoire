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


def compute_exp_centers(df: pd.DataFrame, tracking_cfg: dict) -> dict:
    """Estime le centre du cône pour chaque expérience depuis sa position finale.

    Algorithme :
      1. Pour chaque expérience, médiane des 15 dernières positions → endpoint_i.
      2. Centre de référence global = médiane de tous les endpoints.
      3. Outliers (endpoint à > 2 × MAD du centre de référence) → remplacés par
         le centre de référence.
      4. Chaque expérience est centrée sur son propre endpoint (ou le centre de
         référence pour les outliers).

    Cela corrige les offsets caméra inter-expériences sans dépendre de
    center_x/center_y dans la config (qui peut être approximatif).

    Retourne {expID: (cx_px, cy_px)}.
    """
    last_n = 15  # frames finales pour estimer la position d'arrêt

    raw: dict = {}
    for exp_id, group in df.groupby("expID"):
        tail   = group.sort_values("temps").tail(last_n)
        raw[exp_id] = (float(tail["x"].median()), float(tail["y"].median()))

    all_x = np.array([v[0] for v in raw.values()])
    all_y = np.array([v[1] for v in raw.values()])
    cx_ref = float(np.median(all_x))
    cy_ref = float(np.median(all_y))

    # Seuil outlier : 2 × MAD (Median Absolute Deviation) sur la distance au centre
    dists  = np.sqrt((all_x - cx_ref) ** 2 + (all_y - cy_ref) ** 2)
    mad    = float(np.median(np.abs(dists - np.median(dists))))
    thresh = max(2 * mad, 50.0)   # au moins 50 px de tolérance

    n_valid = int((dists <= thresh).sum())
    log.info(
        "compute_exp_centers : centre de référence (%.1f, %.1f) px, "
        "%d/%d expériences dans le seuil (±%.0f px)",
        cx_ref, cy_ref, n_valid, len(raw), thresh,
    )

    return {
        eid: (cx, cy) if np.sqrt((cx - cx_ref) ** 2 + (cy - cy_ref) ** 2) <= thresh
             else (cx_ref, cy_ref)
        for eid, (cx, cy) in raw.items()
    }


def _iter_real_pairs(csv_path: Path, tracking_cfg: dict):
    """Génère (X_feat, y_feat) expérience par expérience sans tout charger en RAM.

    Coordonnées en pixels centrées sur le centre propre à chaque expérience
    (correction de l'offset caméra via compute_exp_centers).
    Les vitesses (speedX, speedY) sont invariantes à la translation.
    """
    df = pd.read_csv(csv_path, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()

    centers = compute_exp_centers(df, tracking_cfg)

    for exp_id, group in df.groupby("expID"):
        group = group.sort_values("temps")
        cx, cy = centers[exp_id]
        xc = group["x"].values     - cx
        yc = group["y"].values     - cy
        vx = group["speedX"].values
        vy = group["speedY"].values

        r      = np.sqrt(xc**2 + yc**2)
        theta  = np.arctan2(yc, xc)
        vr     = (xc * vx + yc * vy) / np.maximum(r, 1e-6)
        vtheta = (xc * vy - yc * vx) / np.maximum(r, 1e-6)

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
