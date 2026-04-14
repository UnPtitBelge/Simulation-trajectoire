"""Benchmark LinearStepModel — précision vs nombre de trajectoires d'entraînement.

Mécanisme d'évolution du modèle
────────────────────────────────
LinearStepModel est une régression Ridge incrémentale. `partial_fit(X, y)` accule
XᵀX et Xᵀy (équations normales) puis résout W = (XᵀX + αI)⁻¹ Xᵀy à chaque appel.

À chaque étape n de la progression géométrique :
  1. Un modèle vierge est créé (compteurs XᵀX / Xᵀy remis à zéro).
  2. `partial_fit` est appelé une fois par trajectoire sur les n premières paires
     (états successifs de la simulation).  Chaque appel accumule les équations
     normales — l'ordre des trajectoires n'a pas d'importance pour le résultat final.
  3. La solution Ridge est calculée : W est la solution de moindres carrés
     régularisée (α = 0.001) sur la totalité des n × len(traj) paires.

Les scalers (StandardScaler sur X et sur les résidus Δ = feat(s_{t+1}) - feat(s_t))
sont calibrés UNE SEULE FOIS sur l'ensemble des --n-trajectories trajectoires.
Cela garantit une normalisation stable même pour les petits n, sans biais de
distribution.

Pourquoi trajectoire par trajectoire et non chunk par chunk ?
Un chunk pré-généré (~10 000 paires ≈ plusieurs trajectoires complètes) suffit à
approcher la convergence de la régression Ridge.  Ce script descend au niveau de la
trajectoire individuelle (~100–500 paires) pour observer la convergence réelle depuis
1 trajectoire d'entraînement.

Évaluation
──────────
Les métriques (MAE r, MAE total, longueur prédite) sont moyennées sur --n-test
trajectoires de test tirées indépendamment (seed=999 ≠ seed=42 pour l'entraînement).
Pour chaque cas de test, on compare la trajectoire prédite par le modèle à la
trajectoire physique exacte simulée avec les mêmes conditions initiales.

Usage :
    python src/scripts/benchmark_linear.py
    python src/scripts/benchmark_linear.py --n-trajectories 5000 --n-test 50
    python src/scripts/benchmark_linear.py --n-contexts 25 --n-highlight 6
"""

import argparse
import concurrent.futures as cf
import sys
import time
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, features_to_state, state_to_features
from ml.predict import predict_trajectory
from physics.cone import compute_cone
from scripts.generate_data import _sample_initial_conditions
from utils.angle import v0_dir_to_vr_vtheta


# ── Génération des trajectoires ────────────────────────────────────────────────


def _generate_trajectories(
    n: int, phys: dict, gen_cfg: dict, rng: np.random.Generator
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Simule n trajectoires aléatoires, retourne [(X_feat, y_feat), …].

    Les trajectoires trop courtes (< min_steps) sont ignorées — on continue
    jusqu'à obtenir n trajectoires valides.
    """
    min_steps = gen_cfg.get("min_steps", 50)
    merged    = {**phys, **gen_cfg}
    pairs: list[tuple[np.ndarray, np.ndarray]] = []

    batch = max(n, 64)          # sur-échantillonnage pour compenser les rejets
    while len(pairs) < n:
        r0, th0, vr0, vth0 = _sample_initial_conditions(batch, merged, rng)
        for i in range(batch):
            if len(pairs) >= n:
                break
            traj = compute_cone(
                r0=float(r0[i]), theta0=float(th0[i]),
                vr0=float(vr0[i]), vtheta0=float(vth0[i]),
                R=phys["R"], depth=phys["depth"],
                friction=phys["friction"], g=phys["g"],
                dt=phys["dt"], n_steps=phys["n_steps"],
            )
            if len(traj) >= min_steps:
                X = state_to_features(traj[:-1].astype(np.float32))
                y = state_to_features(traj[1:].astype(np.float32))
                pairs.append((X, y))

    return pairs


# ── Scalers ───────────────────────────────────────────────────────────────────


def _fit_scalers(pairs: list[tuple[np.ndarray, np.ndarray]]):
    """Calibre scaler_X et scaler_y sur toutes les trajectoires disponibles."""
    from sklearn.preprocessing import StandardScaler

    X_all   = np.vstack([X for X, _ in pairs])
    res_all = np.vstack([y - X for X, y in pairs])
    scaler_X = StandardScaler().fit(X_all)
    scaler_y = StandardScaler().fit(res_all)
    return scaler_X, scaler_y


# ── Entraînement ───────────────────────────────────────────────────────────────


def _train(
    pairs: list[tuple[np.ndarray, np.ndarray]],
    scaler_X,
    scaler_y,
) -> LinearStepModel:
    """Entraîne LinearStepModel depuis zéro sur les paires données (1 passe)."""
    model = LinearStepModel()
    model.inject_scalers(scaler_X, scaler_y)
    for X, y in pairs:
        model.partial_fit(X, y)
    return model


# ── Métriques ──────────────────────────────────────────────────────────────────


def _errors(pred: np.ndarray, true: np.ndarray) -> dict:
    n = min(len(pred), len(true))
    d = np.abs(pred[:n] - true[:n])
    return {
        "n_pred":    len(pred),
        "n_true":    len(true),
        "mae_r":     float(d[:, 0].mean()),
        "mae_theta": float(d[:, 1].mean()),
        "mae_vr":    float(d[:, 2].mean()),
        "mae_vtheta":float(d[:, 3].mean()),
        "mae_total": float(d.mean()),
    }


def _mean_errors(
    model: LinearStepModel,
    test_cases: list[tuple[np.ndarray, np.ndarray]],
    n_steps: int,
    r_max: float,
    r_min: float,
    v_stop: float,
) -> dict:
    """Moyenne des métriques sur tous les cas de test.

    test_cases : liste de (init_state, true_traj) simulés indépendamment.
    """
    all_errs = []
    for init, true_traj in test_cases:
        pred = predict_trajectory(model, init, n_steps, r_max=r_max, r_min=r_min, v_stop=v_stop)
        all_errs.append(_errors(pred, true_traj))
    return {
        "n_pred":    float(np.mean([e["n_pred"]    for e in all_errs])),
        "n_true":    float(np.mean([e["n_true"]    for e in all_errs])),
        "mae_r":     float(np.mean([e["mae_r"]     for e in all_errs])),
        "mae_theta": float(np.mean([e["mae_theta"] for e in all_errs])),
        "mae_vr":    float(np.mean([e["mae_vr"]    for e in all_errs])),
        "mae_vtheta":float(np.mean([e["mae_vtheta"]for e in all_errs])),
        "mae_total": float(np.mean([e["mae_total"] for e in all_errs])),
    }


# ── Progression géométrique ────────────────────────────────────────────────────


def _geom_steps(n_total: int, n_steps: int) -> list[int]:
    """Entiers uniques de 1 à n_total en progression géométrique."""
    raw = np.geomspace(1, n_total, n_steps)
    return sorted(set(max(1, int(round(v))) for v in raw))


# ── Workers parallèles ─────────────────────────────────────────────────────────

# État partagé, injecté une seule fois par processus worker via l'initializer.
_shared: dict = {}


def _init_worker(
    pairs: list,
    scaler_X,
    scaler_y,
    test_cases: list,
    n_steps: int,
    r_max: float,
    r_min: float,
    v_stop: float,
    ref_init: np.ndarray,
) -> None:
    """Copie les données lourdes dans le processus worker (une seule fois)."""
    _shared["pairs"]      = pairs
    _shared["scaler_X"]   = scaler_X
    _shared["scaler_y"]   = scaler_y
    _shared["test_cases"] = test_cases
    _shared["n_steps"]    = n_steps
    _shared["r_max"]      = r_max
    _shared["r_min"]      = r_min
    _shared["v_stop"]     = v_stop
    _shared["ref_init"]   = ref_init


def _run_step(n: int) -> tuple[int, dict, np.ndarray, float]:
    """Entraîne et évalue le modèle sur les n premières trajectoires."""
    t0     = time.perf_counter()
    subset = _shared["pairs"][:n]
    model  = _train(subset, _shared["scaler_X"], _shared["scaler_y"])
    errs   = _mean_errors(
        model, _shared["test_cases"],
        _shared["n_steps"], _shared["r_max"], _shared["r_min"], _shared["v_stop"],
    )
    traj = predict_trajectory(
        model, _shared["ref_init"], _shared["n_steps"],
        r_max=_shared["r_max"], r_min=_shared["r_min"], v_stop=_shared["v_stop"],
    )
    return n, errs, traj, time.perf_counter() - t0


# ── Visualisation ──────────────────────────────────────────────────────────────


def _plot(
    steps: list[int],
    errors: list[dict],
    trajs: dict[int, np.ndarray],
    ref_traj: np.ndarray,
    highlight: list[int],
    R: float,
    dt: float,
    n_test: int,
) -> None:
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"Benchmark LinearStepModel — précision vs nombre de trajectoires d'entraînement\n"
        f"(progression géométrique : 1, 2, 4, 8, … — métriques moyennées sur {n_test} trajectoires de test)",
        fontsize=12,
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32)

    n_arr   = np.array(steps)
    mae_r   = np.array([e["mae_r"]    for e in errors])
    mae_tot = np.array([e["mae_total"] for e in errors])
    n_pred  = np.array([e["n_pred"]   for e in errors])
    n_true  = errors[0]["n_true"]

    palette = plt.cm.plasma(np.linspace(0.1, 0.9, len(highlight)))  # type: ignore

    # ── MAE vs trajectoires ───────────────────────────────────────────────
    ax_mae = fig.add_subplot(gs[0, 0])
    ax_mae.plot(n_arr, mae_r,   color="steelblue",  linewidth=2,   label="MAE r (m)")
    ax_mae.plot(n_arr, mae_tot, color="darkorange",  linewidth=1.5, linestyle="--",
                label="MAE total")
    for i, n in enumerate(highlight):
        ax_mae.axvline(n, color=palette[i], linestyle=":", linewidth=1, alpha=0.6)
    ax_mae.set_xscale("log")
    ax_mae.set_title("Erreur MAE vs trajectoires d'entraînement")
    ax_mae.set_xlabel("Trajectoires (échelle log)")
    ax_mae.set_ylabel("MAE (m)")
    ax_mae.legend(fontsize=9)
    ax_mae.grid(True, alpha=0.3, which="both")

    # ── Longueur prédite ──────────────────────────────────────────────────
    ax_len = fig.add_subplot(gs[0, 1])
    ax_len.axhline(n_true, color="green", linestyle="--", linewidth=1.5,
                   label=f"Vrai (moy. {n_true:.0f} pas)")
    ax_len.plot(n_arr, n_pred, color="steelblue", linewidth=2, label="Prédit (moy.)")
    for i, n in enumerate(highlight):
        ax_len.axvline(n, color=palette[i], linestyle=":", linewidth=1, alpha=0.6)
    ax_len.set_xscale("log")
    ax_len.set_title("Longueur de trajectoire prédite")
    ax_len.set_xlabel("Trajectoires (échelle log)")
    ax_len.set_ylabel("Nombre de pas")
    ax_len.legend(fontsize=9)
    ax_len.grid(True, alpha=0.3, which="both")

    # ── Trajectoires XY ───────────────────────────────────────────────────
    ax_xy = fig.add_subplot(gs[1, 0])
    ang = np.linspace(0, 2 * np.pi, 200)
    ax_xy.plot(R * np.cos(ang), R * np.sin(ang),
               color="gray", linestyle="--", linewidth=1)
    ax_xy.plot(
        ref_traj[:, 0] * np.cos(ref_traj[:, 1]),
        ref_traj[:, 0] * np.sin(ref_traj[:, 1]),
        color="green", linewidth=2, label="Vérité terrain (preset)", zorder=5,
    )
    for i, n in enumerate(highlight):
        traj = trajs.get(n)
        if traj is None:
            continue
        ax_xy.plot(
            traj[:, 0] * np.cos(traj[:, 1]),
            traj[:, 0] * np.sin(traj[:, 1]),
            color=palette[i], linewidth=1.2, alpha=0.85, label=f"{n} traj.",
        )
    ax_xy.set_aspect("equal")
    ax_xy.set_title("Trajectoire — vue de dessus")
    ax_xy.set_xlabel("x (m)")
    ax_xy.set_ylabel("y (m)")
    ax_xy.legend(fontsize=8)
    ax_xy.grid(True, alpha=0.25)

    # ── r(t) ─────────────────────────────────────────────────────────────
    ax_r = fig.add_subplot(gs[1, 1])
    ax_r.plot(np.arange(len(ref_traj)) * dt, ref_traj[:, 0],
              color="green", linewidth=2, label="Vrai (preset)", zorder=5)
    for i, n in enumerate(highlight):
        traj = trajs.get(n)
        if traj is None:
            continue
        ax_r.plot(np.arange(len(traj)) * dt, traj[:, 0],
                  color=palette[i], linewidth=1.2, alpha=0.85, label=f"{n} traj.")
    ax_r.set_title("r(t)")
    ax_r.set_xlabel("t (s)")
    ax_r.set_ylabel("r (m)")
    ax_r.legend(fontsize=8)
    ax_r.grid(True, alpha=0.25)

    plt.show()


# ── Main ───────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n-trajectories", type=int, default=2000,
        help="Nombre max de trajectoires d'entraînement (défaut : 2000)",
    )
    parser.add_argument(
        "--n-contexts", type=int, default=20,
        help="Nombre de points sur la progression géométrique (défaut : 20)",
    )
    parser.add_argument(
        "--n-test", type=int, default=20,
        help="Trajectoires de test pour moyenner les métriques (défaut : 20)",
    )
    parser.add_argument(
        "--n-highlight", type=int, default=5,
        help="Trajectoires affichées sur les graphes XY/r(t) (défaut : 5)",
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Processus parallèles pour les étapes du benchmark (défaut : 1)",
    )
    args = parser.parse_args()

    cfg     = load_config("ml")
    phys    = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg = cfg["synth"]["generation"]
    preset  = cfg["preset"]["default"]

    # ── Jeu d'entraînement ────────────────────────────────────────────────
    print(f"Génération de {args.n_trajectories} trajectoires d'entraînement…")
    rng   = np.random.default_rng(42)
    pairs = _generate_trajectories(args.n_trajectories, phys, gen_cfg, rng)
    print(f"  {len(pairs)} trajectoires valides générées")

    print("Calibration des scalers sur l'ensemble d'entraînement…")
    scaler_X, scaler_y = _fit_scalers(pairs)

    # ── Jeu de test indépendant ───────────────────────────────────────────
    print(f"Génération de {args.n_test} trajectoires de test (seed distinct)…")
    rng_test  = np.random.default_rng(999)
    n_steps   = cfg["display"]["n_steps_pred"]
    r_max     = phys["R"]
    r_min     = phys["center_radius"]
    v_stop    = phys["v_stop"]

    test_pairs_raw = _generate_trajectories(args.n_test, phys, gen_cfg, rng_test)
    test_inits     = []
    test_true_trajs: list[np.ndarray] = []
    for X, _ in test_pairs_raw:
        # Reconstruire l'état initial depuis la première ligne de features
        init_state = features_to_state(X[0]).astype(float)
        true_traj  = compute_cone(
            r0=float(init_state[0]), theta0=float(init_state[1]),
            vr0=float(init_state[2]), vtheta0=float(init_state[3]),
            R=phys["R"], depth=phys["depth"], friction=phys["friction"],
            g=phys["g"], dt=phys["dt"], n_steps=n_steps,
        )
        test_inits.append(init_state)
        test_true_trajs.append(true_traj)

    test_cases = list(zip(test_inits, test_true_trajs))
    print(f"  {len(test_cases)} cas de test prêts\n")

    # ── Trajectoire de référence (preset) pour les plots XY / r(t) ───────
    vr0, vth0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    ref_init  = np.array([preset["r0"], preset["theta0"], vr0, vth0])
    ref_true  = compute_cone(
        r0=float(ref_init[0]), theta0=float(ref_init[1]),
        vr0=float(ref_init[2]), vtheta0=float(ref_init[3]),
        R=phys["R"], depth=phys["depth"], friction=phys["friction"],
        g=phys["g"], dt=phys["dt"], n_steps=n_steps,
    )

    steps = _geom_steps(len(pairs), args.n_contexts)
    print(f"Étapes ({len(steps)}) : {steps}\n")

    errors: list[dict]            = []
    trajs:  dict[int, np.ndarray] = {}   # pred sur le preset (pour les plots)

    n_workers = min(args.workers, len(steps))
    initargs  = (pairs, scaler_X, scaler_y, test_cases, n_steps, r_max, r_min, v_stop, ref_init)
    print(f"{'Traj.':>8}  {'Paires':>8}  {'MAE r':>10}  {'MAE total':>10}  {'n_pred moy':>12}  {'temps':>7}")
    print("─" * 72)
    with cf.ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_init_worker,
        initargs=initargs,
    ) as pool:
        for n, errs, traj, elapsed in pool.map(_run_step, steps):
            n_pairs  = sum(len(X) for X, _ in pairs[:n])
            errors.append(errs)
            trajs[n] = traj
            print(
                f"{n:>8}  {n_pairs:>8,}  {errs['mae_r']:>10.5f}  {errs['mae_total']:>10.5f}"
                f"  {errs['n_pred']:>12.1f}  {elapsed:>6.2f}s"
            )

    hi_idx    = np.unique(np.round(np.linspace(0, len(steps) - 1, args.n_highlight)).astype(int))
    highlight = [steps[int(i)] for i in hi_idx]

    _plot(steps, errors, trajs, ref_true, highlight, r_max, phys["dt"], args.n_test)
