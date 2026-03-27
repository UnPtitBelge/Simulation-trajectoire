"""Preset management utilities for sim-to-real."""

import logging
import os

import numpy as np

from src.model.params.integrators import MLModel

from .data_utils import _PRESETS_NPZ

log = logging.getLogger(__name__)


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
                "r2_x": float(meta[0]),
                "r2_y": float(meta[1]),
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
