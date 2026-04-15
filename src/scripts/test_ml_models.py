"""Test des modèles ML (linéaire et MLP) sur tous les contextes d'entraînement.

Charge et évalue deux familles de modèles :
  - Step-by-step : synth_{linear,mlp}_{ctx}.pkl — prédiction récursive pas-à-pas
  - Directs CI→traj : direct_{linear,mlp}_{ctx}.pkl — prédiction en une inférence

Produit deux figures 2×2 (une par famille), avec la même structure :
  col 0 = linéaire  |  col 1 = MLP
  row 0 = trajectoire XY (vue de dessus)
  row 1 = r(t) et |v|(t)

Usage :
    python src/scripts/test_ml_models.py
"""

import concurrent.futures as cf
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.direct_models import DirectModelBase
from ml.models import LinearStepModel, MLPStepModel
from ml.predict import predict_trajectory
from utils.angle import v0_dir_to_vr_vtheta


ALGOS       = ["linear", "mlp"]
ALGO_LABELS = {"linear": "Régression linéaire", "mlp": "MLP"}

_PALETTE = ["steelblue", "darkorange", "seagreen", "crimson", "mediumpurple"]


# ── Modèles step-by-step ──────────────────────────────────────────────────────


def _load_predict_step(args: tuple) -> tuple[tuple[str, str], "np.ndarray | None"]:
    """Worker : charge un modèle step et prédit une trajectoire."""
    models_dir, algo, context, init_state, n_steps, r_max, r_min, v_stop = args
    model = _load_step_model(models_dir, algo, context)
    if model is None:
        return (algo, context), None
    traj = predict_trajectory(model, init_state, n_steps, r_max=r_max, r_min=r_min, v_stop=v_stop)
    return (algo, context), traj


def _load_step_model(models_dir: Path, algo: str, context: str):
    """Charge un modèle step-by-step pré-entraîné. Retourne None si absent."""
    path = models_dir / f"synth_{algo}_{context}.pkl"
    if not path.exists():
        return None
    if algo == "linear":
        return LinearStepModel.load(path)
    return MLPStepModel.load(path)


# ── Modèles directs ────────────────────────────────────────────────────────────


def _load_direct_model(models_dir: Path, algo: str, context: str) -> DirectModelBase | None:
    """Charge un modèle direct (DirectModelBase). Retourne None si absent."""
    path = models_dir / f"direct_{algo}_{context}.pkl"
    if not path.exists():
        return None
    return DirectModelBase.load(path)


# ── Statistiques console ───────────────────────────────────────────────────────


def print_stats(
    paradigm: str, algo: str, context: str,
    traj: np.ndarray, dt: float, R: float,
    target_len: int | None = None,
) -> None:
    r      = traj[:, 0]
    vr     = traj[:, 2]
    vtheta = traj[:, 3]
    speed  = np.sqrt(vr**2 + vtheta**2)
    n_used = len(traj)

    if paradigm == "direct":
        stop_reason = f"(output fixe, target_len={target_len})"
    elif r[-1] >= R - 1e-6:
        stop_reason = "(sortie bord)"
    else:
        stop_reason = "(bille arrêtée)"

    print(f"\n{'─' * 52}")
    print(f"  [{paradigm}] {ALGO_LABELS[algo]:28s}  [{context}]")
    print(f"{'─' * 52}")
    print(f"  Pas       : {n_used} {stop_reason}")
    print(f"  Durée     : {n_used * dt:.2f} s")
    print(f"  r  : min={r.min():.4f} m   max={r.max():.4f} m   final={r[-1]:.4f} m")
    print(f"  vr : min={vr.min():.4f}    max={vr.max():.4f}    final={vr[-1]:.4f} m/s")
    print(f"  vθ : min={vtheta.min():.4f}    max={vtheta.max():.4f}    final={vtheta[-1]:.4f} m/s")
    print(f"  |v|: final={speed[-1]:.4f} m/s   Ec finale={0.5 * speed[-1]**2:.6f} J/kg")


# ── Visualisation ──────────────────────────────────────────────────────────────


def plot_results(
    trajs: dict,               # {(algo, context): np.ndarray}
    R: float,
    dt: float,
    preset_name: str,
    contexts: list[str],
    context_colors: dict[str, str],
    title_prefix: str = "Modèles step-by-step",
) -> None:
    """Figure 2×2 : col = algo (linear|mlp), row = (XY | r+v).

    Chaque subplot superpose tous les contextes disponibles.
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 10), constrained_layout=True)
    fig.suptitle(
        f"{title_prefix} — preset « {preset_name} »   (R = {R} m,  dt = {dt} s)",
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

            ax_xy.plot(x, y, color=color, linewidth=1.5, label=context)
            ax_xy.plot(x[0],  y[0],  "o", color=color, markersize=6)
            ax_xy.plot(x[-1], y[-1], "x", color=color, markersize=8, markeredgewidth=2)

            ax_rv.plot(t, r,     color=color, linewidth=1.5, label=f"r — {context}")
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

    plt.show()


# ── Main ───────────────────────────────────────────────────────────────────────


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

    r_min  = phys["center_radius"]
    v_stop = phys["v_stop"]

    # ── 1. Modèles step-by-step (prédiction en parallèle) ────────────────────
    print("\n═══ Modèles step-by-step ════════════════════════════════")
    trajs_step: dict = {}
    missing_step: list[str] = []

    combos = [
        (models_dir, algo, context, init_state, n_steps, R, r_min, v_stop)
        for algo in ALGOS
        for context in CONTEXTS
    ]
    with cf.ProcessPoolExecutor() as pool:
        for (algo, context), traj in pool.map(_load_predict_step, combos):
            if traj is None:
                missing_step.append(f"synth_{algo}_{context}.pkl")
            else:
                trajs_step[(algo, context)] = traj
                print_stats("step", algo, context, traj, dt, R)

    if missing_step:
        print(f"\n⚠  Modèles step-by-step introuvables :")
        for name in missing_step:
            print(f"     {name}")
        print("   Lancez d'abord : python src/scripts/train_models.py")

    # ── 2. Modèles directs (chargés séquentiellement — léger) ────────────────
    print("\n═══ Modèles directs CI→trajectoire ══════════════════════")
    trajs_direct: dict = {}
    missing_direct: list[str] = []

    for algo in ALGOS:
        for context in CONTEXTS:
            model = _load_direct_model(models_dir, algo, context)
            if model is None:
                missing_direct.append(f"direct_{algo}_{context}.pkl")
                continue
            traj = model.predict(init_state)
            trajs_direct[(algo, context)] = traj
            print_stats("direct", algo, context, traj, dt, R,
                        target_len=model.target_len)

    if missing_direct:
        print(f"\n⚠  Modèles directs introuvables :")
        for name in missing_direct:
            print(f"     {name}")
        print("   Lancez d'abord : python src/scripts/train_direct_models.py")

    # ── Visualisation ─────────────────────────────────────────────────────────
    if trajs_step:
        print()
        plot_results(
            trajs_step, R, dt, "default", CONTEXTS, CONTEXT_COLORS,
            title_prefix="Modèles step-by-step (synth_*)",
        )

    if trajs_direct:
        print()
        plot_results(
            trajs_direct, R, dt, "default", CONTEXTS, CONTEXT_COLORS,
            title_prefix="Modèles directs CI→trajectoire (direct_*)",
        )
