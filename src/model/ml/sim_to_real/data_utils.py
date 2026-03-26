"""Data generation utilities for sim-to-real pipeline."""

import csv
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
    "_N_IN", "_N_OUT", "_MIN_TRAJ_LEN", "_POOL_SIZE",
    "_PRESET_LABELS", "_PRESET_N_SIMS", "_CONTEXT_LABELS",
    "_SYNTHETIC_CSV", "_SYNTHETIC_NPZ", "_PRESETS_NPZ", "_MODELS_PKL",
    "pool_is_ready", "load_pool",
    "_run_cone", "_make_feat",
]

# Nombre de points de contexte utilisés comme features d'entrée de la régression.
# Features = [x₀,y₀, x₁,y₁, …, x_{N_IN-1},y_{N_IN-1}, vx₀, vy₀]
# Soit 2·_N_IN + 2 = 12 features (avec _N_IN=5).
_N_IN = 5

# Nombre de positions prédites par le modèle après les _N_IN points de contexte.
_N_OUT = 600

# Longueur minimale requise : _N_IN points de contexte + _N_OUT positions cibles.
# dt = 0.01 s → 605 frames = 6.05 s ≥ 5 s minimum (bille peut sortir du bord).
_MIN_TRAJ_LEN = _N_IN + _N_OUT

# Nombre maximum de courbes d'entraînement affichées (perf. graphique).
_MAX_DISPLAY_TRAJS = 100

# Taille cible du pool pré-généré (stocké dans synthetic_data.npz).
# Note : le filtrage des trajectoires trop courtes réduit le nombre final à ~93k.
_POOL_SIZE = 100_000

# Labels des modèles ML disponibles
_PRESET_LABELS: list[str] = ["RL", "MLP"]

# Tailles de contexte pour Ctrl+1/2/3
_PRESET_N_SIMS: list[int] = [50, 45_000, 90_000]
_CONTEXT_LABELS: list[str] = ["50 trajectoires", "45 000 trajectoires", "90 000 trajectoires"]

# Chemins des fichiers de données
_SYNTHETIC_CSV = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_data.csv")
)
_SYNTHETIC_NPZ = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_data.npz")
)
_PRESETS_NPZ = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "sim_to_real_presets.npz")
)
_MODELS_PKL = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "trained_models.pkl")
)

# ── Fonctions de génération ──────────────────────────────────────────────────

def _make_feat(ctx_x: np.ndarray, ctx_y: np.ndarray, vx0: float, vy0: float) -> np.ndarray:
    """Construit le vecteur de features 1-D pour la régression.

    Format : [x₀, y₀, x₁, y₁, …, x_{N_IN-1}, y_{N_IN-1}, vx₀, vy₀]
    Taille  : 2·_N_IN + 2
    """
    return np.append(np.column_stack([ctx_x, ctx_y]).ravel(), [vx0, vy0])


def _run_cone(r0: float, v0: float, phi0: float, n_frames: int | None = None) -> list:
    """Lance une simulation cône et retourne la trajectoire (x,y) sous forme de liste.

    Args:
        r0, v0, phi0 : conditions initiales
        n_frames    : nombre de frames à simuler (None = jusqu'à arrêt naturel)

    Returns:
        Liste de tuples (x, y) de longueur n_frames (ou jusqu'à arrêt).
    """
    params = ConeParams(r0=r0, v0=v0, phi0=phi0)
    if n_frames is not None:
        params = ConeParams(r0=r0, v0=v0, phi0=phi0, n_frames=n_frames)
    result = simulate_cone(params)
    return [(pt[0], pt[1]) for pt in result["trajectory"]]


