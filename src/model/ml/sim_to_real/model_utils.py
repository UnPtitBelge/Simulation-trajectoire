"""Model training and preset management utilities."""

import logging
import os
import pickle

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data_utils import (
    _N_IN, _N_OUT, _PRESETS_NPZ, _MODELS_PKL, _MAX_DISPLAY_TRAJS,
    load_pool, _run_cone, _make_feat,
)

_CACHED_MODELS: dict | None = None

log = logging.getLogger(__name__)

# ── Fonctions de prédiction et entraînement ──────────────────────────────────

def _predict_trajectory(model_x, model_y, r0: float, v0: float, phi0: float) -> np.ndarray:
    """Prédit la trajectoire depuis des CI données — O(_N_IN) simulation + O(1) ML.

    Retourne un tableau (N_IN + N_OUT, 2) contenant le contexte simulé puis
    la prédiction ML.
    """
    phi_rad = np.radians(phi0)
    vx0 = v0 * np.cos(phi_rad)
    vy0 = v0 * np.sin(phi_rad)

    ctx_raw = _run_cone(r0, v0, phi0, n_frames=_N_IN + 1)
    while len(ctx_raw) < _N_IN:
        ctx_raw.append(ctx_raw[-1])

    ctx_x = np.array([pt[0] for pt in ctx_raw[:_N_IN]])
    ctx_y = np.array([pt[1] for pt in ctx_raw[:_N_IN]])

    feat = _make_feat(ctx_x, ctx_y, vx0, vy0).reshape(1, -1)
    pred = np.column_stack([model_x.predict(feat)[0], model_y.predict(feat)[0]])
    ctx = np.column_stack([ctx_x, ctx_y])
    return np.vstack([ctx, pred]).astype(np.float32)


def train_and_evaluate(pool_data: dict) -> dict:
    """Entraîne RL et MLP sur les trajectoires du pool et retourne les modèles.

    Args:
        pool_data: dict avec clé "trajectories" (N, MIN_TRAJ_LEN, 2) numpy array.

    Returns:
        {
            "lr_x": LinearRegression, "lr_y": LinearRegression,
            "mlp_x": Pipeline, "mlp_y": Pipeline,
            "metrics_lr": {n_train, r2_x, r2_y, rmse_x, rmse_y},
            "metrics_mlp": {...},
            "train_trajs": [{"x_full": array|None, "y_full": array|None}, ...],
        }
    Sauvegarde automatiquement les modèles dans _MODELS_PKL.
    """
    trajs = pool_data["trajectories"]   # (N, MIN_TRAJ_LEN, 2)
    dt = 0.01                           # ConeParams.dt par défaut

    X_list:   list[np.ndarray] = []
    y_x_list: list[np.ndarray] = []
    y_y_list: list[np.ndarray] = []
    train_trajs: list[dict]    = []

    for i, traj in enumerate(trajs):
        traj_arr = np.asarray(traj)
        if traj_arr.shape[0] < _N_IN + _N_OUT:
            continue
        ctx = traj_arr[:_N_IN]
        target = traj_arr[_N_IN:_N_IN + _N_OUT]
        vx0 = (traj_arr[1, 0] - traj_arr[0, 0]) / dt
        vy0 = (traj_arr[1, 1] - traj_arr[0, 1]) / dt
        X_list.append(_make_feat(ctx[:, 0], ctx[:, 1], vx0, vy0))
        y_x_list.append(target[:, 0])
        y_y_list.append(target[:, 1])
        if i < _MAX_DISPLAY_TRAJS:
            train_trajs.append({"x_full": traj_arr[:, 0], "y_full": traj_arr[:, 1]})
        else:
            train_trajs.append({"x_full": None, "y_full": None})

    if not X_list:
        raise RuntimeError("train_and_evaluate : aucune trajectoire utilisable")

    X   = np.array(X_list)
    y_x = np.array(y_x_list)
    y_y = np.array(y_y_list)
    n_train = len(X_list)

    # Régression linéaire
    lr_x = LinearRegression().fit(X, y_x)
    lr_y = LinearRegression().fit(X, y_y)

    # MLP (64→32, sortie _N_OUT)
    mlp_x = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42),
    ).fit(X, y_x)
    mlp_y = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42),
    ).fit(X, y_y)

    def _metrics(model_x, model_y, tag: str) -> dict:
        px = model_x.predict(X)
        py = model_y.predict(X)
        return {
            "n_train": n_train,
            "r2_x":   float(r2_score(y_x, px, multioutput="uniform_average")),
            "r2_y":   float(r2_score(y_y, py, multioutput="uniform_average")),
            "rmse_x": float(np.sqrt(mean_squared_error(y_x, px, multioutput="uniform_average"))),
            "rmse_y": float(np.sqrt(mean_squared_error(y_y, py, multioutput="uniform_average"))),
        }

    result = {
        "lr_x":       lr_x,
        "lr_y":       lr_y,
        "mlp_x":      mlp_x,
        "mlp_y":      mlp_y,
        "metrics_lr":  _metrics(lr_x,  lr_y,  "lr"),
        "metrics_mlp": _metrics(mlp_x, mlp_y, "mlp"),
        "train_trajs": train_trajs,
    }
    save_trained_models(result, _MODELS_PKL)
    return result


def save_trained_models(models_dict: dict, path: str = _MODELS_PKL) -> None:
    """Sauvegarde les modèles sklearn entraînés dans un fichier pickle.

    Args:
        models_dict: Structure {config_key: {"rl_x": model, "rl_y": model, 
                                             "mlp_x": model, "mlp_y": model}}
                     Exemple: {"linear": {...}, "mlp": {...}}
        path: Chemin du fichier pickle

    Les modèles sont des objets sklearn (LinearRegression ou Pipeline).
    Taille typique : ~50-100 MB pour tous les modèles.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(models_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
    log.info("Modèles sauvegardés : %d configs → %s", len(models_dict), path)


def load_trained_models(path: str = _MODELS_PKL) -> dict | None:
    """Charge les modèles sklearn depuis un fichier pickle.

    Returns:
        dict: Structure {config_key: {"rl_x": model, "rl_y": model, ...}}
              ou None si le fichier est absent ou corrompu.

    Les modèles retournés sont prêts à utiliser avec .predict().
    """
    if not os.path.exists(path):
        log.warning("Modèles introuvables : %s", path)
        return None
    try:
        with open(path, "rb") as f:
            models = pickle.load(f)
        log.info("Modèles chargés : %d configs depuis %s", len(models), path)
        return models
    except Exception as e:
        log.error("Erreur chargement modèles : %s", e)
        return None


def models_are_ready(path: str = _MODELS_PKL) -> bool:
    """Retourne True si le fichier de modèles existe et contient les modèles attendus."""
    if not os.path.exists(path):
        return False
    try:
        models = load_trained_models(path)
        if not models:
            return False
        # Vérifier que chaque config contient les 4 modèles
        for model_type in ["linear", "mlp"]:
            if model_type not in models:
                return False
            config_models = models[model_type]
            expected = ["rl_x", "rl_y", "mlp_x", "mlp_y"]
            if not all(k in config_models for k in expected):
                return False
        return True
    except Exception:
        return False


def get_cached_models() -> dict | None:
    """Retourne les modèles chargés en mémoire (si disponibles)."""
    return _CACHED_MODELS


def set_cached_models(models: dict) -> None:
    """Stocke les modèles en mémoire pour accès instantané."""
    global _CACHED_MODELS
    _CACHED_MODELS = models