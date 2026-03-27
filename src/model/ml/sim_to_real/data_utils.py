"""Data generation utilities for sim-to-real pipeline."""

import logging
import math
import os
import random

import numpy as np

from src.model.params.cone_params import ConeParams
from src.model.simulation.cone import simulate_cone

log = logging.getLogger(__name__)

# ── Constantes ML ─────────────────────────────────────────────────────────────

__all__ = [
    "_N_IN",
    "_N_OUT",
    "_MIN_TRAJ_LEN",
    "_POOL_SIZE",
    "_MAX_DISPLAY_TRAJS",
    "_PRESET_LABELS",
    "_PRESET_N_SIMS",
    "_CONTEXT_LABELS",
    "_SYNTHETIC_CSV",
    "_SYNTHETIC_NPZ",
    "_PRESETS_NPZ",
    "_MODELS_PKL",
    "pool_is_ready",
    "load_pool",
    "_run_cone",
    "_run_cone_xy",
    "_make_feat",
]

# Nombre de points de contexte utilisés comme features d'entrée de la régression.
# Features = [x₀,y₀, x₁,y₁, …, x_{N_IN-1},y_{N_IN-1}, vx₀, vy₀]
# Soit 2·_N_IN + 2 = 12 features (avec _N_IN=5).
_N_IN = 5

# Nombre de positions prédites par le modèle après les _N_IN points de contexte.
_N_OUT = 600

# Longueur minimale requise : _N_IN points de contexte + _N_OUT positions cibles.
_MIN_TRAJ_LEN = _N_IN + _N_OUT

# Nombre maximum de courbes d'entraînement affichées (perf. graphique).
_MAX_DISPLAY_TRAJS = 100

# Taille cible du pool pré-généré (stocké dans synthetic_data.npz).
_POOL_SIZE = 1_000_000

# Labels des modèles ML disponibles
_PRESET_LABELS: list[str] = ["RL", "MLP"]

# Tailles de contexte pour Ctrl+1/2/3/4
_PRESET_N_SIMS: list[int] = [50, 45_000, 90_000, 1_000_000]
_CONTEXT_LABELS: list[str] = [
    "50 trajectoires",
    "45 000 trajectoires",
    "90 000 trajectoires",
    "1 000 000 trajectoires",
]

# Chemins des fichiers de données
_SYNTHETIC_CSV = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_data.csv"
    )
)
_SYNTHETIC_NPZ = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_data.npz"
    )
)
_PRESETS_NPZ = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "sim_to_real_presets.npz"
    )
)
_MODELS_PKL = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "data", "trained_models.pkl"
    )
)

# ── Fonctions de base ─────────────────────────────────────────────────────────


def _make_feat(
    ctx_x: np.ndarray, ctx_y: np.ndarray, vx0: float, vy0: float
) -> np.ndarray:
    """Construit le vecteur de features 1-D pour la régression.

    Format : [x₀, y₀, x₁, y₁, …, x_{N_IN-1}, y_{N_IN-1}, vx₀, vy₀]
    Taille  : 2·_N_IN + 2
    """
    return np.append(np.column_stack([ctx_x, ctx_y]).ravel(), [vx0, vy0])


def _run_cone(r0: float, v0: float, phi0: float, n_frames: int | None = None) -> list:
    """Lance une simulation cône et retourne la trajectoire (x,y) sous forme de liste."""
    params = ConeParams(r0=r0, v0=v0, phi0=phi0)
    if n_frames is not None:
        params = ConeParams(r0=r0, v0=v0, phi0=phi0, n_frames=n_frames)
    result = simulate_cone(params)
    return [(pt[0], pt[1]) for pt in result["trajectory"]]


def _run_cone_xy(
    x0: float, y0: float, v0: float, phi0_abs: float, n_frames: int | None = None
) -> list:
    """Lance une simulation cône depuis la position cartésienne (x0, y0).

    phi0_abs est l'angle de la vitesse initiale en degrés dans le repère absolu.
    Exploite la symétrie rotationnelle du cône : démarrer en (r0·cos α, r0·sin α)
    avec vitesse d'angle phi0_abs est équivalent à démarrer en (r0, 0) avec vitesse
    d'angle (phi0_abs - α), puis tourner toute la trajectoire de α.
    """
    r0 = math.sqrt(x0 * x0 + y0 * y0)
    alpha = math.atan2(y0, x0)  # angle de position en radians
    phi0_rel = math.degrees(alpha)  # angle relatif pour la simulation
    traj = _run_cone(r0, v0, phi0_abs - phi0_rel, n_frames)

    # Rotation de la trajectoire par alpha pour replacer dans le repère absolu
    cos_a, sin_a = math.cos(alpha), math.sin(alpha)
    return [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in traj]


# ── Pool de données ────────────────────────────────────────────────────────────


def pool_is_ready(path: str = _SYNTHETIC_NPZ, min_n: int = _POOL_SIZE) -> bool:
    """Retourne True si le pool .npz existe et contient suffisamment de trajectoires.

    Accepte 90% de min_n comme seuil (filtrage des trajectoires trop courtes).
    Supporte les formats legacy (object array de dicts) et normalisé (float array 3D).
    """
    if not os.path.exists(path):
        return False
    try:
        with np.load(path, allow_pickle=True) as data:
            trajs = _normalize_trajectories(data["trajectories"])
            return len(trajs) >= int(min_n * 0.9)
    except Exception:
        return False


def _normalize_trajectories(trajs: np.ndarray) -> np.ndarray:
    """Normalise les trajectoires en tableau d'objets numpy (N,), chaque élément (n_i, 2).

    Accepte trois formats d'entrée :
    - Format float 3D  : (N, M, 2) → converti en object array pour uniformité.
    - Format object    : object array de numpy arrays (n_i, 2) → retourné tel quel.
    - Format legacy    : object array de dicts {"x": [...], "y": [...]} → converti.
    """
    if trajs.dtype != object:
        # Format float 3D (N, M, 2) — convertir en object array de tableaux 2D
        result = np.empty(len(trajs), dtype=object)
        for i, t in enumerate(trajs):
            result[i] = np.asarray(t, dtype=np.float32)
        return result

    if len(trajs) == 0:
        return trajs

    first = trajs[0]
    if isinstance(first, dict):
        # Format legacy : object array de dicts {"x": [...], "y": [...]}
        result = np.empty(len(trajs), dtype=object)
        for i, traj in enumerate(trajs):
            try:
                x = np.asarray(traj["x"], dtype=np.float32)
                y = np.asarray(traj["y"], dtype=np.float32)
                n = min(len(x), len(y))
                result[i] = np.column_stack([x[:n], y[:n]])
            except (KeyError, TypeError):
                result[i] = np.empty((0, 2), dtype=np.float32)
        return result

    # Format object array de numpy arrays — retourner tel quel
    return trajs


def load_pool(path: str = _SYNTHETIC_NPZ, n_sims: int | None = None) -> dict | None:
    """Charge le pool synthétique et retourne un sous-ensemble de n_sims trajectoires.

    Returns:
        {"trajectories": np.ndarray (N, MIN_TRAJ_LEN, 2), "ref_trajs": dict[str, np.ndarray]}
        ou None si le fichier est absent ou illisible.
    Accepte les formats legacy (object array de dicts) et normalisé (float array 3D).
    """
    if not os.path.exists(path):
        log.warning("Pool introuvable : %s", path)
        return None
    try:
        d = np.load(path, allow_pickle=True)
        trajs = _normalize_trajectories(d["trajectories"])
        log.info("load_pool : %d trajectoires disponibles", len(trajs))
        if n_sims is not None and n_sims < len(trajs):
            idx = np.random.choice(len(trajs), n_sims, replace=False)
            trajs = trajs[idx]
        ref_trajs: dict[str, np.ndarray] = {}
        for key in ["pres_standard", "pres_rapide", "pres_bord"]:
            k = f"ref_{key}"
            if k in d:
                ref_trajs[key] = d[k]
        return {"trajectories": trajs, "ref_trajs": ref_trajs}
    except Exception as exc:
        log.error("load_pool : erreur lecture %s : %s", path, exc)
        return None


def _lhs_samples(n: int, lo: float, hi: float) -> list[float]:
    """Génère n échantillons Latin Hypercube dans [lo, hi]."""
    intervals = [(i + random.random()) / n for i in range(n)]
    random.shuffle(intervals)
    return [lo + (hi - lo) * x for x in intervals]
