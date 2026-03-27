"""Preset management utilities for sim-to-real."""

import logging
import os

import numpy as np

from src.model.params.integrators import MLModel
from src.model.params.sim_to_real import SimToRealParams as _P
from .data_utils import _PRESET_LABELS, _PRESETS_NPZ, _MODELS_PKL
from .model_utils import _predict_trajectory, load_trained_models

log = logging.getLogger(__name__)


def compute_and_save_presets(
    path: str = _PRESETS_NPZ,
    models_path: str | None = None,
    ci_key: str = "pres_standard",
    progress_cb=None,
) -> None:
    """Pré-calcule les trajectoires prédites pour les 2 modèles (RL/MLP).

    Charge les modèles entraînés depuis le fichier .pkl et prédit les
    trajectoires pour la CI donnée. Sauvegarde le résultat dans path.

    Args:
        path       : chemin du fichier .npz de sortie
        models_path: chemin du fichier .pkl contenant les modèles
        ci_key     : clé du preset de CI dans SimToRealParams.PRESETS
        progress_cb: callback de progression (current, total, msg)
    """
    from .data_utils import _PRESET_N_SIMS

    all_models = load_trained_models(models_path or _MODELS_PKL)
    if not all_models:
        log.error("compute_and_save_presets : modèles manquants dans %s",
                  models_path or _MODELS_PKL)
        return

    # Utiliser le meilleur contexte disponible (le plus grand n_sims)
    available_n = [k for k in _PRESET_N_SIMS if k in all_models]
    if not available_n:
        # Fallback : structure plate (ancien format)
        models: dict = all_models
    else:
        models = all_models[max(available_n)]

    presets = _P.PRESETS
    ci = presets.get(ci_key, presets[next(iter(presets))])
    r0, v0, phi0 = ci["r0"], ci["v0"], ci["phi0"]

    arrays: dict[str, np.ndarray] = {}
    total_steps = len(_PRESET_LABELS)

    for step_i, (model_tag, key_x, key_y) in enumerate([
        ("rl",  "lr_x",  "lr_y"),
        ("mlp", "mlp_x", "mlp_y"),
    ]):
        if progress_cb:
            progress_cb(step_i, total_steps, f"Prédiction {_PRESET_LABELS[step_i]}…")

        model_x = models.get(key_x)
        model_y = models.get(key_y)
        if model_x is None or model_y is None:
            log.warning("compute_and_save_presets : modèle '%s' introuvable", key_x)
            continue

        pred = _predict_trajectory(model_x, model_y, r0, v0, phi0)
        arrays[f"pred_{model_tag}"] = pred
        arrays[f"meta_{model_tag}"] = np.zeros(4, dtype=np.float32)

    if progress_cb:
        progress_cb(total_steps, total_steps, "Sauvegarde…")

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez_compressed(path, **arrays)  # type: ignore[arg-type]
    log.info("Presets sauvegardés : %s", path)


def load_presets(path: str = _PRESETS_NPZ) -> dict | None:
    """Charge les presets pré-calculés.

    Retourne un dict :
      {
        "rl":  {"pred_np": (605,2), "metrics": {...}, "model_type": MLModel.LINEAR},
        "mlp": {"pred_np": (605,2), "metrics": {...}, "model_type": MLModel.MLP},
      }
    ou None si le fichier est absent.
    """
    if not os.path.exists(path):
        return None
    try:
        data = np.load(path)
    except Exception:
        return None

    presets: dict = {}
    for model_tag, model_type in [("rl", MLModel.LINEAR), ("mlp", MLModel.MLP)]:
        pred_key = f"pred_{model_tag}"
        meta_key = f"meta_{model_tag}"
        if pred_key not in data or meta_key not in data:
            continue
        meta = data[meta_key]
        presets[model_tag] = {
            "pred_np": data[pred_key],
            "metrics": {
                "r2_x":   float(meta[0]),
                "r2_y":   float(meta[1]),
                "rmse_x": float(meta[2]),
                "rmse_y": float(meta[3]),
            },
            "model_type": model_type,
            "label": "RL" if model_tag == "rl" else "MLP",
        }
    return presets if presets else None


def presets_are_ready(path: str = _PRESETS_NPZ) -> bool:
    """Retourne True si le fichier de presets existe et contient les 2 entrées."""
    if not os.path.exists(path):
        return False
    try:
        data = np.load(path)
        return all(f"pred_{m}" in data for m in ("rl", "mlp"))
    except Exception:
        return False
