"""Data generation utilities for sim-to-real pipeline."""

import csv
import logging
import os
import random

import numpy as np

from src.model.params.cone_params import ConeParams
from src.model.simulation.cone import simulate_cone

log = logging.getLogger(__name__)

# ── Constantes ML ─────────────────────────────────────────────────────────────

__all__ = [
    "_N_IN", "_N_OUT", "_MIN_TRAJ_LEN", "_POOL_SIZE", "_MAX_DISPLAY_TRAJS",
    "_PRESET_LABELS", "_PRESET_N_SIMS", "_CONTEXT_LABELS",
    "_SYNTHETIC_CSV", "_SYNTHETIC_NPZ", "_PRESETS_NPZ", "_MODELS_PKL",
    "pool_is_ready", "load_pool", "generate_and_save_pool",
    "_run_cone", "_make_feat",
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
_POOL_SIZE = 100_000

# Labels des modèles ML disponibles
_PRESET_LABELS: list[str] = ["RL", "MLP"]

# Tailles de contexte pour Ctrl+1/2/3
_PRESET_N_SIMS: list[int] = [50, 45_000, 90_000]
_CONTEXT_LABELS: list[str] = [
    "50 trajectoires",
    "45 000 trajectoires",
    "90 000 trajectoires",
]

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

# ── Fonctions de base ─────────────────────────────────────────────────────────

def _make_feat(ctx_x: np.ndarray, ctx_y: np.ndarray, vx0: float, vy0: float) -> np.ndarray:
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


# ── Pool de données ────────────────────────────────────────────────────────────

def pool_is_ready(path: str = _SYNTHETIC_NPZ, min_n: int = _POOL_SIZE) -> bool:
    """Retourne True si le pool .npz existe et contient suffisamment de trajectoires.

    Accepte 90% de min_n comme seuil (filtrage des trajectoires trop courtes).
    """
    if not os.path.exists(path):
        return False
    try:
        with np.load(path) as data:
            return len(data["trajectories"]) >= int(min_n * 0.9)
    except Exception:
        return False


def load_pool(path: str = _SYNTHETIC_NPZ, n_sims: int | None = None) -> dict | None:
    """Charge le pool synthétique et retourne un sous-ensemble de n_sims trajectoires.

    Returns:
        {"trajectories": np.ndarray (N, MIN_TRAJ_LEN, 2), "ref_trajs": dict[str, np.ndarray]}
        ou None si le fichier est absent ou illisible.
    """
    if not os.path.exists(path):
        log.warning("Pool introuvable : %s", path)
        return None
    try:
        d = np.load(path, allow_pickle=False)
        trajs: np.ndarray = d["trajectories"]
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


def generate_and_save_pool(
    path: str = _SYNTHETIC_NPZ,
    csv_path: str | None = None,
    progress_cb=None,
) -> None:
    """Génère _POOL_SIZE trajectoires via LHS et les sauvegarde dans path.

    Les CI (r0, v0, phi0) sont échantillonnées par Latin Hypercube Sampling.
    Les trajectoires de longueur insuffisante (<_MIN_TRAJ_LEN) sont filtrées.
    """
    from src.model.params.sim_to_real import SimToRealParams

    R0_MIN, R0_MAX     = 0.08, 0.35
    V0_MIN, V0_MAX     = 0.10, 2.50
    PHI0_MIN, PHI0_MAX = 0.0,  360.0

    n = _POOL_SIZE
    r0_vals   = _lhs_samples(n, R0_MIN, R0_MAX)
    v0_vals   = _lhs_samples(n, V0_MIN, V0_MAX)
    phi0_vals = _lhs_samples(n, PHI0_MIN, PHI0_MAX)

    trajectories: list[np.ndarray] = []
    csv_rows: list[tuple] = []

    for i, (r0, v0, phi0) in enumerate(zip(r0_vals, v0_vals, phi0_vals)):
        if progress_cb and i % 500 == 0:
            progress_cb(i, n)
        traj = _run_cone(r0, v0, phi0, n_frames=_MIN_TRAJ_LEN + 5)
        if len(traj) >= _MIN_TRAJ_LEN:
            trajectories.append(np.array(traj[:_MIN_TRAJ_LEN], dtype=np.float32))
            if csv_path:
                csv_rows.append((r0, v0, phi0, len(traj)))

    if not trajectories:
        raise RuntimeError("generate_and_save_pool : aucune trajectoire valide générée")

    trajs_array = np.stack(trajectories)
    log.info("Pool généré : %d / %d trajectoires valides", len(trajectories), n)

    presets = SimToRealParams.PRESETS
    arrays: dict[str, np.ndarray] = {"trajectories": trajs_array}
    for key, preset in presets.items():
        ref = _run_cone(float(preset["r0"]), float(preset["v0"]), float(preset["phi0"]))
        arrays[f"ref_{key}"] = np.array(ref, dtype=np.float32)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez_compressed(path, **arrays)  # type: ignore[arg-type]
    log.info("Pool sauvegardé : %s", path)

    if csv_path and csv_rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["r0", "v0", "phi0", "traj_len"])
            writer.writerows(csv_rows)

    if progress_cb:
        progress_cb(n, n)
