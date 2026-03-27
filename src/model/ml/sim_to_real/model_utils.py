"""Model training and preset management utilities."""

import logging
import os
import pickle

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data_utils import (
    _N_IN,
    _N_OUT,
    _MODELS_PKL,
    _MAX_DISPLAY_TRAJS,
    _run_cone,
    _make_feat,
)

_CACHED_MODELS: dict | None = None

log = logging.getLogger(__name__)

# ── Fonctions de prédiction et entraînement ──────────────────────────────────


def _compute_metrics_chunked(
    model_x,
    model_y,
    X: np.ndarray,
    y_x: np.ndarray,
    y_y: np.ndarray,
    n_train: int,
    chunk_size: int = 50000,
) -> dict:
    """Calcule les métriques par chunks pour éviter la surcharge mémoire.

    Args:
        model_x, model_y: Modèles sklearn entraînés
        X: Features d'entrée (n_samples, n_features)
        y_x, y_y: Targets (n_samples, n_outputs)
        n_train: Nombre total d'échantillons
        chunk_size: Taille des chunks pour les prédictions

    Returns:
        dict avec r2_x, r2_y, rmse_x, rmse_y
    """
    n_samples = len(X)

    # Accumulateurs pour le calcul incrémental
    ss_res_x = 0.0  # sum of squared residuals
    ss_res_y = 0.0
    ss_tot_x = 0.0  # total sum of squares
    ss_tot_y = 0.0

    # Calculer la moyenne globale d'abord (nécessaire pour R²)
    y_x_mean = np.mean(y_x, axis=0)
    y_y_mean = np.mean(y_y, axis=0)

    for start_idx in range(0, n_samples, chunk_size):
        end_idx = min(start_idx + chunk_size, n_samples)
        X_chunk = X[start_idx:end_idx]
        y_x_chunk = y_x[start_idx:end_idx]
        y_y_chunk = y_y[start_idx:end_idx]

        # Prédictions pour ce chunk
        px_chunk = model_x.predict(X_chunk)
        py_chunk = model_y.predict(X_chunk)

        # Accumuler les résidus
        ss_res_x += np.sum((y_x_chunk - px_chunk) ** 2)
        ss_res_y += np.sum((y_y_chunk - py_chunk) ** 2)
        ss_tot_x += np.sum((y_x_chunk - y_x_mean) ** 2)
        ss_tot_y += np.sum((y_y_chunk - y_y_mean) ** 2)

    # Calculer R² et RMSE
    r2_x = 1.0 - (ss_res_x / ss_tot_x) if ss_tot_x > 0 else 0.0
    r2_y = 1.0 - (ss_res_y / ss_tot_y) if ss_tot_y > 0 else 0.0
    rmse_x = np.sqrt(ss_res_x / n_samples)
    rmse_y = np.sqrt(ss_res_y / n_samples)

    return {
        "n_train": n_train,
        "r2_x": float(r2_x),
        "r2_y": float(r2_y),
        "rmse_x": float(rmse_x),
        "rmse_y": float(rmse_y),
    }


def _predict_trajectory(
    model_x, model_y, r0: float, v0: float, phi0: float
) -> np.ndarray:
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


def train_and_evaluate(pool_data: dict, chunk_size: int = 50000) -> dict:
    """Entraîne RL et MLP sur les trajectoires du pool et retourne les modèles.

    Args:
        pool_data: dict avec clé "trajectories" (N, MIN_TRAJ_LEN, 2) numpy array.
        chunk_size: nombre de trajectoires à traiter par chunk (défaut: 50000).

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
    trajs = pool_data["trajectories"]  # (N, MIN_TRAJ_LEN, 2)
    dt = 0.01  # ConeParams.dt par défaut
    n_total = len(trajs)

    log.info(
        f"Entraînement par chunks : {n_total} trajectoires, {chunk_size} par chunk"
    )

    # Pré-allouer les tableaux pour éviter l'accumulation de chunks
    n_features = 2 * _N_IN + 2  # (x₀,...,x₄, y₀,...,y₄, vx₀, vy₀)
    X = np.empty((n_total, n_features), dtype=np.float32)
    y_x = np.empty((n_total, _N_OUT), dtype=np.float32)
    y_y = np.empty((n_total, _N_OUT), dtype=np.float32)

    train_trajs: list[dict] = []
    n_processed = 0

    # Traiter les trajectoires par chunks pour économiser la RAM
    for chunk_start in range(0, n_total, chunk_size):
        chunk_end = min(chunk_start + chunk_size, n_total)
        chunk_trajs = trajs[chunk_start:chunk_end]

        log.info(
            f"  → Chunk {chunk_start//chunk_size + 1}/"
            f"{(n_total + chunk_size - 1)//chunk_size} "
            f"({chunk_start}–{chunk_end})"
        )

        chunk_idx = 0
        for i, traj in enumerate(chunk_trajs):
            global_idx = chunk_start + i
            traj_arr = np.asarray(traj, dtype=np.float32)
            if (
                traj_arr.ndim != 2
                or traj_arr.shape[1] != 2
                or traj_arr.shape[0] < 2
            ):
                # trajectoire malformée (< 2 points : vitesse initiale
                # incalculable)
                continue

            # Padder avec le dernier point si trop courte — la bille reste
            # à sa position finale
            n = traj_arr.shape[0]
            if n < _N_IN + _N_OUT:
                pad = np.tile(traj_arr[-1:], (_N_IN + _N_OUT - n, 1))
                traj_arr = np.vstack([traj_arr, pad])

            ctx = traj_arr[:_N_IN]
            target = traj_arr[_N_IN : _N_IN + _N_OUT]
            vx0 = (traj_arr[1, 0] - traj_arr[0, 0]) / dt
            vy0 = (traj_arr[1, 1] - traj_arr[0, 1]) / dt

            # Écrire directement dans le tableau pré-alloué
            write_idx = chunk_start + chunk_idx
            X[write_idx] = _make_feat(ctx[:, 0], ctx[:, 1], vx0, vy0)
            y_x[write_idx] = target[:, 0]
            y_y[write_idx] = target[:, 1]
            chunk_idx += 1

            if global_idx < _MAX_DISPLAY_TRAJS:
                train_trajs.append({"x_full": traj_arr[:, 0], "y_full": traj_arr[:, 1]})

        n_processed += chunk_idx

    # Compléter train_trajs avec des None si nécessaire
    while len(train_trajs) < n_total and len(train_trajs) < _MAX_DISPLAY_TRAJS:
        train_trajs.append({"x_full": None, "y_full": None})

    if n_processed == 0:
        raise RuntimeError(
            "train_and_evaluate : aucune trajectoire utilisable (toutes < 2 points)"
        )

    # Tronquer aux trajectoires valides
    X = X[:n_processed]
    y_x = y_x[:n_processed]
    y_y = y_y[:n_processed]
    n_train = n_processed

    log.info("  → Entraînement LinearRegression...")
    # Régression linéaire
    lr_x = LinearRegression().fit(X, y_x)
    lr_y = LinearRegression().fit(X, y_y)

    log.info("  → Calcul des métriques LR (par chunks)...")
    metrics_lr = _compute_metrics_chunked(
        lr_x, lr_y, X, y_x, y_y, n_train, chunk_size=50000
    )

    log.info("  → Entraînement MLP...")
    # MLP (64→32, sortie _N_OUT)
    mlp_x = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42),
    ).fit(X, y_x)
    mlp_y = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42),
    ).fit(X, y_y)

    log.info("  → Calcul des métriques MLP (par chunks)...")
    metrics_mlp = _compute_metrics_chunked(
        mlp_x, mlp_y, X, y_x, y_y, n_train, chunk_size=50000
    )

    # Libérer la mémoire des données d'entraînement
    del X, y_x, y_y

    log.info("  ✓ Entraînement terminé")
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
    """Retourne True si le pkl contient les 3 variantes de contexte (_PRESET_N_SIMS).

    Structure attendue : {n_sims: {"lr_x", "lr_y", "mlp_x", "mlp_y", ...}, ...}
    """
    if not os.path.exists(path):
        return False
    try:
        from .data_utils import _PRESET_N_SIMS

        models = load_trained_models(path)
        if not models:
            return False
        _REQUIRED = ["lr_x", "lr_y", "mlp_x", "mlp_y"]
        return all(
            n in models and all(k in models[n] for k in _REQUIRED)
            for n in _PRESET_N_SIMS
        )
    except Exception:
        return False


def get_cached_models() -> dict | None:
    """Retourne les modèles chargés en mémoire (si disponibles)."""
    return _CACHED_MODELS


def set_cached_models(models: dict) -> None:
    """Stocke les modèles en mémoire pour accès instantané."""
    global _CACHED_MODELS
    _CACHED_MODELS = models
