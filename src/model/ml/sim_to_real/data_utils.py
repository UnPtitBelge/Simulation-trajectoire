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
    "generate_and_save_pool", "pool_is_ready", "load_pool",
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
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_data.csv")
)
_SYNTHETIC_NPZ = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_data.npz")
)
_PRESETS_NPZ = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "sim_to_real_presets.npz")
)
_MODELS_PKL = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "trained_models.pkl")
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


def _latin_hypercube_ci(n: int, rng: random.Random) -> list[tuple[float, float, float]]:
    """Génère n triplets (r0, v0, phi0) via Latin Hypercube Sampling.

    Le LHS garantit une couverture uniforme de l'espace des paramètres.
    Chaque dimension est divisée en n intervalles, un point est tiré dans
    chaque intervalle, puis les dimensions sont mélangées aléatoirement.

    Args:
        n  : nombre de triplets à générer
        rng: générateur aléatoire pour reproductibilité

    Returns:
        Liste de (r0, v0, phi0) avec r0 ∈ [0.08, 0.35], v0 ∈ [0.3, 2.5], phi0 ∈ [0°, 360°]
    """
    # Diviser chaque dimension en n intervalles
    r0_bins = np.linspace(0.08, 0.35, n + 1)
    v0_bins = np.linspace(0.3, 2.5, n + 1)
    phi0_bins = np.linspace(0, 360, n + 1)

    # Tirer un point dans chaque intervalle
    r0_vals = [rng.uniform(r0_bins[i], r0_bins[i + 1]) for i in range(n)]
    v0_vals = [rng.uniform(v0_bins[i], v0_bins[i + 1]) for i in range(n)]
    phi0_vals = [rng.uniform(phi0_bins[i], phi0_bins[i + 1]) for i in range(n)]

    # Mélanger chaque dimension indépendamment
    rng.shuffle(r0_vals)
    rng.shuffle(v0_vals)
    rng.shuffle(phi0_vals)

    return list(zip(r0_vals, v0_vals, phi0_vals))


def generate_cone_dataset(
    n_sims: int,
    seed: int = 42,
    progress_cb=None,
) -> tuple[list[dict], list[dict]]:
    """Génère un dataset de n_sims trajectoires cône avec CI aléatoires.

    Chaque trajectoire est simulée jusqu'à arrêt naturel (early stopping).
    Les trajectoires trop courtes (< _MIN_TRAJ_LEN) sont filtrées.

    Args:
        n_sims     : nombre de simulations à lancer
        seed       : graine aléatoire pour reproductibilité
        progress_cb: callback de progression (current, total)

    Returns:
        (trajectories, ref_trajs) où:
        - trajectories : liste de dicts {expID, temps, x, y, speedX, speedY}
        - ref_trajs    : 2 trajectoires holdout (expID 16 et 17) pour évaluation
    """
    rng = random.Random(seed)
    cis = _latin_hypercube_ci(n_sims * 3, rng)  # 3× plus pour filtrage

    trajectories = []
    attempts = 0

    for exp_id, (r0, v0, phi0) in enumerate(cis, start=1):
        if attempts >= n_sims * 8:
            break
        attempts += 1

        traj = _run_cone(r0, v0, phi0)
        if len(traj) < _MIN_TRAJ_LEN:
            continue

        # Calculer les vitesses par différences finies
        x_arr = np.array([pt[0] for pt in traj])
        y_arr = np.array([pt[1] for pt in traj])
        dt = 0.01  # ConeParams.dt par défaut
        speed_x = np.gradient(x_arr, dt)
        speed_y = np.gradient(y_arr, dt)

        trajectories.append({
            "expID": exp_id,
            "temps": [i * dt for i in range(len(traj))],
            "x": x_arr.tolist(),
            "y": y_arr.tolist(),
            "speedX": speed_x.tolist(),
            "speedY": speed_y.tolist(),
            "r0": r0,
            "v0": v0,
            "phi0": phi0,
        })

        if progress_cb and exp_id % 100 == 0:
            progress_cb(len(trajectories), n_sims)

    # Holdout fixe : expID 16 et 17 (jamais dans le dataset d'entraînement)
    ref_trajs = []
    for ref_id, (r0, v0, phi0) in enumerate([(0.2, 1.0, 45), (0.15, 1.5, 135)], start=16):
        traj = _run_cone(r0, v0, phi0, n_frames=_MIN_TRAJ_LEN)
        x_arr = np.array([pt[0] for pt in traj])
        y_arr = np.array([pt[1] for pt in traj])
        dt = 0.01
        speed_x = np.gradient(x_arr, dt)
        speed_y = np.gradient(y_arr, dt)
        ref_trajs.append({
            "expID": ref_id,
            "temps": [i * dt for i in range(len(traj))],
            "x": x_arr.tolist(),
            "y": y_arr.tolist(),
            "speedX": speed_x.tolist(),
            "speedY": speed_y.tolist(),
        })

    return trajectories, ref_trajs


def generate_and_save_pool(
    path: str = _SYNTHETIC_NPZ,
    csv_path: str = _SYNTHETIC_CSV,
    progress_cb=None,
) -> None:
    """Génère le pool synthétique et sauvegarde dans .npz et .csv.

    Args:
        path       : chemin du fichier .npz de sortie
        csv_path   : chemin du fichier .csv de sortie (pour compatibilité)
        progress_cb: callback de progression (current, total)
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    trajectories, ref_trajs = generate_cone_dataset(_POOL_SIZE, progress_cb=progress_cb)

    # Sauvegarder en .npz (format optimisé pour numpy)
    np.savez_compressed(
        path,
        trajectories=np.array(trajectories, dtype=object),  # type: ignore[arg-type]
        ref_trajs=np.array(ref_trajs, dtype=object),        # type: ignore[arg-type]
    )
    log.info("Pool sauvegardé : %d trajectoires → %s", len(trajectories), path)

    # Sauvegarder en .csv (pour compatibilité historique)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["expID", "temps", "x", "y", "speedX", "speedY", "r0", "v0", "phi0"])
        for traj in trajectories:
            for i, t in enumerate(traj["temps"]):
                writer.writerow([
                    traj["expID"],
                    t,
                    traj["x"][i],
                    traj["y"][i],
                    traj["speedX"][i],
                    traj["speedY"][i],
                    traj["r0"],
                    traj["v0"],
                    traj["phi0"],
                ])
    log.info("CSV sauvegardé : %s", csv_path)


def load_pool(path: str = _SYNTHETIC_NPZ, n_sims: int | None = None) -> dict | None:
    """Charge le pool synthétique depuis un fichier .npz.

    Args:
        path    : chemin du fichier .npz
        n_sims  : si spécifié, échantillonne n_sims trajectoires aléatoires

    Returns:
        dict avec clés 'trajectories' et 'ref_trajs', ou None si erreur
    """
    if not os.path.exists(path):
        log.warning("Pool introuvable : %s", path)
        return None

    try:
        data = np.load(path, allow_pickle=True)
        trajectories = data["trajectories"].tolist()
        ref_trajs = data["ref_trajs"].tolist()

        if n_sims is not None and n_sims < len(trajectories):
            rng = random.Random(42)
            pool_idxs = list(range(len(trajectories)))
            rng.shuffle(pool_idxs)
            pool_idxs = pool_idxs[:min(n_sims, len(pool_idxs))]
            trajectories = [trajectories[i] for i in pool_idxs]

        return {"trajectories": trajectories, "ref_trajs": ref_trajs}
    except Exception as e:
        log.error("Erreur chargement pool : %s", e)
        return None


def pool_is_ready(path: str = _SYNTHETIC_NPZ, min_n: int = _POOL_SIZE) -> bool:
    """Retourne True si le pool .npz existe et contient au moins min_n trajectoires.

    Accepte 90% de min_n comme seuil (filtrage des trajectoires trop courtes
    peut réduire légèrement le nombre final).
    """
    if not os.path.exists(path):
        return False
    try:
        with np.load(path) as data:
            n_trajs = len(data["trajectories"])
            threshold = int(min_n * 0.9)
            return n_trajs >= threshold
    except Exception:
        return False