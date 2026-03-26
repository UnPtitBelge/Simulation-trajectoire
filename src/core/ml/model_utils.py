"""Model training and preset management utilities."""

import logging
import pickle

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data_utils import _N_IN, _N_OUT, _PRESETS_NPZ, _MODELS_PKL, load_pool

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


def train_and_evaluate(trajectories: list[dict]) -> dict:
    """Entraîne les modèles RL et MLP sur les trajectoires fournies.

    Utilise les 5 premiers points comme contexte (features) et prédit les
    _N_OUT positions suivantes. Les trajectoires 16 et 17 sont utilisées comme
    holdout pour évaluer les métriques.

    Args:
        trajectories : liste de trajectoires (chaque trajectoire a x, y, speedX, speedY)

    Returns:
        dict avec clés :
        - lr_x, lr_y, mlp_x, mlp_y : modèles entraînés
        - metrics_lr, metrics_mlp : métriques R² et RMSE
        - train_trajs : trajectoires d'entraînement (pour visualisation)
    """
    # Préparer les données d'entraînement
    X_train, yx_train, yy_train = [], [], []
    train_trajs = []

    for traj in trajectories:
        if traj["expID"] in (16, 17):  # Holdout — ne pas inclure dans l'entraînement
            continue

        x_full = np.array(traj["x"])
        y_full = np.array(traj["y"])

        # Features : 5 points de contexte + vitesses initiales
        ctx_x = x_full[:_N_IN]
        ctx_y = y_full[:_N_IN]
        vx0 = traj["speedX"][0]
        vy0 = traj["speedY"][0]

        X_train.append(_make_feat(ctx_x, ctx_y, vx0, vy0))
        yx_train.append(x_full[_N_IN:_N_IN + _N_OUT])
        yy_train.append(y_full[_N_IN:_N_IN + _N_OUT])

        # Pour visualisation : stocker x_full/y_full uniquement si < _MAX_DISPLAY_TRAJS
        if len(train_trajs) < 100:  # _MAX_DISPLAY_TRAJS
            train_trajs.append({
                "x_full": x_full,
                "y_full": y_full,
                "expID": traj["expID"],
            })

    X_train = np.array(X_train)
    yx_train = np.array(yx_train)
    yy_train = np.array(yy_train)

    # Entraîner les modèles
    lr_x = LinearRegression().fit(X_train, yx_train)
    lr_y = LinearRegression().fit(X_train, yy_train)
    mlp_x = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32)))
    mlp_y = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32)))
    mlp_x.fit(X_train, yx_train)
    mlp_y.fit(X_train, yy_train)

    # Évaluer sur les holdout (expID 16 et 17)
    def evaluate_model(model_x, model_y, ref_id: int):
        ref_traj = next(t for t in trajectories if t["expID"] == ref_id)
        x_ref = np.array(ref_traj["x"])
        y_ref = np.array(ref_traj["y"])
        vx0 = ref_traj["speedX"][0]
        vy0 = ref_traj["speedY"][0]

        ctx_x = x_ref[:_N_IN]
        ctx_y = y_ref[:_N_IN]
        feat = _make_feat(ctx_x, ctx_y, vx0, vy0).reshape(1, -1)

        x_pred = model_x.predict(feat)[0]
        y_pred = model_y.predict(feat)[0]

        r2_x = r2_score(x_ref[_N_IN:_N_IN + _N_OUT], x_pred)
        r2_y = r2_score(y_ref[_N_IN:_N_IN + _N_OUT], y_pred)
        rmse_x = np.sqrt(mean_squared_error(x_ref[_N_IN:_N_IN + _N_OUT], x_pred))
        rmse_y = np.sqrt(mean_squared_error(y_ref[_N_IN:_N_IN + _N_OUT], y_pred))

        return {"r2_x": r2_x, "r2_y": r2_y, "rmse_x": rmse_x, "rmse_y": rmse_y}

    metrics_lr = evaluate_model(lr_x, lr_y, 16)
    metrics_mlp = evaluate_model(mlp_x, mlp_y, 17)

    return {
        "lr_x": lr_x,
        "lr_y": lr_y,
        "mlp_x": mlp_x,
        "mlp_y": mlp_y,
        "metrics_lr": metrics_lr,
        "metrics_mlp": metrics_mlp,
        "train_trajs": train_trajs,
    }


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
    from .sim_to_real import _CACHED_MODELS
    return _CACHED_MODELS


def set_cached_models(models: dict) -> None:
    """Stocke les modèles en mémoire pour accès instantané."""
    from .sim_to_real import _CACHED_MODELS
    global _CACHED_MODELS
    _CACHED_MODELS = models