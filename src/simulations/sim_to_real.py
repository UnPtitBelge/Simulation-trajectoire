"""Sim-to-Real — génération de données synthétiques depuis la simulation cône.

Pipeline :
  1. Lancer N simulations cône avec des CI aléatoires (r0, v0, phi0)
     → seules r0, v0, phi0 sont modifiées ; tous les autres paramètres (pente,
       frottement, dt, n_frames, R_cone…) utilisent les défauts de ConeParams.
  2. Chaque simulation tourne jusqu'à l'arrêt naturel de la bille (via early
     stopping de simulate_cone) — aucune troncature artificielle.
  3. Enregistrer (expID, temps, x, y, speedX, speedY) dans un CSV.
  4. Entraîner la régression linéaire ML sur ces données synthétiques.
     Features : [x₀,y₀, x₁,y₁, …, x_{N_IN-1},y_{N_IN-1}, vx₀, vy₀]
              = 2·_N_IN + 2 = 12 valeurs (5 points de contexte + CI vitesse).
  5. Évaluer les métriques sur 2 trajectoires holdout (jamais vues).
  6. Pré-calculer 3 trajectoires de référence (une par preset) hors dataset.

Plages CI utilisées dans le dataset synthétique :
  r0   ∈ [0.08, 0.35] m  (R_cone = 0.40 m par défaut)
  v0   ∈ [0.30, 2.50] m/s
  phi0 ∈ [0°, 360°]
"""

import csv
import logging
import math
import os
import pickle
import random

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.core.params.integrators import MLModel
from src.core.params.cone import ConeParams
from src.core.params.sim_to_real import SimToRealParams
from src.simulations.base import Plot
from src.simulations.cone import simulate_cone
from src.utils.theme import (
    CLR_ML_BG,
    CLR_PRIMARY,
    CLR_SUCCESS,
    CLR_TEXT_SECONDARY,
    FS_LG,
    FS_MD,
    FS_SM,
    FS_XS,
)

log = logging.getLogger(__name__)

# ── Cache global des modèles ──────────────────────────────────────────────────

_CACHED_MODELS: dict | None = None  # Modèles chargés en mémoire au démarrage

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

# ── Constantes ML ─────────────────────────────────────────────────────────────

# Nombre de points de contexte utilisés comme features d'entrée de la régression.
# Features = [x₀,y₀, x₁,y₁, …, x_{N_IN-1},y_{N_IN-1}, vx₀, vy₀]
# Soit 2·_N_IN + 2 = 12 features (avec _N_IN=5).
_N_IN  = 5

# Nombre de positions prédites par le modèle après les _N_IN points de contexte.
_N_OUT = 600

# Nombre maximum de courbes d'entraînement affichées (perf. graphique).
_MAX_DISPLAY_TRAJS = 100

# Longueur minimale requise : _N_IN points de contexte + _N_OUT positions cibles.
# dt = 0.01 s → 605 frames = 6.05 s ≥ 5 s minimum (bille peut sortir du bord).
_MIN_TRAJ_LEN = _N_IN + _N_OUT

# Taille cible du pool pré-généré (stocké dans synthetic_data.npz).
# Note : le filtrage des trajectoires trop courtes réduit le nombre final à ~93k.
_POOL_SIZE = 100_000

# Valeurs de n_sims pour les 3 presets de comparaison (min / moitié / max).
# Basées sur les ~93k trajectoires réellement disponibles après filtrage.
_PRESET_N_SIMS: list[int] = [50, 45_000, 90_000]
_PRESET_LABELS: list[str] = ["50", "45k", "90k"]


def _make_feat(ctx_x: np.ndarray, ctx_y: np.ndarray, vx0: float, vy0: float) -> np.ndarray:
    """Construit le vecteur de features 1-D pour la régression.

    Format : [x₀, y₀, x₁, y₁, …, x_{N_IN-1}, y_{N_IN-1}, vx₀, vy₀]
    Taille  : 2·_N_IN + 2
    """
    return np.append(np.column_stack([ctx_x, ctx_y]).ravel(), [vx0, vy0])


def _run_cone(r0: float, v0: float, phi0: float, n_frames: int | None = None) -> list:
    """Lance une simulation cône avec les défauts de ConeParams, CI seules modifiées.

    n_frames est un paramètre de calcul (durée max), pas un paramètre physique.
    Si None, utilise le défaut de ConeParams (3000 frames = 30 s).
    """
    kw: dict = {"n_frames": n_frames} if n_frames is not None else {}
    p = ConeParams(r0=r0, v0=v0, phi0=phi0, **kw)
    return simulate_cone(p)["trajectory"]


def _latin_hypercube_ci(n: int, rng: random.Random) -> list[tuple[float, float, float]]:
    """Latin Hypercube Sampling sur (r0, v0, phi0).

    Garantit une couverture uniforme de l'espace des CI : chaque dimension est
    divisée en n intervalles égaux et exactement un échantillon est placé dans
    chaque intervalle, puis les dimensions sont appairées aléatoirement.

    Plages : r0 ∈ [0.08, 0.35] m, v0 ∈ [0.30, 2.50] m/s, phi0 ∈ [0°, 360°]
    """
    def _dim(lo: float, hi: float) -> list[float]:
        step = (hi - lo) / n
        vals = [lo + (i + rng.random()) * step for i in range(n)]
        rng.shuffle(vals)
        return vals

    r0s  = _dim(0.08, 0.35)
    v0s  = _dim(0.30, 2.50)
    phis = _dim(0.0,  360.0)
    return list(zip(r0s, v0s, phis))


def generate_cone_dataset(
    n_sims: int,
    csv_path: str = _SYNTHETIC_CSV,
    seed: int = 42,
    progress_cb=None,
) -> dict | None:
    """Lance n_sims simulations cône avec des CI aléatoires et écrit le CSV.

    Seules r0, v0, phi0 sont modifiées ; slope, friction, dt, n_frames utilisent
    les valeurs par défaut de ConeParams (pas de constantes locales hardcodées).
    Chaque simulation tourne jusqu'à l'arrêt naturel (early stopping de simulate_cone).

    Retourne un dict :
      "trajectories" : list[dict]          — données d'entraînement (>= _MIN_TRAJ_LEN pts)
      "ref_trajs"    : dict[str, ndarray]  — trajectoires de référence (presets)
    ou None si aucune trajectoire n'a pu être générée.

    Chaque trajectoire d'entraînement contient :
      x, y       : _MIN_TRAJ_LEN premiers points — contexte + cibles pour le ML
      x_full, y_full : trajectoire complète          — pour l'affichage
      vx, vy     : vitesse initiale analytique       — feature ML

    progress_cb(current, total) est appelé après chaque trajectoire acceptée.
    """
    rng = random.Random(seed)
    trajectories = []

    # Latin Hypercube Sampling : couverture uniforme de l'espace des CI.
    # On génère plus de candidats que nécessaire (×3) pour absorber les rejets
    # (trajectoires trop courtes). Le surplus est tiré aléatoirement.
    n_lhs = n_sims * 3
    lhs_candidates = _latin_hypercube_ci(n_lhs, rng)
    lhs_iter = iter(lhs_candidates)

    def _next_ci() -> tuple[float, float, float]:
        """Renvoie le prochain candidat LHS, ou un tirage aléatoire si épuisé."""
        try:
            return next(lhs_iter)
        except StopIteration:
            return (
                rng.uniform(0.08, 0.35),
                rng.uniform(0.30, 2.50),
                rng.uniform(0.0, 360.0),
            )

    attempts = 0
    while len(trajectories) < n_sims and attempts < n_sims * 8:
        attempts += 1
        r0, v0, phi0 = _next_ci()

        traj_xyz = _run_cone(r0, v0, phi0)

        # On exige au moins _N_IN points de contexte + _N_OUT points cibles
        if len(traj_xyz) < _MIN_TRAJ_LEN:
            continue

        phi_rad = math.radians(phi0)
        xy      = np.array([[pt[0], pt[1]] for pt in traj_xyz])

        keep_full = len(trajectories) < _MAX_DISPLAY_TRAJS
        trajectories.append({
            "exp_id": len(trajectories) + 1,
            # Portion ML : _N_IN contexte + _N_OUT cibles
            "x":      xy[:_MIN_TRAJ_LEN, 0],
            "y":      xy[:_MIN_TRAJ_LEN, 1],
            # Trajectoire complète pour l'affichage — seulement pour les _MAX_DISPLAY_TRAJS premières
            # (évite la consommation mémoire explosive pour n_sims > 5 000)
            "x_full": xy[:, 0] if keep_full else None,
            "y_full": xy[:, 1] if keep_full else None,
            # Vitesse initiale analytique (feature ML)
            "vx": v0 * math.cos(phi_rad),
            "vy": v0 * math.sin(phi_rad),
        })

        if progress_cb:
            progress_cb(len(trajectories), n_sims)

    if not trajectories:
        log.warning("Aucune trajectoire générée après %d tentatives", attempts)
        return None

    # ── Écriture CSV ──────────────────────────────────────────────────────────
    try:
        os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["expID", "temps", "x", "y", "speedX", "speedY"])
            for traj in trajectories:
                vx0, vy0 = traj["vx"], traj["vy"]
                xs, ys   = traj["x"], traj["y"]
                for j in range(len(xs)):
                    writer.writerow([
                        traj["exp_id"], j,
                        f"{xs[j]:.6f}", f"{ys[j]:.6f}",
                        f"{vx0:.6f}", f"{vy0:.6f}",
                    ])
    except Exception as e:
        log.error("Écriture CSV échouée : %s", e)

    # ── Trajectoires de référence (presets, hors dataset) ────────────────────
    # Accepte toute longueur ≥ 2 — pas de filtre par _MIN_TRAJ_LEN ici.
    ref_trajs: dict[str, np.ndarray] = {}
    for key, preset in SimToRealParams.PRESENTATION_PRESETS.items():
        traj_ref = _run_cone(preset["r0"], preset["v0"], preset["phi0"])
        if len(traj_ref) >= 2:
            ref_trajs[key] = np.array([[pt[0], pt[1]] for pt in traj_ref])

    log.info(
        "Dataset : %d trajectoires, %d références → %s",
        len(trajectories), len(ref_trajs), csv_path,
    )
    return {"trajectories": trajectories, "ref_trajs": ref_trajs}


# ── Pool pré-généré (synthetic_data.npz) ──────────────────────────────────────

def generate_and_save_pool(
    n: int = _POOL_SIZE,
    path: str = _SYNTHETIC_NPZ,
    seed: int = 42,
    progress_cb=None,
) -> None:
    """Génère n trajectoires cônes et les sauvegarde dans un fichier numpy compressé.

    Filtre automatiquement les trajectoires trop courtes (< _MIN_TRAJ_LEN frames,
    soit 6.05 s avec dt=0.01 — garantit ≥ 5 s même si la bille sort du bord).

    Le fichier .npz contient :
      x_traj : (N, _MIN_TRAJ_LEN) float32 — coordonnées x
      y_traj : (N, _MIN_TRAJ_LEN) float32 — coordonnées y
      vx0    : (N,)               float32 — vitesse initiale x
      vy0    : (N,)               float32 — vitesse initiale y

    Format beaucoup plus compact que le CSV :
      100 000 trajectoires × 605 pts ≈ 485 MB non compressé → ~50 MB compressé.
    """
    rng = random.Random(seed)
    x_list:  list[np.ndarray] = []
    y_list:  list[np.ndarray] = []
    vx0_list: list[float] = []
    vy0_list: list[float] = []

    n_lhs = n * 3
    lhs_candidates = _latin_hypercube_ci(n_lhs, rng)
    lhs_iter = iter(lhs_candidates)

    def _next_ci() -> tuple[float, float, float]:
        try:
            return next(lhs_iter)
        except StopIteration:
            return (
                rng.uniform(0.08, 0.35),
                rng.uniform(0.30, 2.50),
                rng.uniform(0.0, 360.0),
            )

    attempts = 0
    while len(x_list) < n and attempts < n * 8:
        attempts += 1
        r0, v0, phi0 = _next_ci()
        traj_xyz = _run_cone(r0, v0, phi0)

        if len(traj_xyz) < _MIN_TRAJ_LEN:
            continue

        phi_rad = math.radians(phi0)
        xy = np.array([[pt[0], pt[1]] for pt in traj_xyz], dtype=np.float32)
        x_list.append(xy[:_MIN_TRAJ_LEN, 0])
        y_list.append(xy[:_MIN_TRAJ_LEN, 1])
        vx0_list.append(float(v0 * math.cos(phi_rad)))
        vy0_list.append(float(v0 * math.sin(phi_rad)))

        if progress_cb:
            progress_cb(len(x_list), n)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez_compressed(
        path,
        x_traj = np.stack(x_list),
        y_traj = np.stack(y_list),
        vx0    = np.array(vx0_list, dtype=np.float32),
        vy0    = np.array(vy0_list, dtype=np.float32),
    )
    log.info("Pool sauvegardé : %d trajectoires → %s", len(x_list), path)


def load_pool(
    path: str = _SYNTHETIC_NPZ,
    n_sims: int | None = None,
    seed: int = 0,
) -> dict | None:
    """Charge le pool pré-généré et retourne un dict compatible avec train_and_evaluate.

    n_sims : nombre de trajectoires d'entraînement à échantillonner depuis le pool.
             Les indices 0 et 1 sont toujours réservés comme holdout (résultats
             comparables quelle que soit la valeur de n_sims).
             Si None, utilise tout le pool (hors holdout).

    Retourne {"trajectories": list[dict], "ref_trajs": dict}
    ou None si le fichier est absent.
    """
    if not os.path.exists(path):
        log.warning("Pool introuvable : %s", path)
        return None

    with np.load(path) as data:
        x_traj = data["x_traj"]   # (N, 605)
        y_traj = data["y_traj"]
        vx0    = data["vx0"]       # (N,)
        vy0    = data["vy0"]
        N = len(x_traj)

        # Indices 0-1 : holdout fixe (cohérence des métriques entre n_sims différents)
        holdout_idxs = [0, 1]
        pool_idxs = list(range(2, N))

        if n_sims is not None:
            rng = random.Random(seed + n_sims)  # reproductible par valeur de n_sims
            rng.shuffle(pool_idxs)
            pool_idxs = pool_idxs[:min(n_sims, len(pool_idxs))]

        selected = pool_idxs + holdout_idxs   # holdout toujours en fin de liste

        trajectories = []
        for rank, idx in enumerate(selected):
            trajectories.append({
                "exp_id": rank + 1,
                "x":      x_traj[idx].copy(),
                "y":      y_traj[idx].copy(),
                "x_full": x_traj[idx].copy() if rank < _MAX_DISPLAY_TRAJS else None,
                "y_full": y_traj[idx].copy() if rank < _MAX_DISPLAY_TRAJS else None,
                "vx":     float(vx0[idx]),
                "vy":     float(vy0[idx]),
            })

    # Trajectoires de référence (presets, calculées à la volée — 3 simulations)
    ref_trajs: dict[str, np.ndarray] = {}
    for key, preset in SimToRealParams.PRESENTATION_PRESETS.items():
        traj_ref = _run_cone(preset["r0"], preset["v0"], preset["phi0"])
        if len(traj_ref) >= 2:
            ref_trajs[key] = np.array([[pt[0], pt[1]] for pt in traj_ref])

    return {"trajectories": trajectories, "ref_trajs": ref_trajs}


def pool_is_ready(path: str = _SYNTHETIC_NPZ, min_n: int = _POOL_SIZE) -> bool:
    """Retourne True si le pool .npz existe et contient au moins min_n trajectoires.
    
    Accepte 90% de min_n comme seuil (filtrage des trajectoires trop courtes
    peut réduire légèrement le nombre final).
    """
    if not os.path.exists(path):
        return False
    try:
        with np.load(path) as data:
            n_trajs = len(data["x_traj"])
            threshold = int(min_n * 0.9)
            return n_trajs >= threshold
    except Exception:
        return False


# ── Presets de comparaison pré-calculés ───────────────────────────────────────

def _predict_trajectory(model_x, model_y, r0: float, v0: float, phi0: float) -> np.ndarray:
    """Prédit la trajectoire depuis des CI données — O(_N_IN) simulation + O(1) ML.

    Retourne un tableau (N_IN + N_OUT, 2) contenant le contexte simulé puis
    la prédiction ML.
    """
    phi_rad = math.radians(phi0)
    vx0 = v0 * math.cos(phi_rad)
    vy0 = v0 * math.sin(phi_rad)

    ctx_raw = _run_cone(r0, v0, phi0, n_frames=_N_IN + 1)
    while len(ctx_raw) < _N_IN:
        ctx_raw.append(ctx_raw[-1])

    ctx_x = np.array([pt[0] for pt in ctx_raw[:_N_IN]])
    ctx_y = np.array([pt[1] for pt in ctx_raw[:_N_IN]])

    feat  = _make_feat(ctx_x, ctx_y, vx0, vy0).reshape(1, -1)
    pred  = np.column_stack([model_x.predict(feat)[0], model_y.predict(feat)[0]])
    ctx   = np.column_stack([ctx_x, ctx_y])
    return np.vstack([ctx, pred]).astype(np.float32)


def compute_and_save_presets(
    path: str = _PRESETS_NPZ,
    models_path: str = _MODELS_PKL,
    ci_key: str = "nominale",
    progress_cb=None,
) -> None:
    """Pré-calcule 6 trajectoires prédites : 3 n_sims × 2 modèles (RL + MLP).
    
    IMPORTANT : Sauvegarde aussi les 12 modèles entraînés (4 modèles × 3 configs)
    dans models_path pour chargement instantané au démarrage de l'app.

    Les conditions initiales utilisées sont le preset `ci_key` (par défaut
    "nominale" = CI de présentation).  Les résultats sont stockés dans deux fichiers :
    
    1. path (presets.npz) : trajectoires prédites + métriques (~30 KB)
       pred_rl_50, pred_rl_45000, pred_rl_90000     : (N_IN+N_OUT, 2)
       pred_mlp_50, pred_mlp_45000, pred_mlp_90000  : (N_IN+N_OUT, 2)
       meta_rl_50, …                                : [r2_x, r2_y, rmse_x, rmse_y, n_train]
    
    2. models_path (trained_models.pkl) : modèles sklearn entraînés (~50-100 MB)
       {"50": {"rl_x": model, "rl_y": model, "mlp_x": model, "mlp_y": model},
        "45000": {...}, "90000": {...}}
    """
    from src.core.params.sim_to_real import SimToRealParams as _P
    ci = _P.PRESENTATION_PRESETS.get(ci_key, _P.PRESENTATION_PRESETS["nominale"])
    r0, v0, phi0 = ci["r0"], ci["v0"], ci["phi0"]

    arrays: dict[str, np.ndarray] = {}
    models_dict: dict[str, dict] = {}  # Structure : {config_key: {model_name: model}}
    total_steps = len(_PRESET_N_SIMS)

    for step_i, n in enumerate(_PRESET_N_SIMS):
        label = _PRESET_LABELS[step_i]
        config_key = str(n)
        
        if progress_cb:
            progress_cb(step_i, total_steps, f"Entraînement {n:,} trajectoires…")

        data = load_pool(n_sims=n)
        if data is None:
            log.error("compute_and_save_presets : pool manquant pour n=%d", n)
            continue
        result = train_and_evaluate(data["trajectories"])

        # Sauvegarder les modèles pour cette config
        models_dict[config_key] = {
            "rl_x": result["lr_x"],
            "rl_y": result["lr_y"],
            "mlp_x": result["mlp_x"],
            "mlp_y": result["mlp_y"],
        }

        # RL
        pred_rl = _predict_trajectory(result["lr_x"], result["lr_y"], r0, v0, phi0)
        m_rl    = result["metrics_lr"]
        arrays[f"pred_rl_{n}"] = pred_rl
        arrays[f"meta_rl_{n}"] = np.array(
            [m_rl["r2_x"], m_rl["r2_y"], m_rl["rmse_x"], m_rl["rmse_y"], n],
            dtype=np.float32,
        )

        # MLP
        pred_mlp = _predict_trajectory(result["mlp_x"], result["mlp_y"], r0, v0, phi0)
        m_mlp    = result["metrics_mlp"]
        arrays[f"pred_mlp_{n}"] = pred_mlp
        arrays[f"meta_mlp_{n}"] = np.array(
            [m_mlp["r2_x"], m_mlp["r2_y"], m_mlp["rmse_x"], m_mlp["rmse_y"], n],
            dtype=np.float32,
        )

    if progress_cb:
        progress_cb(total_steps, total_steps, "Sauvegarde…")

    # Sauvegarder les trajectoires prédites (npz)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    np.savez_compressed(path, **arrays)
    log.info("Presets sauvegardés : %s", path)
    
    # Sauvegarder les modèles entraînés (pickle)
    save_trained_models(models_dict, models_path)



def load_presets(path: str = _PRESETS_NPZ) -> dict | None:
    """Charge les presets pré-calculés.

    Retourne un dict :
      {
        "rl_50":  {"pred_np": (605,2), "metrics": {...}, "model_type": MLModel.LINEAR, "n_sims": 50,  "label": "RL — 50"},
        "rl_33000": …,
        …
        "mlp_100000": …,
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
    for i, n in enumerate(_PRESET_N_SIMS):
        lbl = _PRESET_LABELS[i]
        for model_tag, model_type in [("rl", MLModel.LINEAR), ("mlp", MLModel.MLP)]:
            pred_key = f"pred_{model_tag}_{n}"
            meta_key = f"meta_{model_tag}_{n}"
            if pred_key not in data or meta_key not in data:
                continue
            meta = data[meta_key]
            key  = f"{model_tag}_{n}"
            presets[key] = {
                "pred_np":    data[pred_key],                   # (605, 2)
                "metrics":    {
                    "r2_x":   float(meta[0]),
                    "r2_y":   float(meta[1]),
                    "rmse_x": float(meta[2]),
                    "rmse_y": float(meta[3]),
                    "n_train": int(meta[4]),
                },
                "model_type": model_type,
                "n_sims":     n,
                "label":      f"{'RL' if model_tag == 'rl' else 'MLP'} — {lbl}",
            }
    return presets if presets else None


def presets_are_ready(path: str = _PRESETS_NPZ) -> bool:
    """Retourne True si le fichier de presets existe et contient les 6 entrées."""
    if not os.path.exists(path):
        return False
    try:
        data = np.load(path)
        expected = [f"pred_{m}_{n}" for m in ("rl", "mlp") for n in _PRESET_N_SIMS]
        return all(k in data for k in expected)
    except Exception:
        return False


# ── Sauvegarde et chargement des modèles sklearn ──────────────────────────────

def save_trained_models(models_dict: dict, path: str = _MODELS_PKL) -> None:
    """Sauvegarde les modèles sklearn entraînés dans un fichier pickle.
    
    Args:
        models_dict: Structure {config_key: {"rl_x": model, "rl_y": model, 
                                             "mlp_x": model, "mlp_y": model}}
                     Exemple: {"50": {...}, "45000": {...}, "90000": {...}}
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
    """Retourne True si le fichier de modèles existe et contient les 12 modèles.
    
    Vérifie la présence des 4 modèles (rl_x, rl_y, mlp_x, mlp_y) pour chaque
    configuration de _PRESET_N_SIMS.
    """
    if not os.path.exists(path):
        return False
    try:
        models = load_trained_models(path)
        if not models:
            return False
        # Vérifier que chaque config contient les 4 modèles
        for n in _PRESET_N_SIMS:
            config_key = str(n)
            if config_key not in models:
                return False
            config_models = models[config_key]
            expected = ["rl_x", "rl_y", "mlp_x", "mlp_y"]
            if not all(k in config_models for k in expected):
                return False
        return True
    except Exception:
        return False


def get_cached_models() -> dict | None:
    """Retourne les modèles chargés en mémoire (cache global).
    
    Si les modèles ne sont pas encore chargés, tente de les charger depuis le fichier.
    Cette fonction est appelée par l'UI pour accéder aux modèles instantanément.
    
    Returns:
        dict: Structure {config_key: {"rl_x": model, "rl_y": model, "mlp_x": model, "mlp_y": model}}
              Exemple: {"50": {...}, "45000": {...}, "90000": {...}}
              ou None si les modèles ne sont pas disponibles.
    """
    global _CACHED_MODELS
    if _CACHED_MODELS is None:
        _CACHED_MODELS = load_trained_models()
        if _CACHED_MODELS:
            log.info("Modèles chargés en cache : %d configs", len(_CACHED_MODELS))
    return _CACHED_MODELS


def set_cached_models(models: dict) -> None:
    """Définit explicitement les modèles en cache (utilisé au démarrage de l'app)."""
    global _CACHED_MODELS
    _CACHED_MODELS = models
    log.info("Modèles mis en cache : %d configs", len(models) if models else 0)


def predict_with_model(
    config_key: str,
    model_type: str,
    r0: float,
    v0: float,
    phi0: float,
    models_dict: dict | None = None,
) -> np.ndarray | None:
    """Prédit une trajectoire avec un modèle pré-entraîné.
    
    Args:
        config_key: "50", "45000" ou "90000" (nombre de trajectoires d'entraînement)
        model_type: "rl" (Linear Regression) ou "mlp" (MLP)
        r0, v0, phi0: Conditions initiales
        models_dict: Dict des modèles (si None, utilise le cache global)
    
    Returns:
        array (N_IN+N_OUT, 2) : contexte simulé + prédiction ML
        ou None si le modèle n'est pas disponible
    """
    if models_dict is None:
        models_dict = get_cached_models()
    
    if not models_dict or config_key not in models_dict:
        log.error("Modèle introuvable : config=%s", config_key)
        return None
    
    config_models = models_dict[config_key]
    model_x_key = f"{model_type}_x"
    model_y_key = f"{model_type}_y"
    
    if model_x_key not in config_models or model_y_key not in config_models:
        log.error("Modèle introuvable : config=%s, type=%s", config_key, model_type)
        return None
    
    return _predict_trajectory(
        config_models[model_x_key],
        config_models[model_y_key],
        r0, v0, phi0
    )


def train_and_evaluate(trajectories: list[dict]) -> dict:
    """Entraîne la régression linéaire et évalue sur les 2 dernières trajectoires.

    Features d'entrée : _make_feat → 2·_N_IN + 2 valeurs
      [x₀,y₀, x₁,y₁, …, x_{N_IN-1},y_{N_IN-1}, vx₀, vy₀]
    Sorties : _N_OUT positions après le contexte (x et y indépendants).

    Les 2 dernières trajectoires servent de holdout (jamais vues à l'entraînement).
    """
    if len(trajectories) < 3:
        raise ValueError("Il faut au moins 3 trajectoires (1 train + 2 holdout).")

    n_train = len(trajectories) - 2
    train_trajs = trajectories[:n_train]
    holdout     = trajectories[-2]

    # ── Matrices d'entraînement ───────────────────────────────────────────────
    X  = np.array([
        _make_feat(t["x"][:_N_IN], t["y"][:_N_IN], t["vx"], t["vy"])
        for t in train_trajs
    ])
    Yx = np.array([t["x"][_N_IN:_N_IN + _N_OUT] for t in train_trajs])
    Yy = np.array([t["y"][_N_IN:_N_IN + _N_OUT] for t in train_trajs])

    # ── Régression linéaire ───────────────────────────────────────────────────
    lr_x = LinearRegression().fit(X, Yx)
    lr_y = LinearRegression().fit(X, Yy)

    # ── MLP (adam + early_stopping : scalable de quelques dizaines à 100 000 samples) ──
    mlp_x = make_pipeline(
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(64, 32), solver="adam",
            max_iter=300, early_stopping=True, n_iter_no_change=15, random_state=42,
        ),
    ).fit(X, Yx)
    mlp_y = make_pipeline(
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(64, 32), solver="adam",
            max_iter=300, early_stopping=True, n_iter_no_change=15, random_state=42,
        ),
    ).fit(X, Yy)

    # ── Métriques sur le holdout ──────────────────────────────────────────────
    feat_h  = _make_feat(
        holdout["x"][:_N_IN], holdout["y"][:_N_IN],
        holdout["vx"], holdout["vy"],
    ).reshape(1, -1)
    truth_x = holdout["x"][_N_IN:_N_IN + _N_OUT]
    truth_y = holdout["y"][_N_IN:_N_IN + _N_OUT]

    def _metrics(mx, my, n):
        px = mx.predict(feat_h)[0]
        py = my.predict(feat_h)[0]
        return {
            "r2_x":   float(r2_score(truth_x, px)),
            "r2_y":   float(r2_score(truth_y, py)),
            "rmse_x": float(np.sqrt(mean_squared_error(truth_x, px))),
            "rmse_y": float(np.sqrt(mean_squared_error(truth_y, py))),
            "n_train": n,
        }

    metrics_lr  = _metrics(lr_x,  lr_y,  n_train)
    metrics_mlp = _metrics(mlp_x, mlp_y, n_train)

    ctx   = np.column_stack([holdout["x"][:_N_IN], holdout["y"][:_N_IN]])
    pred  = np.column_stack([lr_x.predict(feat_h)[0], lr_y.predict(feat_h)[0]])
    truth = np.column_stack([truth_x, truth_y])

    return {
        "metrics_lr":      metrics_lr,
        "metrics_mlp":     metrics_mlp,
        "pred_positions":  np.vstack([ctx, pred]),    # (_N_IN + _N_OUT, 2)
        "truth_positions": np.vstack([ctx, truth]),   # (_N_IN + _N_OUT, 2)
        "train_trajs":     train_trajs,
        "lr_x":            lr_x,
        "lr_y":            lr_y,
        "mlp_x":           mlp_x,
        "mlp_y":           mlp_y,
    }


# ── Pens ──────────────────────────────────────────────────────────────────────

_PEN_TRAIN = pg.mkPen((150, 150, 150, 50), width=1)
_PEN_TRUTH = pg.mkPen(CLR_SUCCESS, width=2)
_PEN_PRED  = pg.mkPen(CLR_PRIMARY, width=2)


# ── PlotSimToReal ─────────────────────────────────────────────────────────────

class PlotSimToReal(Plot):
    """Simulation Sim-to-Real : génère un dataset cône synthétique et entraîne le ML.

    Utilisation en mode présentation :
      - _compute()       : génère les trajectoires + entraîne le modèle (QThread)
      - _draw_initial()  : bascule sur la vue résultats, affiche les trajectoires
      - _draw(i)         : anime la trajectoire prédite frame par frame

    La vérité terrain (courbe verte) n'est affichée que si les CI courantes
    correspondent exactement à l'un des 3 presets de présentation.
    Les 3 trajectoires de référence sont pré-calculées hors dataset d'entraînement.

    Seules les CI (r0, v0, phi0) sont passées à ConeParams ; tous les autres
    paramètres physiques utilisent les valeurs par défaut de ConeParams.

    Un signal `progress(current, total)` est émis depuis le thread de calcul
    pour mettre à jour la barre de progression visible pendant le chargement.
    """

    SIM_KEY = "sim_to_real"

    # Émis depuis le thread de calcul — connexion automatiquement queued (thread-safe)
    progress: Signal = Signal(int, int)

    def __init__(self, params: SimToRealParams | None = None):
        _p = params or SimToRealParams()
        super().__init__(_p)
        self.params: SimToRealParams = _p

        self._result:       dict       = {}
        self._pred_np:      np.ndarray = np.empty((0, 2))
        self._train_curves: list       = []
        self.metrics:       dict       = {}
        self._lr_x                     = None
        self._lr_y                     = None
        self._mlp_x                    = None
        self._mlp_y                    = None
        self._ref_trajs:    dict       = {}     # preset_key → (N, 2)
        self._last_n_sims:  int        = -1
        self._precomputed:  dict       = {}     # key → {pred_np, metrics, model_type, …}
        self._preset_btns:  dict[str, QPushButton] = {}

        # Registres des sliders CI — peuplés par _build_ci_bar()
        self._ci_sliders:    dict[str, QSlider] = {}
        self._ci_val_labels: dict[str, QLabel]  = {}

        self.widget = self._build_widget()

        # Boucle automatique : quand l'animation se termine, on repart du début
        self.anim_finished.connect(self._reset_animation)

    # ── Construction du widget ────────────────────────────────────────────────

    def _build_widget(self) -> QWidget:
        root = QWidget()
        root.setStyleSheet(f"background:{CLR_ML_BG};")
        root.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_loading_page())   # index 0
        self._stack.addWidget(self._build_results_page())   # index 1
        self._stack.setCurrentIndex(0)

        layout.addWidget(self._stack)
        return root

    def _build_loading_page(self) -> QWidget:
        """Écran de chargement — visible pendant _compute()."""
        page = QWidget()
        page.setStyleSheet(f"background:{CLR_ML_BG};")

        outer = QVBoxLayout(page)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner = QWidget()
        inner.setFixedWidth(480)
        lay = QVBoxLayout(inner)
        lay.setSpacing(18)
        lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Sim-to-Real — Entraînement en cours")
        title.setStyleSheet(
            f"color:white; font-size:{FS_LG}; font-weight:500; background:transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        self._loading_subtitle = QLabel(
            f"Chargement de {self.params.n_sims} trajectoires depuis le pool…"
        )
        self._loading_subtitle.setStyleSheet(
            f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_MD}; background:transparent;"
        )
        self._loading_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._loading_subtitle)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(10)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ background:#374151; border-radius:5px; border:none; }}"
            f"QProgressBar::chunk {{ background:{CLR_PRIMARY}; border-radius:5px; }}"
        )
        lay.addWidget(self._progress_bar)

        self._loading_status = QLabel("Démarrage…")
        self._loading_status.setStyleSheet(
            f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS}; background:transparent;"
        )
        self._loading_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._loading_status)

        outer.addWidget(inner)

        self.progress.connect(self._on_progress)
        return page

    def _build_results_page(self) -> QWidget:
        """Vue résultats — visible après entraînement."""
        page = QWidget()
        page.setStyleSheet(f"background:{CLR_ML_BG};")

        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Plot pyqtgraph ────────────────────────────────────────────────────
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground(CLR_ML_BG)
        self._plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._plot_widget.showGrid(x=False, y=False)
        self._plot_widget.hideAxis("bottom")
        self._plot_widget.hideAxis("left")
        self._plot_widget.setAspectLocked(True)
        self._plot_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        legend = self._plot_widget.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(31, 41, 55, 200))

        # Vérité terrain — seulement visible quand CI = un preset
        self._truth_curve = self._plot_widget.plot(
            [], [], pen=_PEN_TRUTH, name="Réel (référence preset)"
        )
        self._pred_curve = self._plot_widget.plot(
            [], [], pen=_PEN_PRED, name="Prédit (ML)"
        )
        self._cursor = self._plot_widget.plot(
            [], [],
            pen=None, symbol="o", symbolSize=8,
            symbolBrush=pg.mkBrush("w"), symbolPen=pg.mkPen("w", width=1),
        )

        lay.addWidget(self._plot_widget, stretch=1)

        # ── Barre de métriques ────────────────────────────────────────────────
        self._metrics_bar = QWidget()
        self._metrics_bar.setStyleSheet(
            "background:#111827; border-top:1px solid #374151;"
        )
        bar = QHBoxLayout(self._metrics_bar)
        bar.setContentsMargins(24, 8, 24, 8)
        bar.setSpacing(40)

        self._bar_labels: dict[str, QLabel] = {}
        for key, label, color in [
            ("n_train", "Trajectoires entr.", "#9CA3AF"),
            ("r2_x",    "R² x",              CLR_SUCCESS),
            ("r2_y",    "R² y",              CLR_SUCCESS),
            ("rmse_x",  "RMSE x",            "#F87171"),
            ("rmse_y",  "RMSE y",            "#F87171"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            k_lbl = QLabel(label)
            k_lbl.setStyleSheet(
                f"color:#6B7280; font-size:{FS_XS}; background:transparent;"
            )
            v_lbl = QLabel("—")
            v_lbl.setStyleSheet(
                f"color:{color}; font-size:{FS_SM}; font-weight:500;"
                f" background:transparent;"
            )
            col.addWidget(k_lbl)
            col.addWidget(v_lbl)
            bar.addLayout(col)
            self._bar_labels[key] = v_lbl

        bar.addStretch()
        note = QLabel("données synthétiques (sim cône)")
        note.setStyleSheet(
            f"color:#4B5563; font-size:{FS_XS}; background:transparent;"
        )
        bar.addWidget(note)

        lay.addWidget(self._metrics_bar, stretch=0)
        lay.addWidget(self._build_model_presets_bar(), stretch=0)
        lay.addWidget(self._build_ci_bar(), stretch=0)
        return page

    def _build_model_presets_bar(self) -> QWidget:
        """Barre de 6 boutons preset pré-calculés (RL×3 + MLP×3)."""
        bar = QWidget()
        bar.setStyleSheet("background:#0D1117; border-top:1px solid #1E293B;")
        bar.setFixedHeight(44)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 6, 16, 6)
        lay.setSpacing(6)

        lbl = QLabel("Presets :")
        lbl.setStyleSheet(f"color:#6B7280; font-size:{FS_XS}; background:transparent;")
        lay.addWidget(lbl)

        _INACTIVE = (
            "QPushButton {"
            "  background:#1F2937; color:#9CA3AF;"
            f" font-size:{FS_XS}; border-radius:4px; padding:2px 10px;"
            "}"
            "QPushButton:hover { background:#374151; }"
        )
        _ACTIVE = (
            "QPushButton {"
            "  background:#2563EB; color:#FFFFFF;"
            f" font-size:{FS_XS}; border-radius:4px; padding:2px 10px;"
            "}"
        )

        # Séparateur entre RL et MLP
        for model_tag, model_label, ns_list in [
            ("rl",  "RL",  _PRESET_N_SIMS),
            ("mlp", "MLP", _PRESET_N_SIMS),
        ]:
            sep = QLabel(f"  {model_label}")
            sep.setStyleSheet(
                f"color:#4B5563; font-size:{FS_XS}; background:transparent;"
            )
            lay.addWidget(sep)
            for i, n in enumerate(ns_list):
                key = f"{model_tag}_{n}"
                btn = QPushButton(_PRESET_LABELS[i])
                btn.setFixedHeight(28)
                btn.setStyleSheet(_INACTIVE)
                btn.setProperty("_preset_key", key)
                btn.setProperty("_inactive_style", _INACTIVE)
                btn.setProperty("_active_style",   _ACTIVE)
                btn.clicked.connect(lambda checked=False, k=key: self._apply_model_preset(k))
                lay.addWidget(btn)
                self._preset_btns[key] = btn

        lay.addStretch()
        return bar

    def _apply_model_preset(self, key: str) -> None:
        """Injecte directement un preset pré-calculé sans re-entraîner."""
        if key not in self._precomputed:
            log.warning("Preset '%s' non disponible.", key)
            return

        p = self._precomputed[key]
        self._pred_np = p["pred_np"]
        self.metrics  = p["metrics"]

        # Mise à jour des labels de métriques
        m = p["metrics"]
        self._bar_labels["n_train"].setText(str(m.get("n_train", "—")))
        self._bar_labels["r2_x"].setText(  f"{m.get('r2_x',  0):.3f}")
        self._bar_labels["r2_y"].setText(  f"{m.get('r2_y',  0):.3f}")
        self._bar_labels["rmse_x"].setText(f"{m.get('rmse_x',0):.4f} m")
        self._bar_labels["rmse_y"].setText(f"{m.get('rmse_y',0):.4f} m")

        # Surlignage du bouton actif
        for k, btn in self._preset_btns.items():
            btn.setStyleSheet(
                btn.property("_active_style") if k == key
                else btn.property("_inactive_style")
            )

        # Relance l'animation depuis le début
        self._reset_animation()

    def _build_ci_bar(self) -> QWidget:
        """Barre de contrôle des conditions initiales de test."""
        bar = QWidget()
        bar.setStyleSheet("background:#0F172A; border-top:1px solid #1E293B;")
        bar.setFixedHeight(62)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 8, 24, 8)
        lay.setSpacing(0)

        # r0 va jusqu'à 0.39 pour couvrir LAUNCH_R0=0.36 (hors distribution ML [0.08,0.35])
        _CI = [
            ("r0",   "r₀",  "m",   0.08, 0.39,  0.01, ".2f"),
            ("v0",   "v₀",  "m/s", 0.10, 2.50,  0.05, ".2f"),
            ("phi0", "φ₀",  "°",   0.0,  355.0,  5.0, ".0f"),
        ]

        for i, (attr, lbl_txt, unit, lo, hi, step, fmt) in enumerate(_CI):
            if i:
                sep = QLabel("|")
                sep.setStyleSheet("color:#1E293B; background:transparent; padding:0 16px;")
                lay.addWidget(sep)

            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet(
                f"color:#9CA3AF; font-size:{FS_SM}; font-weight:500;"
                f" background:transparent; min-width:22px;"
            )
            lay.addWidget(lbl)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setFixedWidth(150)
            cur = getattr(self.params, attr, lo)
            slider.setValue(int((cur - lo) / (hi - lo) * 100))
            slider.setStyleSheet(
                "QSlider::groove:horizontal{height:4px;background:#374151;border-radius:2px;}"
                f"QSlider::handle:horizontal{{width:14px;height:14px;margin:-5px 0;"
                f"background:{CLR_PRIMARY};border-radius:7px;}}"
                "QSlider::sub-page:horizontal{background:#3B82F6;border-radius:2px;}"
            )
            lay.addWidget(slider)

            val_lbl = QLabel(f"{cur:{fmt}} {unit}")
            val_lbl.setStyleSheet(
                f"color:white; font-size:{FS_XS}; font-family:monospace;"
                f" background:transparent; min-width:64px; padding-left:8px;"
            )
            lay.addWidget(val_lbl)

            self._ci_sliders[attr]    = slider
            self._ci_val_labels[attr] = val_lbl

            slider.valueChanged.connect(
                lambda pos, a=attr, l=lo, h=hi, s=step, f=fmt, u=unit, vl=val_lbl:
                    self._on_ci_slider(a, l, h, s, f, u, pos, vl)
            )

        lay.addStretch()
        return bar

    # ── Slot de progression (main thread) ────────────────────────────────────

    @Slot(int, int)
    def _on_progress(self, current: int, total: int) -> None:
        pct = int(current / max(total, 1) * 100)
        self._progress_bar.setValue(pct)
        self._loading_status.setText(f"Simulation {current} / {total}")

    # ── CI sliders (main thread) ──────────────────────────────────────────────

    def _on_ci_slider(
        self, attr: str, lo: float, hi: float, step: float,
        fmt: str, unit: str, pos: int, val_lbl: QLabel,
    ) -> None:
        """Mise à jour d'un slider CI : recalcule la prédiction instantanément."""
        raw = lo + pos / 100.0 * (hi - lo)
        val = round(round(raw / step) * step, 10)
        setattr(self.params, attr, val)
        val_lbl.setText(f"{val:{fmt}} {unit}")
        if self._lr_x is not None:
            self._do_predict()
            self._update_truth_visibility()
            self._reset_animation()

    def _sync_ci_sliders(self) -> None:
        """Synchronise les sliders CI avec self.params (après preset ou cache)."""
        _CI = [
            ("r0",   0.08, 0.39,  0.01, ".2f", "m"),
            ("v0",   0.10, 2.50,  0.05, ".2f", "m/s"),
            ("phi0", 0.0,  355.0,  5.0, ".0f", "°"),
        ]
        for attr, lo, hi, _, fmt, unit in _CI:
            if attr not in self._ci_sliders:
                continue
            val = getattr(self.params, attr, lo)
            slider = self._ci_sliders[attr]
            slider.blockSignals(True)
            slider.setValue(int((val - lo) / (hi - lo) * 100))
            slider.blockSignals(False)
            self._ci_val_labels[attr].setText(f"{val:{fmt}} {unit}")

    # ── Vérité terrain conditionnelle ─────────────────────────────────────────

    def _find_matching_preset(self) -> str | None:
        """Retourne la clé du preset dont les CI correspondent aux paramètres courants."""
        for key, preset in SimToRealParams.PRESENTATION_PRESETS.items():
            if (abs(self.params.r0   - preset["r0"])   < 0.006 and
                    abs(self.params.v0   - preset["v0"])   < 0.03  and
                    abs(self.params.phi0 - preset["phi0"]) < 3.0):
                return key
        return None

    def _update_truth_visibility(self) -> None:
        """Affiche la trajectoire réelle si les CI correspondent à un preset."""
        key = self._find_matching_preset()
        if key and key in self._ref_trajs:
            ref = self._ref_trajs[key]
            self._truth_curve.setData(ref[:, 0], ref[:, 1])
        else:
            self._truth_curve.setData([], [])

    # ── Prédiction légère (main thread) ───────────────────────────────────────

    def _do_predict(self) -> None:
        """Prédit la trajectoire depuis les CI courantes — O(_N_IN) simulation + O(1) ML.

        Simule les _N_IN premiers pas (contexte), construit le vecteur de features,
        puis appelle le modèle sélectionné (RL ou MLP). Le résultat est dans self._pred_np.
        """
        use_mlp = self.params.model_type == MLModel.MLP
        model_x = self._mlp_x if use_mlp else self._lr_x
        model_y = self._mlp_y if use_mlp else self._lr_y
        if model_x is None or model_y is None:
            return

        phi_rad = math.radians(self.params.phi0)
        vx0 = self.params.v0 * math.cos(phi_rad)
        vy0 = self.params.v0 * math.sin(phi_rad)

        # Simulation courte pour obtenir les _N_IN points de contexte.
        # On passe n_frames=_N_IN+1 pour ne pas simuler 3000 frames inutilement.
        ctx_raw = _run_cone(self.params.r0, self.params.v0, self.params.phi0,
                            n_frames=_N_IN + 1)
        # Sécurité : répéter le dernier point si simulation trop courte (rare)
        while len(ctx_raw) < _N_IN:
            ctx_raw.append(ctx_raw[-1])

        ctx_x = np.array([pt[0] for pt in ctx_raw[:_N_IN]])
        ctx_y = np.array([pt[1] for pt in ctx_raw[:_N_IN]])

        feat   = _make_feat(ctx_x, ctx_y, vx0, vy0).reshape(1, -1)
        pred_x = model_x.predict(feat)[0]   # (_N_OUT,)
        pred_y = model_y.predict(feat)[0]   # (_N_OUT,)

        # _pred_np = contexte simulé + prédiction ML
        context        = np.column_stack([ctx_x, ctx_y])          # (_N_IN, 2)
        predicted      = np.column_stack([pred_x, pred_y])        # (_N_OUT, 2)
        self._pred_np  = np.vstack([context, predicted])          # (_N_IN+_N_OUT, 2)
        self._n_frames = len(self._pred_np)

    def _reset_animation(self) -> None:
        """Remet l'animation à zéro avec la nouvelle prédiction (main thread)."""
        if not self._ready or not len(self._pred_np):
            return
        self.stop()
        self.frame      = 0
        self._frame_acc = 0.0
        x0, y0 = self._pred_np[0]
        self._pred_curve.setData([], [])
        self._cursor.setData([x0], [y0])
        self.frame_updated.emit(0)
        self.timer.start()

    # ── Override setup() — court-circuit pour les changements de CI ───────────

    def setup(self) -> None:
        """Si seules les CI ont changé (modèles déjà entraînés), prédit sans thread."""
        if self._lr_x is not None and self.params.n_sims == self._last_n_sims:
            self.stop()
            self._do_predict()
            self._sync_ci_sliders()
            self._update_truth_visibility()
            if hasattr(self, "_bar_labels"):
                self._update_metrics_bar()
            self.frame      = 0
            self._frame_acc = 0.0
            if self._ready:
                x0, y0 = self._pred_np[0]
                self._pred_curve.setData([], [])
                self._cursor.setData([x0], [y0])
                self.frame_updated.emit(0)
                self.setup_done.emit()
                if self._start_after_setup:
                    self._start_after_setup = False
                    self.timer.start()
        else:
            # Ré-entraînement complet : rebascule sur l'écran de chargement
            if hasattr(self, "_stack"):
                self._stack.setCurrentIndex(0)
                self._progress_bar.setValue(0)
                self._loading_subtitle.setText(
                    f"Chargement de {self.params.n_sims} trajectoires depuis le pool…"
                )
                self._loading_status.setText("Démarrage…")
            super().setup()

    # ── Cache ─────────────────────────────────────────────────────────────────

    def _get_cache_data(self) -> dict:
        return {
            "_result":      self._result,
            "_n_frames":    self._n_frames,
            "metrics":      self.metrics,
            "_lr_x":        self._lr_x,
            "_lr_y":        self._lr_y,
            "_mlp_x":       self._mlp_x,
            "_mlp_y":       self._mlp_y,
            "_ref_trajs":   self._ref_trajs,
            "_last_n_sims": self._last_n_sims,
        }

    def _set_cache_data(self, data: dict) -> None:
        self._result      = data["_result"]
        self._n_frames    = data["_n_frames"]
        self.metrics      = data["metrics"]
        self._lr_x        = data.get("_lr_x")
        self._lr_y        = data.get("_lr_y")
        self._mlp_x       = data.get("_mlp_x")
        self._mlp_y       = data.get("_mlp_y")
        self._ref_trajs   = data.get("_ref_trajs", {})
        self._last_n_sims = data.get("_last_n_sims", -1)

    # ── Calcul (QThread) ──────────────────────────────────────────────────────

    def _compute(self) -> None:
        data = load_pool(n_sims=self.params.n_sims)
        if data is None:
            raise RuntimeError(
                "Pool synthétique introuvable. "
                "Relancez l'application pour le régénérer."
            )

        result = train_and_evaluate(data["trajectories"])
        self._result      = result
        self.metrics      = result["metrics_lr"]
        self._lr_x        = result["lr_x"]
        self._lr_y        = result["lr_y"]
        self._mlp_x       = result["mlp_x"]
        self._mlp_y       = result["mlp_y"]
        self._ref_trajs   = data["ref_trajs"]
        self._last_n_sims = self.params.n_sims
        self._do_predict()

    # ── Rendu (main thread) ───────────────────────────────────────────────────

    def _draw_initial(self) -> None:
        self._stack.setCurrentIndex(1)

        # Charge les presets pré-calculés une seule fois
        if not self._precomputed:
            loaded = load_presets()
            if loaded:
                self._precomputed = loaded

        for c in self._train_curves:
            self._plot_widget.removeItem(c)
        self._train_curves.clear()

        r = self._result
        if not r:
            return

        # Trajectoires d'entraînement — max _MAX_DISPLAY_TRAJS courbes grises
        # (x_full/y_full sont None pour les trajectoires au-delà de _MAX_DISPLAY_TRAJS)
        trajs_to_show = [t for t in r["train_trajs"] if t.get("x_full") is not None]
        for traj in trajs_to_show:
            c = self._plot_widget.plot(
                traj["x_full"].tolist(), traj["y_full"].tolist(), pen=_PEN_TRAIN
            )
            self._train_curves.append(c)

        # Vérité terrain conditionnelle (preset uniquement)
        self._update_truth_visibility()

        # Prédiction initiale (_do_predict déjà appelé dans _compute)
        x0, y0 = self._pred_np[0]
        self._pred_curve.setData([], [])
        self._cursor.setData([x0], [y0])

        self._sync_ci_sliders()
        self._update_metrics_bar()

        self.frame_updated.emit(0)

    def _update_metrics_bar(self) -> None:
        """Met à jour la barre de métriques selon le modèle actif."""
        use_mlp = self.params.model_type == MLModel.MLP
        m = self._result.get("metrics_mlp" if use_mlp else "metrics_lr", self.metrics)
        self.metrics = m
        self._bar_labels["n_train"].setText(str(m.get("n_train", "—")))
        self._bar_labels["r2_x"].setText(  f"{m.get('r2_x',  0):.3f}")
        self._bar_labels["r2_y"].setText(  f"{m.get('r2_y',  0):.3f}")
        self._bar_labels["rmse_x"].setText(f"{m.get('rmse_x',0):.4f} m")
        self._bar_labels["rmse_y"].setText(f"{m.get('rmse_y',0):.4f} m")

    def _draw(self, i: int) -> None:
        if not (0 <= i < len(self._pred_np)):
            return
        trail = self._pred_np[:i + 1]
        self._pred_curve.setData(trail[:, 0], trail[:, 1])
        self._cursor.setData([self._pred_np[i, 0]], [self._pred_np[i, 1]])

    # ── Métriques (mode libre) ────────────────────────────────────────────────

    def format_metrics(self) -> str:
        if not self.metrics:
            return ""
        m = self.metrics
        return (
            f"n_train : {m.get('n_train', '?')}   "
            f"R² x : {m.get('r2_x', 0):.3f}   R² y : {m.get('r2_y', 0):.3f}   "
            f"RMSE x : {m.get('rmse_x', 0):.4f} m   RMSE y : {m.get('rmse_y', 0):.4f} m"
        )

    def get_metrics_schema(self) -> list[dict]:
        from src.utils.theme import CLR_DANGER, CLR_PRIMARY, CLR_SUCCESS
        schema = [
            {"key": "prog", "label": "Progression", "unit": "%",  "fmt": ".0f", "color": CLR_PRIMARY},
            {"key": "x",    "label": "x prédit",    "unit": "m",  "fmt": ".4f", "color": "#9CA3AF"},
            {"key": "y",    "label": "y prédit",    "unit": "m",  "fmt": ".4f", "color": "#9CA3AF"},
        ]
        if self.metrics:
            schema += [
                {"key": "r2_x",   "label": "R² x",   "unit": "",  "fmt": ".3f", "color": CLR_SUCCESS},
                {"key": "r2_y",   "label": "R² y",   "unit": "",  "fmt": ".3f", "color": CLR_SUCCESS},
                {"key": "rmse_x", "label": "RMSE x", "unit": "m", "fmt": ".4f", "color": CLR_DANGER},
                {"key": "rmse_y", "label": "RMSE y", "unit": "m", "fmt": ".4f", "color": CLR_DANGER},
            ]
        return schema

    def get_frame_metrics(self, i: int) -> dict:
        if not (0 <= i < len(self._pred_np)):
            return {}
        x, y = float(self._pred_np[i, 0]), float(self._pred_np[i, 1])
        prog = (i + 1) / max(self._n_frames, 1) * 100.0
        d: dict = {"prog": prog, "x": x, "y": y}
        if self.metrics:
            d.update({k: self.metrics.get(k, 0.0) for k in ("r2_x", "r2_y", "rmse_x", "rmse_y")})
        return d
