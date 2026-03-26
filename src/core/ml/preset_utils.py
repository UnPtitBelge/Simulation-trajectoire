"""Preset management utilities for sim-to-real."""

import os

import numpy as np

from .data_utils import _PRESET_LABELS,  _N_IN, _N_OUT, _PRESETS_NPZ, _PRESET_LABELS
from .model_utils import _predict_trajectory, train_and_evaluate, save_trained_models


def compute_and_save_presets(
    path: str = _PRESETS_NPZ,
    models_path: str = None,
    ci_key: str = "nominale",
    progress_cb=None,
) -> None:
    """Pré-calcule les trajectoires prédites pour les 2 modèles (RL/MLP).

    Args:
        path       : chemin du fichier .npz de sortie
        models_path: chemin du fichier .pkl pour sauvegarder les modèles
        ci_key     : clé du preset de CI ("nominale", "pres_standard", etc.)
        progress_cb: callback de progression (current, total, msg)
    """
    ci = _P.PRESENTATION_PRESETS.get(ci_key, _P.PRESENTATION_PRESETS["nominale"])
    r0, v0, phi0 = ci["r0"], ci["v0"], ci["phi0"]

    arrays: dict[str, np.ndarray] = {}
    models_dict: dict[str, dict] = {}  # Structure : {model_type: {model_name: model}}
    total_steps = len(_PRESET_LABELS)

    for step_i, model_type in enumerate([_P.MLModel.LINEAR, _P.MLModel.MLP]):
        label = _PRESET_LABELS[step_i]
        config_key = model_type.value
        
        if progress_cb:
            progress_cb(step_i, total_steps, f"Entraînement modèle {label}…")

        data = load_pool()
        if data is None:
            log.error("compute_and_save_presets : pool manquant")
            continue
        result = train_and_evaluate(data["trajectories"])

        # Sauvegarder les modèles
        models_dict[config_key] = {
            "rl_x": result["lr_x"],
            "rl_y": result["lr_y"],
            "mlp_x": result["mlp_x"],
            "mlp_y": result["mlp_y"],
        }

        # RL
        pred_rl = _predict_trajectory(result["lr_x"], result["lr_y"], r0, v0, phi0)
        m_rl = result["metrics_lr"]
        arrays[f"pred_rl"] = pred_rl
        arrays[f"meta_rl"] = np.array(
            [m_rl["r2_x"], m_rl["r2_y"], m_rl["rmse_x"], m_rl["rmse_y"]],
            dtype=np.float32,
        )

        # MLP
        pred_mlp = _predict_trajectory(result["mlp_x"], result["mlp_y"], r0, v0, phi0)
        m_mlp = result["metrics_mlp"]
        arrays[f"pred_mlp"] = pred_mlp
        arrays[f"meta_mlp"] = np.array(
            [m_mlp["r2_x"], m_mlp["r2_y"], m_mlp["rmse_x"], m_mlp["rmse_y"]],
            dtype=np.float32,
        )

    if progress_cb:
        progress_cb(total_steps, total_steps, "Sauvegarde…")

    # Sauvegarder les trajectoires prédites (npz)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez_compressed(path, **arrays)
    log.info("Presets sauvegardés : %s", path)
    
    # Sauvegarder les modèles entraînés (pickle)
    if models_path:
        save_trained_models(models_dict, models_path)


def load_presets(path: str = _PRESETS_NPZ) -> dict | None:
    """Charge les presets pré-calculés.

    Retourne un dict :
      {
        "rl":  {"pred_np": (605,2), "metrics": {...}, "model_type": MLModel.LINEAR, "label": "RL"},
        "mlp": {"pred_np": (605,2), "metrics": {...}, "model_type": MLModel.MLP, "label": "MLP"},
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
    for model_tag, model_type in [("rl", _P.MLModel.LINEAR), ("mlp", _P.MLModel.MLP)]:
        pred_key = f"pred_{model_tag}"
        meta_key = f"meta_{model_tag}"
        if pred_key not in data or meta_key not in data:
            continue
        meta = data[meta_key]
        key = f"{model_tag}"
        presets[key] = {
            "pred_np": data[pred_key],                   # (605, 2)
            "metrics": {
                "r2_x": float(meta[0]),
                "r2_y": float(meta[1]),
                "rmse_x": float(meta[2]),
                "rmse_y": float(meta[3]),
            },
            "model_type": model_type,
            "label": f"{'RL' if model_tag == 'rl' else 'MLP'}",
        }
    return presets if presets else None


def presets_are_ready(path: str = _PRESETS_NPZ) -> bool:
    """Retourne True si le fichier de presets existe et contient les 2 entrées."""
    if not os.path.exists(path):
        return False
    try:
        data = np.load(path)
        expected = [f"pred_{m}" for m in ("rl", "mlp")]
        return all(k in data for k in expected)
    except Exception:
        return False