"""Logique d'entraînement pour les modèles directs CI → trajectoire.

Entraînement direct (train_direct_synth) :
  1. Génère n_total trajectoires synthétiques complètes depuis le simulateur physique.
  2. Calcule target_len = médiane des longueurs, plafonnée à max_steps.
  3. Pour chaque contexte (fraction des trajectoires) :
       - Construit le dataset (X_ci, Y_traj) avec les trajectoires du contexte.
       - Entraîne DirectLinearModel et DirectMLPModel (scaler fitté par contexte).
       - Sauvegarde les .pkl dans models_dir.

Différences fondamentales avec train.py (step-by-step) :
  - Trajectoires entières conservées en mémoire (pas de chunks).
  - Pas d'entraînement incrémental — données chargées en une passe.
  - Scaler fitté par contexte (contrairement au scaler partagé du step-by-step) :
    pour les step models, chaque chunk est trop petit pour estimer les stats
    de la distribution globale, d'où la nécessité d'un scaler partagé calibré
    sur un échantillon uniforme. Pour les directs, X_ctx contient l'intégralité
    des CI du contexte en une fois → stats représentatives par construction.
"""

import gc
import logging
from pathlib import Path

import numpy as np

from ml.direct_models import (
    DirectLinearModel,
    DirectMLPModel,
    DirectModelBase,
    ci_to_features,
)
from physics.cone import compute_cone
from scripts.generate_data import _sample_initial_conditions

log = logging.getLogger(__name__)


# ── Génération de trajectoires complètes ──────────────────────────────────────


def generate_trajectories(
    n: int,
    phys_cfg: dict,
    gen_cfg: dict,
    rng: np.random.Generator,
) -> list[np.ndarray]:
    """Génère n trajectoires complètes en (r, θ, vr, vθ).

    Retourne une liste d'arrays de forme (T, 4) — longueur T variable.
    Les trajectoires plus courtes que min_steps sont ignorées.

    Utilise les mêmes paramètres que generate_data.py pour que les CI
    synthétiques soient cohérentes avec les chunks pré-calculés.
    """
    merged = {**phys_cfg, **gen_cfg}
    r0s, theta0s, vr0s, vth0s = _sample_initial_conditions(n, merged, rng)
    min_steps          = gen_cfg.get("min_steps", 50)
    rolling            = bool(phys_cfg.get("rolling", False))
    rolling_resistance = float(phys_cfg.get("rolling_resistance", 0.0))
    drag_coeff         = float(phys_cfg.get("drag_coeff", 0.0))

    trajs: list[np.ndarray] = []
    for i in range(n):
        traj = compute_cone(
            r0=float(r0s[i]),
            theta0=float(theta0s[i]),
            vr0=float(vr0s[i]),
            vtheta0=float(vth0s[i]),
            R=float(phys_cfg["R"]),
            depth=float(phys_cfg["depth"]),
            friction=float(phys_cfg["friction"]),
            g=float(phys_cfg["g"]),
            dt=float(phys_cfg["dt"]),
            n_steps=int(phys_cfg["n_steps"]),
            rolling=rolling,
            rolling_resistance=rolling_resistance,
            drag_coeff=drag_coeff,
        )
        if len(traj) >= max(2, min_steps):
            trajs.append(traj.astype(np.float32))

    return trajs


# ── Construction du dataset ────────────────────────────────────────────────────


def choose_target_len(trajs: list[np.ndarray], max_steps: int) -> int:
    """Longueur cible = médiane des longueurs, plafonnée à max_steps."""
    if not trajs:
        return max_steps
    return min(int(np.median([len(t) for t in trajs])), max_steps)


def build_dataset(
    trajs: list[np.ndarray],
    target_len: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Construit X (CI encodées, shape (N, 5)) et Y (trajectoires aplaties, shape (N, 4×T)).

    Les trajectoires plus courtes que target_len sont ignorées.
    Y contient la trajectoire depuis t=0 inclus :
      Y = [r₀, θ₀, vr₀, vθ₀, r₁, θ₁, vr₁, vθ₁, …]
    """
    X_list: list[np.ndarray] = []
    Y_list: list[np.ndarray] = []

    for traj in trajs:
        if len(traj) < target_len:
            continue
        X_list.append(ci_to_features(traj[0]))
        Y_list.append(traj[:target_len].flatten())

    n_out = target_len * 4
    if not X_list:
        return np.empty((0, 5), np.float32), np.empty((0, n_out), np.float32)
    return np.array(X_list, dtype=np.float32), np.array(Y_list, dtype=np.float32)


# ── API publique ───────────────────────────────────────────────────────────────


def train_direct_synth(
    phys_cfg:   dict,
    gen_cfg:    dict,
    contexts:   dict,
    n_total:    int   = 50_000,
    max_steps:  int   = 1_000,
    models_dir: Path  = Path("data/models"),
    seed:       int   = 0,
) -> dict[str, DirectModelBase]:
    """Génère des trajectoires synthétiques et entraîne DirectLinearModel + DirectMLPModel.

    Paramètres
    ----------
    phys_cfg   : paramètres physiques fusionnés (common.toml + synth.physics)
    gen_cfg    : paramètres de génération (synth.generation)
    contexts   : {"1pct": 0.01, "10pct": 0.10, …}
    n_total    : trajectoires pour le contexte 100pct (défaut : 50 000)
    max_steps  : plafond de target_len (défaut : 1 000 pas = 10 s à dt=0.01)
    models_dir : dossier de sauvegarde des .pkl
    seed       : graine aléatoire (défaut : 0 — train ; 999 réservé au test)

    Retourne
    --------
    dict {nom_fichier: modèle entraîné} pour tous les contextes × algos.
    """
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    # ── Génération du jeu complet (100pct) ────────────────────────────────────
    log.info("train_direct_synth : génération de %d trajectoires (seed=%d)", n_total, seed)
    rng      = np.random.default_rng(seed)
    all_trajs = generate_trajectories(n_total, phys_cfg, gen_cfg, rng)
    n_gen    = len(all_trajs)
    lengths  = [len(t) for t in all_trajs]
    log.info(
        "  %d trajectoires gardées — lon. méd=%d, p5=%d, p95=%d",
        n_gen,
        int(np.median(lengths)),
        int(np.percentile(lengths, 5)),
        int(np.percentile(lengths, 95)),
    )

    # target_len partagé pour tous les contextes — même dimension de sortie
    target_len = choose_target_len(all_trajs, max_steps)
    log.info("  target_len = %d pas", target_len)

    # Filtre les trajectoires trop courtes une seule fois
    trajs_ok = [t for t in all_trajs if len(t) >= target_len]
    del all_trajs
    gc.collect()

    if not trajs_ok:
        raise ValueError(
            f"Aucune trajectoire ≥ target_len={target_len}. Réduire --max-steps."
        )

    results: dict[str, DirectModelBase] = {}

    # ── Entraînement par contexte ──────────────────────────────────────────────
    # Le scaler est fitté par contexte sur les CI du contexte courant.
    # Contrairement au step-by-step (scaler partagé calibré sur tous les chunks),
    # ici X_ctx est entier en mémoire → statistiques représentatives par construction.
    for ctx_name, ctx_frac in contexts.items():
        n_ctx     = max(1, int(len(trajs_ok) * ctx_frac))
        trajs_ctx = trajs_ok[:n_ctx]
        X_ctx, Y_ctx = build_dataset(trajs_ctx, target_len)

        if len(X_ctx) == 0:
            log.warning("Contexte [%s] : aucune trajectoire valide — ignoré.", ctx_name)
            continue

        log.info("Contexte [%s] : %d trajectoires d'entraînement", ctx_name, len(X_ctx))

        # DirectLinearModel
        lr_model = DirectLinearModel(alpha=1.0, context=ctx_name)
        lr_model.fit(X_ctx, Y_ctx)
        name_lr = f"direct_linear_{ctx_name}.pkl"
        lr_model.save(models_dir / name_lr)
        results[name_lr] = lr_model
        log.info(
            "  DirectLinearModel [%s] — MAE r_train=%.5f  → %s",
            ctx_name, lr_model.mae_r_train, name_lr,
        )

        # DirectMLPModel
        mlp_model = DirectMLPModel(context=ctx_name)
        mlp_model.fit(X_ctx, Y_ctx)
        name_mlp = f"direct_mlp_{ctx_name}.pkl"
        mlp_model.save(models_dir / name_mlp)
        results[name_mlp] = mlp_model
        log.info(
            "  DirectMLPModel    [%s] — MAE r_train=%.5f  iters=%d  → %s",
            ctx_name, mlp_model.mae_r_train, mlp_model.n_iter_, name_mlp,
        )

        del X_ctx, Y_ctx
        gc.collect()

    return results
