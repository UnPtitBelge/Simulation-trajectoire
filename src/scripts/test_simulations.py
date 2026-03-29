"""Test des simulations cône et membrane avec le preset par défaut.

Usage :
    python src/scripts/test_simulations.py
"""

import concurrent.futures as cf
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from physics.cone import compute_cone
from physics.membrane import compute_membrane
from utils.angle import v0_dir_to_vr_vtheta


def print_stats(name: str, traj: np.ndarray, dt: float, n_max: int,
                R: float, r_min: float) -> None:
    r      = traj[:, 0]
    vr     = traj[:, 2]
    vtheta = traj[:, 3]
    speed  = np.sqrt(vr ** 2 + vtheta ** 2)

    n_used  = len(traj)
    r_final = float(r[-1])
    if n_used >= n_max:
        early = " (borne atteinte)"
    elif r_final >= R - 1e-6:
        early = " (sortie bord)"
    elif r_final <= r_min + 1e-6:
        early = " (collision centre)"
    else:
        early = " (bille arrêtée)"

    print(f"\n{'─' * 40}")
    print(f"  {name}")
    print(f"{'─' * 40}")
    print(f"  Pas utilisés    : {n_used} / {n_max}{early}")
    print(f"  Durée simulée   : {n_used * dt:.2f} s")
    print(f"  r  : min={r.min():.4f} m   max={r.max():.4f} m   final={r[-1]:.4f} m")
    print(f"  vr : min={vr.min():.4f}    max={vr.max():.4f}    final={vr[-1]:.4f} m/s")
    print(f"  vθ : min={vtheta.min():.4f}    max={vtheta.max():.4f}    final={vtheta[-1]:.4f} m/s")
    print(f"  |v|: min={speed.min():.4f}    max={speed.max():.4f}    final={speed[-1]:.4f} m/s")
    print(f"  Énergie cinétique finale : {0.5 * speed[-1]**2:.6f} J/kg")


def run_cone(cfg: dict) -> np.ndarray:
    phys   = cfg["physics"]
    preset = cfg["preset"]["default"]
    vr0, vtheta0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    return compute_cone(
        r0=preset["r0"], theta0=preset["theta0"], vr0=vr0, vtheta0=vtheta0,
        R=phys["R"], depth=phys["depth"],
        friction=phys["friction"], g=phys["g"],
        dt=phys["dt"], n_steps=phys["n_steps"],
        ball_radius=phys["ball_radius"], ball_mass=phys["ball_mass"],
        center_radius=phys["center_radius"],
    )


def run_membrane(cfg: dict) -> np.ndarray:
    phys   = cfg["physics"]
    preset = cfg["preset"]["default"]
    vr0, vtheta0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    return compute_membrane(
        r0=preset["r0"], theta0=preset["theta0"], vr0=vr0, vtheta0=vtheta0,
        R=phys["R"], k=phys["k"], r_min=phys["center_radius"],
        friction=phys["friction"], g=phys["g"],
        dt=phys["dt"], n_steps=phys["n_steps"],
        ball_radius=phys["ball_radius"], ball_mass=phys["ball_mass"],
        center_radius=phys["center_radius"],
    )


def plot_trajectories(
    traj_cone: np.ndarray, cone_cfg: dict,
    traj_membrane: np.ndarray, membrane_cfg: dict,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Simulations — preset par défaut", fontsize=13)

    for col, (traj, cfg, name) in enumerate([
        (traj_cone,     cone_cfg,     "Cône"),
        (traj_membrane, membrane_cfg, "Membrane"),
    ]):
        dt    = cfg["physics"]["dt"]
        R     = cfg["physics"]["R"]
        t     = np.arange(len(traj)) * dt
        r     = traj[:, 0]
        theta = traj[:, 1]
        speed = np.sqrt(traj[:, 2] ** 2 + traj[:, 3] ** 2)

        x = r * np.cos(theta)
        y = r * np.sin(theta)

        # ── Vue de dessus (trajectoire XY) ──────────────────────────────────
        ax_xy = axes[0, col]
        sc = ax_xy.scatter(x, y, c=t, cmap="plasma", s=2, linewidths=0)
        ang = np.linspace(0, 2 * np.pi, 300)
        ax_xy.plot(R * np.cos(ang), R * np.sin(ang), color="gray", linestyle="--", linewidth=1)
        ax_xy.set_aspect("equal")
        ax_xy.set_title(f"{name} — trajectoire (vue de dessus)")
        ax_xy.set_xlabel("x (m)")
        ax_xy.set_ylabel("y (m)")
        fig.colorbar(sc, ax=ax_xy, label="t (s)")

        # ── r(t) et |v|(t) ───────────────────────────────────────────────────
        ax_rv = axes[1, col]
        ax_rv.plot(t, r,     label="r (m)",    color="steelblue")
        ax_rv.plot(t, speed, label="|v| (m/s)", color="tomato", linestyle="--")
        ax_rv.set_title(f"{name} — r(t) et |v|(t)")
        ax_rv.set_xlabel("t (s)")
        ax_rv.legend()
        ax_rv.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    cone_cfg     = load_config("cone")
    membrane_cfg = load_config("membrane")

    with cf.ProcessPoolExecutor(max_workers=2) as pool:
        f_cone     = pool.submit(run_cone,     cone_cfg)
        f_membrane = pool.submit(run_membrane, membrane_cfg)
        traj_cone     = f_cone.result()
        traj_membrane = f_membrane.result()

    print_stats("CÔNE",     traj_cone,     cone_cfg["physics"]["dt"],
                cone_cfg["physics"]["n_steps"],
                R=cone_cfg["physics"]["R"],
                r_min=cone_cfg["physics"]["center_radius"])
    print_stats("MEMBRANE", traj_membrane, membrane_cfg["physics"]["dt"],
                membrane_cfg["physics"]["n_steps"],
                R=membrane_cfg["physics"]["R"],
                r_min=membrane_cfg["physics"]["center_radius"])
    print()

    plot_trajectories(traj_cone, cone_cfg, traj_membrane, membrane_cfg)
