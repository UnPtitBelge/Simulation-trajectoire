"""Benchmark des intégrateurs numériques : Euler explicite, Euler-Cromer, RK4.

Ce script répond à la question : pourquoi choisir Euler-Cromer plutôt que
l'Euler explicite ou le RK4 pour la simulation du cône ?

Protocole :
  - Trajectoire de référence : RK4 avec dt_ref = 1e-4 s (≈ 100× plus fin que dt nominal)
  - Pour chaque dt ∈ {0.1, 0.05, 0.02, 0.01, 0.005, 0.001} et chaque intégrateur :
      1. Simuler n_steps = T_total / dt pas
      2. Ré-échantillonner la référence aux mêmes instants
      3. Calculer l'erreur RMSE sur r et la position finale

Résultats attendus :
  - Euler et Euler-Cromer : convergence d'ordre 1 (pente ≈ 1 sur graphe log-log)
  - RK4 : convergence d'ordre 4 (pente ≈ 4)
  - Euler-Cromer : meilleure constante d'erreur que l'Euler explicite (conservation énergie)

Usage :
    python src/scripts/benchmark_integrators.py
    python src/scripts/benchmark_integrators.py --output figures/integrators.png
    python src/scripts/benchmark_integrators.py --no-plot --output results/integrators.csv
"""

import argparse
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from physics.cone import compute_cone


# ── Paramètres du benchmark ─────────────────────────────────────────────────────

# Conditions initiales reproductibles (choisies pour avoir une trajectoire
# suffisamment longue — la bille doit rester dans le cône sur toute la durée T_total)
IC = {
    "r0":      0.30,    # m — départ à 75 % du rayon
    "theta0":  0.0,
    "vr0":     0.0,
    "vtheta0": 0.8,     # m/s — vitesse tangentielle, orbite proche-circulaire
}

DT_VALUES   = [0.10, 0.05, 0.02, 0.010, 0.005, 0.002, 0.001]  # s
DT_REF      = 1e-4     # s — référence "exacte"
T_TOTAL     = 2.0      # s — durée de comparaison
METHODS     = ["euler", "euler_cromer", "rk4"]
COLORS      = {"euler": "tomato", "euler_cromer": "steelblue", "rk4": "seagreen"}
LABELS      = {"euler": "Euler explicite", "euler_cromer": "Euler-Cromer (semi-impl.)", "rk4": "RK4"}


# ── Calcul de référence et d'erreur ─────────────────────────────────────────────


def run_reference(phys: dict, synth: dict) -> np.ndarray:
    """Calcule la trajectoire de référence (RK4, dt_ref très petit)."""
    n_ref = int(T_TOTAL / DT_REF) + 1
    traj = compute_cone(
        **IC,
        R=phys["R"], depth=synth["depth"],
        friction=phys["friction"], g=phys["g"],
        dt=DT_REF, n_steps=n_ref,
        center_radius=phys["center_radius"],
        method="rk4",
    )
    return traj  # (N_ref, 4)


def compute_errors(
    phys: dict, synth: dict,
    ref_traj: np.ndarray,
) -> dict:
    """Pour chaque (method, dt), calcule RMSE(r) et temps CPU."""
    results: dict[str, list] = {m: [] for m in METHODS}
    t_ref = np.arange(len(ref_traj)) * DT_REF  # axe temps de la référence

    for dt in DT_VALUES:
        n_steps = int(T_TOTAL / dt) + 1
        for method in METHODS:
            t0 = time.perf_counter()
            traj = compute_cone(
                **IC,
                R=phys["R"], depth=synth["depth"],
                friction=phys["friction"], g=phys["g"],
                dt=dt, n_steps=n_steps,
                center_radius=phys["center_radius"],
                method=method,
            )
            cpu_s = time.perf_counter() - t0

            # Instants simulés (peut s'arrêter avant T_TOTAL)
            t_sim = np.arange(len(traj)) * dt

            if len(traj) < 2:
                # Bille sortie du cône dès le premier pas (dt trop grand)
                results[method].append({"dt": dt, "rmse_r": np.nan, "err_final": np.nan, "cpu_ms": cpu_s * 1000})
                continue

            # Ré-échantillonne la référence aux mêmes instants que la simulation
            t_cmp = t_sim[t_sim <= t_ref[-1]]
            if len(t_cmp) == 0:
                results[method].append({"dt": dt, "rmse_r": np.nan, "err_final": np.nan, "cpu_ms": cpu_s * 1000})
                continue

            r_ref_interp = np.interp(t_cmp, t_ref, ref_traj[:, 0])
            r_sim        = traj[:len(t_cmp), 0]

            rmse_r    = float(np.sqrt(np.mean((r_sim - r_ref_interp) ** 2)))
            err_final = float(abs(r_sim[-1] - r_ref_interp[-1]))

            results[method].append({
                "dt": dt, "rmse_r": rmse_r, "err_final": err_final, "cpu_ms": cpu_s * 1000,
            })
            print(f"  {method:<14}  dt={dt:.3f}  RMSE(r)={rmse_r:.2e} m  "
                  f"err_final={err_final:.2e} m  CPU={cpu_s*1000:.1f} ms")

    return results


# ── Visualisation ────────────────────────────────────────────────────────────────


def plot_convergence(results: dict, output: Path | None) -> None:
    """Graphe de convergence log-log (erreur finale vs dt) + courbes de trajectoire."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        "Convergence des intégrateurs numériques — simulation du cône\n"
        f"CI : r₀={IC['r0']} m, vθ₀={IC['vtheta0']} m/s  |  T={T_TOTAL} s  |  "
        f"référence : RK4 dt={DT_REF:.0e} s",
        fontsize=11,
    )

    ax_conv, ax_ord = axes

    # ── Panel gauche : erreur finale vs dt ───────────────────────────────────
    for method in METHODS:
        pts = [(r["dt"], r["err_final"]) for r in results[method] if not np.isnan(r["err_final"])]
        if not pts:
            continue
        dts, errs = zip(*pts)
        ax_conv.loglog(dts, errs, "o-",
                       color=COLORS[method], label=LABELS[method], linewidth=2, markersize=6)

    # Droites de référence pour les ordres 1 et 4
    dt_range = np.array([min(DT_VALUES) * 0.8, max(DT_VALUES) * 1.2])
    ax_conv.loglog(dt_range, 0.05  * dt_range ** 1, "k--", linewidth=1, alpha=0.5, label="ordre 1")
    ax_conv.loglog(dt_range, 0.001 * dt_range ** 4, "k:",  linewidth=1, alpha=0.5, label="ordre 4")

    ax_conv.set_xlabel("dt (s)")
    ax_conv.set_ylabel("Erreur finale |r_sim − r_ref| (m)")
    ax_conv.set_title("Convergence en dt (graphe log-log)")
    ax_conv.legend(fontsize=9)
    ax_conv.grid(True, which="both", alpha=0.3)

    # ── Panel droit : RMSE(r) vs dt ──────────────────────────────────────────
    for method in METHODS:
        pts = [(r["dt"], r["rmse_r"]) for r in results[method] if not np.isnan(r["rmse_r"])]
        if not pts:
            continue
        dts, rmses = zip(*pts)
        ax_ord.loglog(dts, rmses, "s--",
                      color=COLORS[method], label=LABELS[method], linewidth=1.5, markersize=5)

    ax_ord.set_xlabel("dt (s)")
    ax_ord.set_ylabel("RMSE(r) sur toute la trajectoire (m)")
    ax_ord.set_title("RMSE(r) vs dt")
    ax_ord.legend(fontsize=9)
    ax_ord.grid(True, which="both", alpha=0.3)

    plt.tight_layout()

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"\nFigure sauvegardée : {output}")

    plt.show()


def print_table(results: dict) -> None:
    """Affiche un tableau récapitulatif erreur + CPU pour le rapport."""
    header = f"{'dt':>7}  " + "  ".join(f"{LABELS[m]:>30}" for m in METHODS)
    print("\n" + "═" * len(header))
    print("RMSE(r) en mètres")
    print(header)
    print("─" * len(header))
    for idx, dt in enumerate(DT_VALUES):
        row = f"{dt:>7.4f}  "
        for method in METHODS:
            v = results[method][idx]["rmse_r"]
            row += f"  {v:>28.2e}  " if not np.isnan(v) else f"  {'—':>28}  "
        print(row)
    print("─" * len(header))

    print("\nTemps CPU par trajectoire (ms)")
    print(header)
    print("─" * len(header))
    for idx, dt in enumerate(DT_VALUES):
        row = f"{dt:>7.4f}  "
        for method in METHODS:
            v = results[method][idx]["cpu_ms"]
            row += f"  {v:>28.2f}  " if not np.isnan(v) else f"  {'—':>28}  "
        print(row)
    print("═" * len(header) + "\n")


def save_csv(results: dict, csv_path: Path) -> None:
    """Exporte les résultats en CSV pour les tableaux du rapport."""
    import csv
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "dt", "rmse_r_m", "err_final_m", "cpu_ms"])
        for method in METHODS:
            for r in results[method]:
                w.writerow([method, r["dt"], r["rmse_r"], r["err_final"], r["cpu_ms"]])
    print(f"CSV sauvegardé : {csv_path}")


# ── Main ─────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark de convergence des intégrateurs numériques."
    )
    parser.add_argument("--output",  type=str, default=None,
                        help="Chemin de sauvegarde de la figure (.png) ou des données (.csv)")
    parser.add_argument("--no-plot", action="store_true",
                        help="Ne pas afficher la figure (utile en mode batch)")
    args = parser.parse_args()

    cfg     = load_config("ml")
    phys    = cfg["physics"]
    synth   = cfg["synth"]["physics"]

    print(f"\nCalcul de la trajectoire de référence (RK4, dt={DT_REF:.0e} s)...")
    ref_traj = run_reference(phys, synth)
    print(f"  → {len(ref_traj)} pas ({len(ref_traj) * DT_REF:.1f} s)")

    print(f"\nBenchmark ({len(DT_VALUES)} valeurs de dt × {len(METHODS)} méthodes) :")
    results = compute_errors(phys, synth, ref_traj)

    print_table(results)

    output_path = Path(args.output) if args.output else None

    if output_path is not None and output_path.suffix == ".csv":
        save_csv(results, output_path)
    elif not args.no_plot or output_path is not None:
        plot_convergence(results, output_path if (output_path and output_path.suffix in (".png", ".pdf")) else None)
        if args.no_plot:
            plt.close("all")
