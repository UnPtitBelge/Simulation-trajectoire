"""Logique d'entraînement pour les deux modèles step.

Entraînement synthétique : lit les chunks .npz un par un, libère la RAM
entre chaque chunk. Les scalers sont fittés sur le premier chunk puis
gardés fixes pour tout l'entraînement.

Entraînement réel : charge le CSV de tracking, convertit en polaire,
extrait les paires (état_t, état_{t+1}).
"""

import gc
import logging
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


def _train_one_context(
    chunk_paths: list[Path],
    models_dir: Path,
    context_name: str,
) -> None:
    """Entraîne LinearStepModel et MLPStepModel sur les chunks donnés."""
    log.info("Contexte %s : %d chunks", context_name, len(chunk_paths))

    # ── Régression linéaire ──
    lr_model = LinearStepModel()
    for i, path in enumerate(chunk_paths):
        X, y = _chunk_to_pairs(path)
        lr_model.partial_fit(X, y)
        del X, y
        gc.collect()
        if (i + 1) % 10 == 0:
            log.info("  LR — chunk %d/%d", i + 1, len(chunk_paths))

    lr_model.save(models_dir / f"synth_linear_{context_name}.pkl")
    del lr_model
    gc.collect()
    log.info("  LinearStepModel [%s] sauvegardé", context_name)

    # ── MLP ──
    mlp_model = MLPStepModel()
    for i, path in enumerate(chunk_paths):
        X, y = _chunk_to_pairs(path)
        mlp_model.partial_fit(X, y)
        del X, y
        gc.collect()
        if (i + 1) % 10 == 0:
            log.info("  MLP — chunk %d/%d", i + 1, len(chunk_paths))

    mlp_model.save(models_dir / f"synth_mlp_{context_name}.pkl")
    del mlp_model
    gc.collect()
    log.info("  MLPStepModel [%s] sauvegardé", context_name)


# ── API publique ───────────────────────────────────────────────────────────────


def train_synth(data_dir: Path, models_dir: Path, contexts: dict) -> None:
    """Entraîne 2 × len(contexts) modèles sur les données synthétiques.

    contexts = {"10pct": 0.10, "50pct": 0.50, "100pct": 1.00}
    """
    all_chunks = sorted(data_dir.glob("chunk_*.npz"))
    if not all_chunks:
        raise FileNotFoundError(f"Aucun chunk trouvé dans {data_dir}")

    models_dir.mkdir(parents=True, exist_ok=True)
    n_total = len(all_chunks)

    for name, fraction in contexts.items():
        n_chunks = max(1, int(n_total * fraction))
        _train_one_context(all_chunks[:n_chunks], models_dir, name)


def train_real(csv_path: Path, tracking_cfg: dict) -> tuple:
    """Charge le CSV de tracking, entraîne LR + MLP, retourne (lr_model, mlp_model).

    Les modèles sont retournés en mémoire (pas sauvegardés sur disque).
    """
    df = pd.read_csv(csv_path, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()

    cx = tracking_cfg["center_x"]
    cy = tracking_cfg["center_y"]
    ppm = tracking_cfg["px_per_meter"]

    # Conversion pixels → mètres et coordonnées polaires
    pairs_X, pairs_y = [], []

    for _, group in df.groupby("expID"):
        group = group.sort_values("temps")
        xm = (group["x"].values - cx) / ppm
        ym = (group["y"].values - cy) / ppm
        vxm = group["speedX"].values / ppm
        vym = group["speedY"].values / ppm

        r = np.sqrt(xm**2 + ym**2)
        theta = np.arctan2(ym, xm)
        vr = (xm * vxm + ym * vym) / np.maximum(r, 1e-6)
        vtheta = (xm * vym - ym * vxm) / np.maximum(r, 1e-6)

        states = np.column_stack([r, theta, vr, vtheta])
        if len(states) < 2:
            continue
        pairs_X.append(states[:-1])
        pairs_y.append(states[1:])

    X_all = np.vstack(pairs_X).astype(np.float32)
    y_all = np.vstack(pairs_y).astype(np.float32)

    X_feat = state_to_features(X_all)
    y_feat = state_to_features(y_all)

    lr_model = LinearStepModel()
    lr_model.partial_fit(X_feat, y_feat)

    mlp_model = MLPStepModel()
    mlp_model.partial_fit(X_feat, y_feat)

    del X_feat, y_feat, X_all, y_all
    gc.collect()

    return lr_model, mlp_model
