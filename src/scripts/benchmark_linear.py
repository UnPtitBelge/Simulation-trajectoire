"""Benchmark LinearStepModel — précision vs nombre de trajectoires d'entraînement.

Génère les trajectoires à la volée (sans passer par les chunks pré-calculés),
entraîne depuis zéro sur n trajectoires (progression géométrique : 1, 2, 4, 8, …)
et mesure l'erreur contre la vérité terrain du simulateur physique.

Un chunk pré-généré contient ~10 000 paires — la régression linéaire y converge
déjà en grande partie. Ce script descend au niveau de la trajectoire individuelle
pour observer la convergence réelle depuis 1 trajectoire.

Usage :
    python src/scripts/benchmark_linear.py
    python src/scripts/benchmark_linear.py --n-trajectories 5000
    python src/scripts/benchmark_linear.py --n-contexts 25 --n-highlight 6
"""

import argparse
import sys
import time
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, state_to_features
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


# ── Progression géométrique ────────────────────────────────────────────────────


def _geom_steps(n_total: int, n_steps: int) -> list[int]:
    """Entiers uniques de 1 à n_total en progression géométrique."""
    raw = np.geomspace(1, n_total, n_steps)
    return sorted(set(max(1, int(round(v))) for v in raw))


# ── Visualisation ──────────────────────────────────────────────────────────────


def _plot(
    steps: list[int],
    errors: list[dict],
    trajs: dict[int, np.ndarray],
    true_traj: np.ndarray,
    highlight: list[int],
    R: float,
    dt: float,
) -> None:
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        "Benchmark LinearStepModel — précision vs nombre de trajectoires d'entraînement\n"
        "(progression géométrique : 1, 2, 4, 8, … trajectoires)",
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
                   label=f"Vrai ({n_true} pas)")
    ax_len.plot(n_arr, n_pred, color="steelblue", linewidth=2, label="Prédit")
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
        true_traj[:, 0] * np.cos(true_traj[:, 1]),
        true_traj[:, 0] * np.sin(true_traj[:, 1]),
        color="green", linewidth=2, label="Vérité terrain", zorder=5,
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
    ax_r.plot(np.arange(len(true_traj)) * dt, true_traj[:, 0],
              color="green", linewidth=2, label="Vrai", zorder=5)
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
        "--n-highlight", type=int, default=5,
        help="Trajectoires affichées sur les graphes XY/r(t) (défaut : 5)",
    )
    args = parser.parse_args()

    cfg     = load_config("ml")
    phys    = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg = cfg["synth"]["generation"]
    preset  = cfg["preset"]["default"]

    print(f"Génération de {args.n_trajectories} trajectoires d'entraînement…")
    rng   = np.random.default_rng(42)
    pairs = _generate_trajectories(args.n_trajectories, phys, gen_cfg, rng)
    print(f"  {len(pairs)} trajectoires valides générées")

    print("Calibration des scalers sur l'ensemble…")
    scaler_X, scaler_y = _fit_scalers(pairs)

    vr0, vth0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    init      = np.array([preset["r0"], preset["theta0"], vr0, vth0])
    true_traj = compute_cone(
        r0=float(init[0]), theta0=float(init[1]),
        vr0=float(init[2]), vtheta0=float(init[3]),
        R=phys["R"], depth=phys["depth"], friction=phys["friction"],
        g=phys["g"], dt=phys["dt"],
        n_steps=cfg["display"]["n_steps_pred"],
    )
    print(f"Vérité terrain : {len(true_traj)} pas\n")

    steps = _geom_steps(len(pairs), args.n_contexts)
    print(f"Étapes ({len(steps)}) : {steps}\n")

    r_max  = phys["R"]
    r_min  = phys["center_radius"]
    v_stop = phys["v_stop"]

    errors: list[dict]            = []
    trajs:  dict[int, np.ndarray] = {}

    print(f"{'Traj.':>8}  {'Paires':>8}  {'MAE r':>10}  {'MAE total':>10}  {'n_pred':>8}  {'temps':>7}")
    print("─" * 65)
    for n in steps:
        t0     = time.perf_counter()
        subset = pairs[:n]
        model  = _train(subset, scaler_X, scaler_y)
        traj   = predict_trajectory(
            model, init, cfg["display"]["n_steps_pred"],
            r_max=r_max, r_min=r_min, v_stop=v_stop,
        )
        elapsed = time.perf_counter() - t0
        errs    = _errors(traj, true_traj)
        n_pairs = sum(len(X) for X, _ in subset)
        errors.append(errs)
        trajs[n] = traj
        print(
            f"{n:>8}  {n_pairs:>8,}  {errs['mae_r']:>10.5f}  {errs['mae_total']:>10.5f}"
            f"  {errs['n_pred']:>8}  {elapsed:>6.2f}s"
        )

    hi_idx    = np.unique(np.round(np.linspace(0, len(steps) - 1, args.n_highlight)).astype(int))
    highlight = [steps[int(i)] for i in hi_idx]

    _plot(steps, errors, trajs, true_traj, highlight, r_max, phys["dt"])
