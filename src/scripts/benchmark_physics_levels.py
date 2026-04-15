"""Comparaison des 4 niveaux de précision physique — cône et membrane.

Niveaux testés :
  L0 — glissement Coulomb (défaut)
  L1 — roulement pur (rolling=True, f=5/7)
  L2 — roulement + résistance (rolling_resistance=0.003)
  L3 — roulement + résistance + traînée (drag_coeff=0.05)

Conditions initiales : orbite quasi-circulaire (vr=0, vθ ≈ vθ_orb).
Cette CI maximise les différences entre niveaux : L1 orbite indéfiniment,
L2 spiral doucement, L3 spiral plus vite, L0 spiral rapidement.

Métriques tracées :
  - r(t) / R       : position radiale normalisée
  - E_kin(t) / E_0 : énergie cinétique normalisée (dissipation)
  - XY (vue de dessus)

Usage :
    python src/scripts/benchmark_physics_levels.py
    python src/scripts/benchmark_physics_levels.py --no-plot --output results/levels.csv
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


# ── Configuration des 4 niveaux ──────────────────────────────────────────────

LEVELS = [
    {
        "name": "L0 — Glissement",
        "color": "#e74c3c",
        "kwargs": {},
    },
    {
        "name": "L1 — Roulement pur",
        "color": "#3498db",
        "kwargs": {"rolling": True},
    },
    {
        "name": "L2 — + Résistance roulement",
        "color": "#2ecc71",
        "kwargs": {"rolling": True, "rolling_resistance": 0.003},
    },
    {
        "name": "L3 — + Traînée aérodynamique",
        "color": "#9b59b6",
        "kwargs": {"rolling": True, "rolling_resistance": 0.003, "drag_coeff": 0.05},
    },
]

N_STEPS = 5_000   # 50 s à dt=0.01 — couvre la durée de vie de tous les niveaux


# ── Helpers ───────────────────────────────────────────────────────────────────

def _orbital_speed_cone(r: float, g: float, depth: float, R: float) -> float:
    """Vitesse orbitale circulaire sur le cône : vθ_orb = √(g·sin(α)·r)."""
    slope = depth / R
    sin_alpha = slope / np.sqrt(1.0 + slope ** 2)
    return np.sqrt(g * sin_alpha * r)


def _orbital_speed_membrane(g: float, k: float) -> float:
    """Vitesse orbitale circulaire sur la membrane : vθ_orb = √(g·k) (constante)."""
    return np.sqrt(g * k)


def _run_level(surface: str, level: dict, phys: dict) -> np.ndarray:
    """Simule une trajectoire pour un niveau donné. Retourne array (N, 4)."""
    common = dict(
        R=phys["R"], friction=phys["friction"],
        g=phys["g"], dt=phys["dt"], n_steps=N_STEPS,
        center_radius=phys.get("center_radius", 0.03),
    )
    common.update(level["kwargs"])

    if surface == "cone":
        r0 = 0.28     # 70 % du rayon
        vtheta0 = _orbital_speed_cone(r0, phys["g"], phys["depth"], phys["R"])
        return compute_cone(
            r0=r0, theta0=0.0, vr0=0.0, vtheta0=vtheta0,
            depth=phys["depth"], **common,
        )
    else:
        r0 = 0.28
        vtheta0 = _orbital_speed_membrane(phys["g"], phys["k"])
        return compute_membrane(
            r0=r0, theta0=0.0, vr0=0.0, vtheta0=vtheta0,
            k=phys["k"], r_min=phys.get("center_radius", 0.03), **common,
        )


def _print_table(surface: str, results: list[tuple]) -> None:
    """Affiche un tableau résumé console."""
    print(f"\n{'═' * 62}")
    print(f"  Surface : {surface.upper()}")
    print(f"{'─' * 62}")
    print(f"  {'Niveau':<30} {'Durée (s)':>9} {'r_final/R':>9} {'E_fin/E_0':>9}")
    print(f"{'─' * 62}")
    for name, traj, dt, R, E0 in results:
        dur = len(traj) * dt
        r_norm = traj[-1, 0] / R
        v2 = traj[-1, 2] ** 2 + traj[-1, 3] ** 2
        e_norm = (0.5 * v2) / E0 if E0 > 0 else 0.0
        print(f"  {name:<30} {dur:>9.2f} {r_norm:>9.4f} {e_norm:>9.4f}")
    print(f"{'═' * 62}")


# ── Plotting ──────────────────────────────────────────────────────────────────

def _plot(cone_data: list, membrane_data: list, output: Path | None) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("Comparaison des niveaux de précision physique", fontsize=13)

    for row, (data, surface_label) in enumerate([
        (cone_data,     "Cône"),
        (membrane_data, "Membrane"),
    ]):
        ax_r, ax_e, ax_xy = axes[row]

        for (name, traj, dt, R, E0), level in zip(data, LEVELS):
            t = np.arange(len(traj)) * dt
            r_norm = traj[:, 0] / R
            v2 = traj[:, 2] ** 2 + traj[:, 3] ** 2
            e_norm = 0.5 * v2 / E0 if E0 > 0 else 0.5 * v2

            kw = dict(label=name, color=level["color"], linewidth=1.5)
            ax_r.plot(t, r_norm, **kw)
            ax_e.plot(t, e_norm, **kw)

            x = traj[:, 0] * np.cos(traj[:, 1])
            y = traj[:, 0] * np.sin(traj[:, 1])
            ax_xy.plot(x, y, color=level["color"], linewidth=0.8, alpha=0.85)

        # Cercle du bord
        ang = np.linspace(0, 2 * np.pi, 300)
        R_val = data[0][3]
        ax_xy.plot(R_val * np.cos(ang), R_val * np.sin(ang),
                   color="gray", linestyle="--", linewidth=0.8)
        ax_xy.set_aspect("equal")
        ax_xy.set_title(f"{surface_label} — trajectoire XY")
        ax_xy.set_xlabel("x (m)")
        ax_xy.set_ylabel("y (m)")

        ax_r.set_title(f"{surface_label} — r(t) / R")
        ax_r.set_xlabel("t (s)")
        ax_r.set_ylabel("r / R")
        ax_r.legend(fontsize=8)
        ax_r.grid(True, alpha=0.25)
        ax_r.set_ylim(0, 1.05)

        ax_e.set_title(f"{surface_label} — Énergie cinétique normalisée")
        ax_e.set_xlabel("t (s)")
        ax_e.set_ylabel("E_kin / E_0")
        ax_e.legend(fontsize=8)
        ax_e.grid(True, alpha=0.25)

    plt.tight_layout()
    if output:
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Figure sauvegardée : {output}")
    else:
        plt.show()


def _save_csv(cone_data: list, membrane_data: list, csv_path: Path) -> None:
    """Exporte les trajectoires dans un CSV large : time, r_L0, r_L1, …, E_L0, …"""
    import csv

    # Durée maximale parmi tous les niveaux
    dt = cone_data[0][2]
    n_max = max(len(t) for t, *_ in [(d[1],) for d in cone_data + membrane_data])

    headers = ["time_s"]
    for surface in ("cone", "membrane"):
        for level in LEVELS:
            tag = level["name"].split("—")[0].strip().lower().replace(" ", "_")
            headers += [f"{surface}_{tag}_r_norm", f"{surface}_{tag}_E_norm"]

    rows = []
    cone_trajs = [(d[1], d[3], d[4]) for d in cone_data]     # (traj, R, E0)
    memb_trajs = [(d[1], d[3], d[4]) for d in membrane_data]

    for i in range(n_max):
        row = [i * dt]
        for trajs in (cone_trajs, memb_trajs):
            for traj, R, E0 in trajs:
                if i < len(traj):
                    r_n = traj[i, 0] / R
                    v2  = traj[i, 2] ** 2 + traj[i, 3] ** 2
                    e_n = 0.5 * v2 / E0 if E0 > 0 else 0.0
                else:
                    r_n = e_n = float("nan")
                row += [round(r_n, 6), round(e_n, 6)]
        rows.append(row)

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"CSV sauvegardé : {csv_path}  ({len(rows)} lignes, {len(headers)} colonnes)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare les 4 niveaux de précision physique (cône + membrane)."
    )
    parser.add_argument("--output", type=Path, default=None,
                        help="Chemin de sortie : .png/.pdf pour figure, .csv pour données")
    parser.add_argument("--no-plot", action="store_true",
                        help="Mode batch — pas de fenêtre graphique")
    args = parser.parse_args()

    cone_cfg     = load_config("cone")
    membrane_cfg = load_config("membrane")

    cone_phys     = cone_cfg["physics"]
    membrane_phys = membrane_cfg["physics"]

    # IC partagée pour le cône (vθ orbitale)
    r0 = 0.28
    E0_cone = 0.5 * _orbital_speed_cone(r0, cone_phys["g"],
                                        cone_phys["depth"], cone_phys["R"]) ** 2
    E0_memb = 0.5 * _orbital_speed_membrane(membrane_phys["g"], membrane_phys["k"]) ** 2

    print("Simulation des 4 niveaux de précision physique...")
    print(f"  r0 = {r0} m   vθ_orb_cone = {_orbital_speed_cone(r0, cone_phys['g'], cone_phys['depth'], cone_phys['R']):.3f} m/s")
    print(f"  vθ_orb_membrane = {_orbital_speed_membrane(membrane_phys['g'], membrane_phys['k']):.3f} m/s")
    print(f"  N_steps max = {N_STEPS}")

    cone_data: list = []
    membrane_data: list = []
    dt = cone_phys["dt"]
    R_cone = cone_phys["R"]
    R_memb = membrane_phys["R"]

    for level in LEVELS:
        tc = _run_level("cone",     level, cone_phys)
        tm = _run_level("membrane", level, membrane_phys)
        cone_data.append((level["name"], tc, dt, R_cone, E0_cone))
        membrane_data.append((level["name"], tm, dt, R_memb, E0_memb))
        print(f"  {level['name']:<35} : cône={len(tc):>5} pas   membrane={len(tm):>5} pas")

    _print_table("cône",     cone_data)
    _print_table("membrane", membrane_data)

    if args.output and str(args.output).endswith(".csv"):
        _save_csv(cone_data, membrane_data, args.output)
    elif not args.no_plot or (args.output and not str(args.output).endswith(".csv")):
        _plot(cone_data, membrane_data, args.output if not args.no_plot else None)
        if args.output and args.no_plot:
            _plot(cone_data, membrane_data, args.output)


if __name__ == "__main__":
    main()
