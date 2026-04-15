"""Test des simulations cône et membrane.

Teste le preset par défaut avec les 4 niveaux de précision physique et
les 3 intégrateurs disponibles pour le cône.

Usage :
    python src/scripts/test_simulations.py
    python src/scripts/test_simulations.py --no-plot --output figures/sims.png
    python src/scripts/test_simulations.py --output results/sims.csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from physics.cone import compute_cone
from physics.membrane import compute_membrane
from utils.angle import v0_dir_to_vr_vtheta


# ── Helpers ───────────────────────────────────────────────────────────────────

def _stopping_reason(traj: np.ndarray, n_max: int, R: float, r_min: float) -> str:
    n = len(traj)
    r_final = float(traj[-1, 0])
    if n >= n_max:
        return "borne atteinte"
    if r_final >= R - 1e-6:
        return "sortie bord"
    if r_final <= r_min + 1e-6:
        return "collision centre"
    return "bille arrêtée"


def print_stats(name: str, traj: np.ndarray, dt: float, n_max: int,
                R: float, r_min: float) -> None:
    r      = traj[:, 0]
    vr     = traj[:, 2]
    vtheta = traj[:, 3]
    speed  = np.sqrt(vr ** 2 + vtheta ** 2)
    reason = _stopping_reason(traj, n_max, R, r_min)

    print(f"\n{'─' * 46}")
    print(f"  {name}")
    print(f"{'─' * 46}")
    print(f"  Pas  : {len(traj)} / {n_max}  ({reason})")
    print(f"  Durée: {len(traj) * dt:.2f} s")
    print(f"  r    : [{r.min():.4f}, {r.max():.4f}]  final={r[-1]:.4f} m")
    print(f"  |v|  : [{speed.min():.4f}, {speed.max():.4f}]  final={speed[-1]:.4f} m/s")
    print(f"  E_cin finale : {0.5 * speed[-1]**2:.6f} J/kg")


# ── Simulations preset par défaut ─────────────────────────────────────────────

def run_cone(cfg: dict, **extra) -> np.ndarray:
    phys   = cfg["physics"]
    preset = cfg["preset"]["default"]
    vr0, vtheta0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    return compute_cone(
        r0=preset["r0"], theta0=preset["theta0"], vr0=vr0, vtheta0=vtheta0,
        R=phys["R"], depth=phys["depth"],
        friction=phys["friction"], g=phys["g"],
        dt=phys["dt"], n_steps=phys["n_steps"],
        center_radius=phys["center_radius"],
        **extra,
    )


def run_membrane(cfg: dict, **extra) -> np.ndarray:
    phys   = cfg["physics"]
    preset = cfg["preset"]["default"]
    vr0, vtheta0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    return compute_membrane(
        r0=preset["r0"], theta0=preset["theta0"], vr0=vr0, vtheta0=vtheta0,
        R=phys["R"], k=phys["k"], r_min=phys["center_radius"],
        friction=phys["friction"], g=phys["g"],
        dt=phys["dt"], n_steps=phys["n_steps"],
        center_radius=phys["center_radius"],
        **extra,
    )


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_default(traj_cone: np.ndarray, cone_cfg: dict,
                 traj_membrane: np.ndarray, membrane_cfg: dict,
                 output: Path | None) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Simulations — preset par défaut (Level 0)", fontsize=13)

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

        ax_xy = axes[0, col]
        sc = ax_xy.scatter(x, y, c=t, cmap="plasma", s=2, linewidths=0)
        ang = np.linspace(0, 2 * np.pi, 300)
        ax_xy.plot(R * np.cos(ang), R * np.sin(ang), "gray", linestyle="--", linewidth=1)
        ax_xy.set_aspect("equal")
        ax_xy.set_title(f"{name} — trajectoire XY")
        ax_xy.set_xlabel("x (m)")
        ax_xy.set_ylabel("y (m)")
        fig.colorbar(sc, ax=ax_xy, label="t (s)")

        ax_rv = axes[1, col]
        ax_rv.plot(t, r,     label="r (m)",    color="steelblue")
        ax_rv.plot(t, speed, label="|v| (m/s)", color="tomato", linestyle="--")
        ax_rv.set_title(f"{name} — r(t) et |v|(t)")
        ax_rv.set_xlabel("t (s)")
        ax_rv.legend()
        ax_rv.grid(True, alpha=0.3)

    plt.tight_layout()
    if output:
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Figure sauvegardée : {output}")
    else:
        plt.show()
    plt.close(fig)


def plot_physics_levels(levels_data: list[tuple], surface: str,
                        output: Path | None) -> None:
    """Trace r(t) et énergie(t) pour les 4 niveaux physiques."""
    import matplotlib.pyplot as plt

    COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6"]
    fig, (ax_r, ax_e) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f"{surface.capitalize()} — niveaux de précision physique", fontsize=13)

    E0 = 0.5 * (levels_data[0][1][:, 2] ** 2 + levels_data[0][1][:, 3] ** 2).max()
    R  = levels_data[0][2]
    dt = levels_data[0][3]

    for (label, traj, R_, dt_), color in zip(levels_data, COLORS):
        t = np.arange(len(traj)) * dt_
        r_norm = traj[:, 0] / R_
        v2 = traj[:, 2] ** 2 + traj[:, 3] ** 2
        e_norm = 0.5 * v2 / E0 if E0 > 0 else 0.5 * v2
        ax_r.plot(t, r_norm, label=label, color=color, linewidth=1.5)
        ax_e.plot(t, e_norm, label=label, color=color, linewidth=1.5)

    for ax, ylabel, title in [
        (ax_r, "r / R",        "Position radiale normalisée"),
        (ax_e, "E_kin / E_max", "Énergie cinétique normalisée"),
    ]:
        ax.set_xlabel("t (s)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.25)

    plt.tight_layout()
    if output:
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Figure niveaux physiques sauvegardée : {output}")
    else:
        plt.show()
    plt.close(fig)


def plot_integrators(integrators_data: list[tuple], output: Path | None) -> None:
    """Trace les trajectoires XY pour les 3 intégrateurs (cône)."""
    import matplotlib.pyplot as plt

    COLORS = {"euler": "#e74c3c", "euler_cromer": "#3498db", "rk4": "#2ecc71"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Cône — comparaison des 3 intégrateurs (preset défaut)", fontsize=13)

    for ax, (method, traj, R, dt) in zip(axes, integrators_data):
        r, theta = traj[:, 0], traj[:, 1]
        t = np.arange(len(traj)) * dt
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        sc = ax.scatter(x, y, c=t, cmap="viridis", s=2, linewidths=0)
        ang = np.linspace(0, 2 * np.pi, 300)
        ax.plot(R * np.cos(ang), R * np.sin(ang), "gray", linestyle="--", linewidth=1)
        ax.set_aspect("equal")
        ax.set_title(method)
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        fig.colorbar(sc, ax=ax, label="t (s)")

    plt.tight_layout()
    if output:
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Figure intégrateurs sauvegardée : {output}")
    else:
        plt.show()
    plt.close(fig)


def save_csv(cone_traj: np.ndarray, membrane_traj: np.ndarray,
             cone_dt: float, membrane_dt: float, path: Path) -> None:
    import csv
    n = max(len(cone_traj), len(membrane_traj))
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step", "cone_r", "cone_theta", "cone_vr", "cone_vtheta",
                    "membrane_r", "membrane_theta", "membrane_vr", "membrane_vtheta"])
        for i in range(n):
            c = cone_traj[i].tolist()     if i < len(cone_traj)     else ["", "", "", ""]
            m = membrane_traj[i].tolist() if i < len(membrane_traj) else ["", "", "", ""]
            w.writerow([i] + c + m)
    print(f"CSV sauvegardé : {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test des simulations physiques — niveaux et intégrateurs."
    )
    parser.add_argument("--output", type=Path, default=None,
                        help="Chemin de sortie (.png pour figure, .csv pour données)")
    parser.add_argument("--no-plot", action="store_true",
                        help="Mode batch — pas de fenêtre graphique")
    args = parser.parse_args()

    cone_cfg     = load_config("cone")
    membrane_cfg = load_config("membrane")
    cone_phys    = cone_cfg["physics"]
    memb_phys    = membrane_cfg["physics"]

    # ── 1. Preset par défaut (Level 0) ────────────────────────────────────────
    print("=== Preset par défaut (Level 0 — glissement) ===")
    traj_cone     = run_cone(cone_cfg)
    traj_membrane = run_membrane(membrane_cfg)

    print_stats("CÔNE",     traj_cone,     cone_phys["dt"],
                cone_phys["n_steps"],     cone_phys["R"],  cone_phys["center_radius"])
    print_stats("MEMBRANE", traj_membrane, memb_phys["dt"],
                memb_phys["n_steps"],     memb_phys["R"],  memb_phys["center_radius"])

    if not args.no_plot:
        out_default = None
        if args.output and str(args.output).endswith(".csv"):
            pass
        elif args.output:
            out_default = args.output
        plot_default(traj_cone, cone_cfg, traj_membrane, membrane_cfg, out_default)

    # ── 2. Niveaux de précision physique (cône) ───────────────────────────────
    print("\n=== Niveaux de précision physique — cône ===")
    physics_configs = [
        ("L0 — Glissement",            {}),
        ("L1 — Roulement pur",         {"rolling": True}),
        ("L2 — + Résistance roulement", {"rolling": True, "rolling_resistance": 0.003}),
        ("L3 — + Traînée aéro",         {"rolling": True, "rolling_resistance": 0.003,
                                          "drag_coeff": 0.05}),
    ]
    levels_cone = []
    for label, extra in physics_configs:
        traj = run_cone(cone_cfg, **extra)
        reason = _stopping_reason(traj, cone_phys["n_steps"],
                                  cone_phys["R"], cone_phys["center_radius"])
        dur = len(traj) * cone_phys["dt"]
        print(f"  {label:<35} : {len(traj):>6} pas ({dur:.1f} s)  [{reason}]")
        levels_cone.append((label, traj, cone_phys["R"], cone_phys["dt"]))

    # ── 3. Niveaux de précision physique (membrane) ───────────────────────────
    print("\n=== Niveaux de précision physique — membrane ===")
    levels_memb = []
    for label, extra in physics_configs:
        traj = run_membrane(membrane_cfg, **extra)
        reason = _stopping_reason(traj, memb_phys["n_steps"],
                                  memb_phys["R"], memb_phys["center_radius"])
        dur = len(traj) * memb_phys["dt"]
        print(f"  {label:<35} : {len(traj):>6} pas ({dur:.1f} s)  [{reason}]")
        levels_memb.append((label, traj, memb_phys["R"], memb_phys["dt"]))

    # ── 4. Comparaison intégrateurs (cône) ────────────────────────────────────
    print("\n=== Intégrateurs numériques — cône (Level 0) ===")
    integrators_data = []
    for method in ("euler", "euler_cromer", "rk4"):
        traj = run_cone(cone_cfg, method=method)
        reason = _stopping_reason(traj, cone_phys["n_steps"],
                                  cone_phys["R"], cone_phys["center_radius"])
        dur = len(traj) * cone_phys["dt"]
        print(f"  {method:<15} : {len(traj):>6} pas ({dur:.1f} s)  [{reason}]"
              f"  r_final={traj[-1,0]:.4f} m")
        integrators_data.append((method, traj, cone_phys["R"], cone_phys["dt"]))

    # ── Sorties ───────────────────────────────────────────────────────────────
    if args.output and str(args.output).endswith(".csv"):
        save_csv(traj_cone, traj_membrane, cone_phys["dt"], memb_phys["dt"], args.output)
    elif not args.no_plot:
        plot_physics_levels(levels_cone, "cône",     None)
        plot_physics_levels(levels_memb, "membrane", None)
        plot_integrators(integrators_data, None)

    print("\nTerminé.")


if __name__ == "__main__":
    main()
