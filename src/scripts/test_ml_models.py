"""Test des modèles ML (linéaire et MLP) sur tous les contextes d'entraînement.

Usage :
    python src/scripts/test_ml_models.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, MLPStepModel
from ml.predict import predict_trajectory
from utils.angle import v0_dir_to_vr_vtheta


ALGOS       = ["linear", "mlp"]
ALGO_LABELS = {"linear": "Régression linéaire", "mlp": "MLP"}

# Palette construite dynamiquement depuis la config pour éviter un KeyError
# si un nouveau contexte est ajouté dans ml.toml.
_PALETTE = ["steelblue", "darkorange", "seagreen", "crimson", "mediumpurple"]


def load_model(models_dir: Path, algo: str, context: str):
    """Charge un modèle pré-entraîné. Retourne None si le fichier est absent."""
    path = models_dir / f"synth_{algo}_{context}.pkl"
    if not path.exists():
        return None
    if algo == "linear":
        return LinearStepModel.load(path)
    return MLPStepModel.load(path)


def print_stats(
    algo: str, context: str, traj: np.ndarray, dt: float, n_max: int, R: float
) -> None:
    r      = traj[:, 0]
    vr     = traj[:, 2]
    vtheta = traj[:, 3]
    speed  = np.sqrt(vr**2 + vtheta**2)

    n_used = len(traj)
    if n_used >= n_max:
        early = " (borne atteinte)"
    elif r[-1] >= R - 1e-6:
        early = " (sortie bord)"
    else:
        early = " (bille arrêtée)"   # |v| < seuil

    print(f"\n{'─' * 48}")
    print(f"  {ALGO_LABELS[algo]:28s}  [{context}]")
    print(f"{'─' * 48}")
    print(f"  Pas utilisés    : {n_used} / {n_max}{early}")
    print(f"  Durée simulée   : {n_used * dt:.2f} s")
    print(f"  r  : min={r.min():.4f} m   max={r.max():.4f} m   final={r[-1]:.4f} m")
    print(f"  vr : min={vr.min():.4f}    max={vr.max():.4f}    final={vr[-1]:.4f} m/s")
    print(f"  vθ : min={vtheta.min():.4f}    max={vtheta.max():.4f}    final={vtheta[-1]:.4f} m/s")
    print(f"  |v|: min={speed.min():.4f}    max={speed.max():.4f}    final={speed[-1]:.4f} m/s")
    print(f"  Énergie cinétique finale : {0.5 * speed[-1]**2:.6f} J/kg")


def plot_results(
    trajs: dict,           # {(algo, context): np.ndarray}
    R: float,
    dt: float,
    preset_name: str,
    contexts: list[str],
    context_colors: dict[str, str],
) -> None:
    """
    Figure 2×2 :
      col 0 = linéaire  |  col 1 = MLP
      row 0 = XY (vue dessus)  |  row 1 = r(t) et |v|(t)
    Chaque subplot superpose les 3 contextes.
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle(
        f"Modèles ML — preset « {preset_name} »   (R = {R} m,  dt = {dt} s)",
        fontsize=13,
    )

    for col, algo in enumerate(ALGOS):
        ax_xy = axes[0, col]
        ax_rv = axes[1, col]

        # Cercle de bord
        ang = np.linspace(0, 2 * np.pi, 300)
        ax_xy.plot(
            R * np.cos(ang), R * np.sin(ang),
            color="gray", linestyle="--", linewidth=1,
        )

        for context in contexts:
            traj = trajs.get((algo, context))
            if traj is None:
                continue

            color = context_colors[context]
            t     = np.arange(len(traj)) * dt
            r     = traj[:, 0]
            theta = traj[:, 1]
            speed = np.sqrt(traj[:, 2]**2 + traj[:, 3]**2)
            x     = r * np.cos(theta)
            y     = r * np.sin(theta)

            # ── Vue de dessus ────────────────────────────────────────────────
            ax_xy.plot(x, y, color=color, linewidth=1.5, label=context)
            ax_xy.plot(x[0],  y[0],  "o", color=color, markersize=6)   # départ
            ax_xy.plot(x[-1], y[-1], "x", color=color, markersize=8, markeredgewidth=2)  # arrivée

            # ── r(t) et |v|(t) ───────────────────────────────────────────────
            ax_rv.plot(t, r,     color=color, linewidth=1.5,
                       label=f"r — {context}")
            ax_rv.plot(t, speed, color=color, linewidth=1.0, linestyle="--",
                       label=f"|v| — {context}")

        ax_xy.set_aspect("equal")
        ax_xy.set_title(f"{ALGO_LABELS[algo]} — trajectoire (vue de dessus)")
        ax_xy.set_xlabel("x (m)")
        ax_xy.set_ylabel("y (m)")
        ax_xy.legend(fontsize=9)
        ax_xy.grid(True, alpha=0.25)

        ax_rv.set_title(f"{ALGO_LABELS[algo]} — r(t) et |v|(t)")
        ax_rv.set_xlabel("t (s)")
        ax_rv.set_ylabel("m  /  m·s⁻¹")
        ax_rv.legend(fontsize=8, ncol=2)
        ax_rv.grid(True, alpha=0.25)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    cfg        = load_config("ml")
    phys       = {**cfg["physics"], **cfg["synth"]["physics"]}
    dt         = phys["dt"]
    n_steps    = cfg["display"]["n_steps_pred"]
    R          = cfg["physics"]["R"]
    models_dir = ROOT / cfg["paths"]["models_dir"]
    preset     = cfg["preset"]["default"]

    CONTEXTS       = cfg["synth"]["contexts"]["names"]
    CONTEXT_COLORS = {name: _PALETTE[i % len(_PALETTE)] for i, name in enumerate(CONTEXTS)}

    vr0, vtheta0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    init_state = np.array([preset["r0"], preset["theta0"], vr0, vtheta0])

    print(f"\nConditions initiales : r0={preset['r0']} m  θ0={preset['theta0']} rad"
          f"  v0={preset['v0']} m/s  dir={preset['direction_deg']}°"
          f"  → vr0={vr0:.4f} m/s  vθ0={vtheta0:.4f} m/s")

    trajs: dict = {}
    missing: list[str] = []

    r_min  = phys["center_radius"]
    v_stop = phys["v_stop"]

    for algo in ALGOS:
        for context in CONTEXTS:
            model = load_model(models_dir, algo, context)
            if model is None:
                missing.append(f"synth_{algo}_{context}.pkl")
                continue
            traj = predict_trajectory(model, init_state, n_steps, r_max=R, r_min=r_min, v_stop=v_stop)
            trajs[(algo, context)] = traj
            print_stats(algo, context, traj, dt, n_steps, R)

    if missing:
        print(f"\n⚠  Modèles introuvables dans {models_dir} :")
        for name in missing:
            print(f"     {name}")
        print("   Lancez d'abord : python src/scripts/train_models.py")

    if trajs:
        print()
        plot_results(trajs, R, dt, "default", CONTEXTS, CONTEXT_COLORS)
