"""Comparaison de la distribution des états : mode aléatoire vs grille.

Génère un petit jeu de données pour chaque mode, simule les trajectoires,
et compare les distributions des états résultants dans l'espace d'entraînement.

Ce qui est comparé :
  - Distribution des rayons r (position sur le cône)
  - Distribution des vitesses |v|
  - Couverture de l'espace (r, |v|) — heatmap 2D
  - Couverture de l'espace (vr, vθ) — heatmap 2D
  - Distribution des longueurs de trajectoire

Usage :
    python src/scripts/test_data_distribution.py
    python src/scripts/test_data_distribution.py --n-random 3000
    python src/scripts/test_data_distribution.py --n-r 20 --n-theta 24 --n-v 4 --n-dir 8
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from physics.cone import compute_cone
from scripts.generate_data import (
    _sample_initial_conditions,
    _sample_initial_conditions_grid,
)


# ── Simulation ─────────────────────────────────────────────────────────────────


def simulate_trajectories(
    r0: np.ndarray,
    theta0: np.ndarray,
    vr0: np.ndarray,
    vtheta0: np.ndarray,
    phys_cfg: dict,
    gen_cfg: dict,
) -> tuple[list[np.ndarray], list[int]]:
    """Simule toutes les CI et retourne (liste de trajectoires, longueurs).

    Chaque trajectoire est un array (N, 4) = (r, θ, vr, vθ).
    Les trajectoires trop courtes (< min_steps) sont exclues.
    """
    min_steps = gen_cfg.get("min_steps", 50)
    trajs: list[np.ndarray] = []
    lengths: list[int] = []

    for i in range(len(r0)):
        traj = compute_cone(
            r0=float(r0[i]), theta0=float(theta0[i]),
            vr0=float(vr0[i]), vtheta0=float(vtheta0[i]),
            R=phys_cfg["R"], depth=phys_cfg["depth"],
            friction=phys_cfg["friction"], g=phys_cfg["g"],
            dt=phys_cfg["dt"], n_steps=phys_cfg["n_steps"],
        )
        if len(traj) >= min_steps:
            trajs.append(traj)
            lengths.append(len(traj))

    return trajs, lengths


def collect_states(trajs: list[np.ndarray]) -> np.ndarray:
    """Concatène toutes les trajectoires en un seul array (N_total, 4)."""
    return np.vstack(trajs) if trajs else np.empty((0, 4))


# ── Affichage ──────────────────────────────────────────────────────────────────


def _hist2d(ax, x, y, bins, x_lim, y_lim, title, xlabel, ylabel, cmap="Blues"):
    h, xedges, yedges = np.histogram2d(x, y, bins=bins,
                                        range=[x_lim, y_lim], density=True)
    ax.imshow(
        h.T, origin="lower", aspect="auto", cmap=cmap,
        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
    )
    ax.set_title(title, fontsize=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def plot_comparison(
    rand_states: np.ndarray,
    grid_states: np.ndarray,
    rand_lengths: list[int],
    grid_lengths: list[int],
    R: float,
    n_rand_ci: int,
    n_grid_ci: int,
) -> None:
    """Figure 3×2 : distributions comparées mode aléatoire (bleu) vs grille (orange)."""
    fig = plt.figure(figsize=(15, 12))
    fig.suptitle(
        f"Distribution des états d'entraînement\n"
        f"Aléatoire : {n_rand_ci:,} CI → {len(rand_lengths):,} traj. "
        f"({sum(rand_lengths):,} états)   |   "
        f"Grille : {n_grid_ci:,} CI → {len(grid_lengths):,} traj. "
        f"({sum(grid_lengths):,} états)",
        fontsize=11,
    )
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

    r_rand  = rand_states[:, 0];  r_grid  = grid_states[:, 0]
    vr_rand = rand_states[:, 2];  vr_grid = grid_states[:, 2]
    vt_rand = rand_states[:, 3];  vt_grid = grid_states[:, 3]
    spd_rand = np.sqrt(vr_rand**2 + vt_rand**2)
    spd_grid = np.sqrt(vr_grid**2 + vt_grid**2)

    BINS = 60
    ALPHA = 0.65

    # ── Ligne 1 : r et |v| ────────────────────────────────────────────────────
    ax_r = fig.add_subplot(gs[0, 0])
    r_bins = np.linspace(0, R, BINS + 1)
    ax_r.hist(r_rand, bins=r_bins, density=True, alpha=ALPHA,
              color="steelblue",  label=f"Aléatoire ({len(rand_lengths):,} traj.)")
    ax_r.hist(r_grid, bins=r_bins, density=True, alpha=ALPHA,
              color="darkorange", label=f"Grille ({len(grid_lengths):,} traj.)")
    # Densité uniforme théorique en surface : p(r) = 2r/R²
    r_th = np.linspace(0, R, 200)
    ax_r.plot(r_th, 2 * r_th / R**2, "k--", linewidth=1.5, label="Uniforme théorique")
    ax_r.set_title("Distribution de r (rayon)")
    ax_r.set_xlabel("r (m)")
    ax_r.set_ylabel("Densité")
    ax_r.legend(fontsize=8)
    ax_r.grid(True, alpha=0.25)

    ax_v = fig.add_subplot(gs[0, 1])
    v_max_plot = float(np.percentile(np.concatenate([spd_rand, spd_grid]), 99))
    v_bins = np.linspace(0, v_max_plot, BINS + 1)
    ax_v.hist(spd_rand, bins=v_bins, density=True, alpha=ALPHA,
              color="steelblue",  label="Aléatoire")
    ax_v.hist(spd_grid, bins=v_bins, density=True, alpha=ALPHA,
              color="darkorange", label="Grille")
    ax_v.set_title("Distribution de |v| (vitesse)")
    ax_v.set_xlabel("|v| (m/s)")
    ax_v.set_ylabel("Densité")
    ax_v.legend(fontsize=8)
    ax_v.grid(True, alpha=0.25)

    # ── Ligne 2 : heatmaps (r, |v|) ──────────────────────────────────────────
    spd_max = float(np.percentile(np.concatenate([spd_rand, spd_grid]), 99))
    ax_rv_rand = fig.add_subplot(gs[1, 0])
    _hist2d(ax_rv_rand, r_rand, spd_rand, bins=50,
            x_lim=[0, R], y_lim=[0, spd_max],
            title="Couverture (r, |v|) — Aléatoire",
            xlabel="r (m)", ylabel="|v| (m/s)", cmap="Blues")

    ax_rv_grid = fig.add_subplot(gs[1, 1])
    _hist2d(ax_rv_grid, r_grid, spd_grid, bins=50,
            x_lim=[0, R], y_lim=[0, spd_max],
            title="Couverture (r, |v|) — Grille",
            xlabel="r (m)", ylabel="|v| (m/s)", cmap="Oranges")

    # ── Ligne 3 : heatmaps (vr, vθ) et longueurs ─────────────────────────────
    vmax_plot = float(np.percentile(
        np.abs(np.concatenate([vr_rand, vr_grid, vt_rand, vt_grid])), 99
    ))
    v_lim = [-vmax_plot, vmax_plot]

    ax_vv_rand = fig.add_subplot(gs[2, 0])
    _hist2d(ax_vv_rand, vr_rand, vt_rand, bins=50,
            x_lim=v_lim, y_lim=v_lim,
            title="Couverture (vr, vθ) — Aléatoire",
            xlabel="vr (m/s)", ylabel="vθ (m/s)", cmap="Blues")

    ax_vv_grid = fig.add_subplot(gs[2, 1])
    _hist2d(ax_vv_grid, vr_grid, vt_grid, bins=50,
            x_lim=v_lim, y_lim=v_lim,
            title="Couverture (vr, vθ) — Grille",
            xlabel="vr (m/s)", ylabel="vθ (m/s)", cmap="Oranges")

    plt.show()


def plot_lengths(rand_lengths: list[int], grid_lengths: list[int]) -> None:
    """Histogramme des longueurs de trajectoire."""
    fig, ax = plt.subplots(figsize=(9, 4))
    bins = np.linspace(0, max(max(rand_lengths), max(grid_lengths)), 60)
    ax.hist(rand_lengths, bins=bins, density=True, alpha=0.65,
            color="steelblue",  label=f"Aléatoire — médiane {np.median(rand_lengths):.0f} pas")
    ax.hist(grid_lengths, bins=bins, density=True, alpha=0.65,
            color="darkorange", label=f"Grille    — médiane {np.median(grid_lengths):.0f} pas")
    ax.set_title("Distribution des longueurs de trajectoire")
    ax.set_xlabel("Nombre de pas")
    ax.set_ylabel("Densité")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.show()


# ── Main ───────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-random", type=int, default=2000,
                        help="Nombre de trajectoires aléatoires (défaut : 2000)")
    parser.add_argument("--n-r",     type=int, default=15,
                        help="Grille : rayons (défaut : 15)")
    parser.add_argument("--n-theta", type=int, default=18,
                        help="Grille : angles (défaut : 18)")
    parser.add_argument("--n-v",     type=int, default=4,
                        help="Grille : vitesses (défaut : 4)")
    parser.add_argument("--n-dir",   type=int, default=8,
                        help="Grille : directions (défaut : 8)")
    args = parser.parse_args()

    cfg      = load_config("ml")
    phys_cfg = cfg["synth"]["physics"]
    gen_cfg  = cfg["synth"]["generation"]

    # ── CI aléatoires ─────────────────────────────────────────────────────────
    rng = np.random.default_rng(0)
    merged_rand = {**phys_cfg, **gen_cfg}
    r0_r, th0_r, vr0_r, vth0_r = _sample_initial_conditions(
        args.n_random, merged_rand, rng
    )

    # ── CI grille ─────────────────────────────────────────────────────────────
    grid_cfg = {
        **phys_cfg, **gen_cfg,
        "n_r": args.n_r, "n_theta": args.n_theta,
        "n_v": args.n_v, "n_dir": args.n_dir,
    }
    r0_g, th0_g, vr0_g, vth0_g = _sample_initial_conditions_grid(grid_cfg)
    n_grid_ci = len(r0_g)

    print(f"\nCI aléatoires  : {args.n_random:,}")
    print(f"CI grille      : {args.n_r} × {args.n_theta} × {args.n_v} × {args.n_dir}"
          f" = {n_grid_ci:,}")

    # ── Simulation ────────────────────────────────────────────────────────────
    print("\nSimulation mode aléatoire...")
    rand_trajs, rand_lengths = simulate_trajectories(
        r0_r, th0_r, vr0_r, vth0_r, phys_cfg, gen_cfg
    )
    print(f"  {len(rand_lengths):,} traj. valides  "
          f"({sum(rand_lengths):,} états  |  "
          f"médiane {int(np.median(rand_lengths))} pas)")

    print("Simulation mode grille...")
    grid_trajs, grid_lengths = simulate_trajectories(
        r0_g, th0_g, vr0_g, vth0_g, phys_cfg, gen_cfg
    )
    print(f"  {len(grid_lengths):,} traj. valides  "
          f"({sum(grid_lengths):,} états  |  "
          f"médiane {int(np.median(grid_lengths))} pas)")

    # ── Agrégation des états ──────────────────────────────────────────────────
    rand_states = collect_states(rand_trajs)
    grid_states = collect_states(grid_trajs)

    # ── Affichage ─────────────────────────────────────────────────────────────
    plot_comparison(
        rand_states, grid_states,
        rand_lengths, grid_lengths,
        R=phys_cfg["R"],
        n_rand_ci=args.n_random,
        n_grid_ci=n_grid_ci,
    )
    plot_lengths(rand_lengths, grid_lengths)
