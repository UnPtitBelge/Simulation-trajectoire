"""Test du cycle complet entraînement → prédiction sur données de tracking réel.

Les données sont gardées en unités pixels/unité-temps (pas de conversion en
mètres) : toutes les expériences sont enregistrées de la même façon, le modèle
s'entraîne directement dans cet espace cohérent.

Sélectionne une expérience comme jeu de test (défaut : dernière),
entraîne sur les autres, compare la prédiction à la trajectoire réelle.

Usage :
    python src/scripts/test_real_training.py
    python src/scripts/test_real_training.py --test-id 9
    python src/scripts/test_real_training.py --passes 5
"""

import argparse
import concurrent.futures as cf
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config

from ml.models import LinearStepModel, MLPStepModel, state_to_features
from ml.predict import predict_trajectory
from ml.train import compute_exp_centers

warnings.filterwarnings("ignore")


# ── Chargement ─────────────────────────────────────────────────────────────────


def load_experiments(csv_path: Path, tracking_cfg: dict) -> dict[int, np.ndarray]:
    """Charge toutes les expériences en pixels centrés avec correction d'offset caméra.

    Utilise compute_exp_centers pour estimer le centre propre à chaque expérience
    (la bille finit toujours au même endroit physique, mais la caméra peut être décalée).

    Retourne {expID: states} où states est (N, 4) = (r_px, θ, vr_px, vθ_px).
    """
    df = pd.read_csv(csv_path, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()

    centers = compute_exp_centers(df, tracking_cfg)

    r_min_px = tracking_cfg.get("center_radius", 0.03) * tracking_cfg.get("px_per_meter", 1350.0)

    experiments: dict[int, np.ndarray] = {}
    for exp_id, group in df.groupby("expID"):
        group = group.sort_values("temps")
        cx, cy = centers[exp_id]
        xc = group["x"].values     - cx
        yc = group["y"].values     - cy
        vx = group["speedX"].values
        vy = group["speedY"].values

        r      = np.sqrt(xc**2 + yc**2)
        theta  = np.arctan2(yc, xc)
        vr     = (xc * vx + yc * vy) / np.maximum(r, r_min_px)
        vtheta = (xc * vy - yc * vx) / np.maximum(r, r_min_px)

        states = np.column_stack([r, theta, vr, vtheta]).astype(np.float32)
        experiments[int(exp_id)] = states

    return experiments


def get_timestamps(csv_path: Path, exp_id: int) -> np.ndarray:
    """Timestamps de l'expérience, normalisés à 0."""
    df = pd.read_csv(csv_path, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()
    group = df[df["expID"] == exp_id].sort_values("temps")
    t = group["temps"].values.astype(float)
    return t - t[0]


# ── Entraînement ───────────────────────────────────────────────────────────────


def train_on_experiments(
    experiments: dict[int, np.ndarray],
    test_id: int,
    n_passes: int,
) -> tuple[LinearStepModel, MLPStepModel]:
    """Entraîne LR et MLP sur toutes les expériences sauf test_id.

    - Scalers calibrés en pré-passe sur toutes les expériences d'entraînement.
    - LR : 1 seule passe (équations normales exactes, répétitions inutiles).
    - MLP : n_passes passes avec shuffle des expériences à chaque pass.
    """
    train_ids = sorted(k for k in experiments if k != test_id)
    print(f"  Expériences d'entraînement : {train_ids}")

    # Pré-passe : calibrer les scalers sur l'ensemble des données d'entraînement
    print("  Pré-passe : calibration des scalers...")
    X_parts, res_parts = [], []
    for exp_id in train_ids:
        states = experiments[exp_id]
        if len(states) < 2:
            continue
        X = state_to_features(states[:-1])
        y = state_to_features(states[1:])
        X_parts.append(X)
        res_parts.append(y - X)

    X_all    = np.vstack(X_parts)
    res_all  = np.vstack(res_parts)
    scaler_X = StandardScaler().fit(X_all)
    scaler_y = StandardScaler().fit(res_all)

    lr_model  = LinearStepModel()
    mlp_model = MLPStepModel()
    lr_model.inject_scalers(scaler_X, scaler_y)
    mlp_model.inject_scalers(scaler_X, scaler_y)

    # LR : 1 passe (équations normales — répéter biaise la régularisation Ridge)
    print("  LR — 1 passe (solution exacte)...")
    for exp_id in train_ids:
        states = experiments[exp_id]
        if len(states) < 2:
            continue
        X = state_to_features(states[:-1])
        y = state_to_features(states[1:])
        lr_model.partial_fit(X, y)

    # MLP : n_passes passes avec shuffle
    rng = np.random.default_rng(0)
    for pass_idx in range(n_passes):
        order = rng.permutation(train_ids).tolist()
        print(f"  MLP — pass {pass_idx + 1}/{n_passes} (expériences shufflées)...")
        for exp_id in order:
            states = experiments[int(exp_id)]
            if len(states) < 2:
                continue
            X = state_to_features(states[:-1])
            y = state_to_features(states[1:])
            mlp_model.partial_fit(X, y)

    return lr_model, mlp_model


# ── Métriques ──────────────────────────────────────────────────────────────────


def trajectory_errors(pred: np.ndarray, true: np.ndarray) -> dict:
    n    = min(len(pred), len(true))
    diff = np.abs(pred[:n] - true[:n])
    coverage = n / len(true) * 100
    return {
        "n_pred": len(pred), "n_true": len(true), "coverage_pct": coverage,
        "mae_r":      float(diff[:, 0].mean()),
        "mae_theta":  float(diff[:, 1].mean()),
        "mae_vr":     float(diff[:, 2].mean()),
        "mae_vtheta": float(diff[:, 3].mean()),
        "mae_total":  float(diff.mean()),
    }


def print_errors(label: str, errs: dict) -> None:
    print(f"\n  {label}")
    print(f"    Pas prédits / vrais : {errs['n_pred']} / {errs['n_true']}"
          f"  ({errs['coverage_pct']:.0f}% couverture)")
    print(f"    MAE r      : {errs['mae_r']:.3f} px")
    print(f"    MAE θ      : {errs['mae_theta']:.5f} rad")
    print(f"    MAE vr     : {errs['mae_vr']:.3f} px/t")
    print(f"    MAE vθ     : {errs['mae_vtheta']:.3f} px/t")
    print(f"    MAE global : {errs['mae_total']:.3f}")


# ── Visualisation ──────────────────────────────────────────────────────────────


def plot_comparison(
    true_states: np.ndarray,
    lr_traj:     np.ndarray,
    mlp_traj:    np.ndarray,
    timestamps:  np.ndarray,
    R_px:        float,
    test_id:     int,
    n_train:     int,
) -> None:
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"Test tracking réel — expID {test_id} (test) / {n_train} expériences (entraînement)\n"
        "Vert = tracking réel  |  Bleu = Linéaire  |  Orange = MLP",
        fontsize=12,
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)
    ax_xy  = fig.add_subplot(gs[0, 0])
    ax_r   = fig.add_subplot(gs[0, 1])
    ax_v   = fig.add_subplot(gs[1, 0])
    ax_err = fig.add_subplot(gs[1, 1])

    t_s = timestamps / 1000.0  # ms → s  # noqa: E501

    # Cercle de bord (en pixels)
    ang = np.linspace(0, 2 * np.pi, 300)
    ax_xy.plot(R_px * np.cos(ang), R_px * np.sin(ang),
               color="gray", linestyle="--", linewidth=1, label=f"bord R={R_px:.0f} px")

    def to_xy(traj):
        return traj[:, 0] * np.cos(traj[:, 1]), traj[:, 0] * np.sin(traj[:, 1])

    for traj, color, label in [
        (true_states, "green",      f"Tracking réel (expID {test_id})"),
        (lr_traj,     "steelblue",  "Linéaire"),
        (mlp_traj,    "darkorange", "MLP"),
    ]:
        x, y = to_xy(traj)
        ax_xy.plot(x, y, color=color, linewidth=1.5, label=label)
        ax_xy.plot(x[0], y[0], "o", color=color, markersize=6)
        ax_xy.plot(x[-1], y[-1], "x", color=color, markersize=8, markeredgewidth=2)

    ax_xy.set_aspect("equal")
    ax_xy.set_title("Trajectoire — vue de dessus (pixels centrés)")
    ax_xy.set_xlabel("x (px)")
    ax_xy.set_ylabel("y (px)")
    ax_xy.legend(fontsize=8)
    ax_xy.grid(True, alpha=0.25)

    for traj, t_ax, color, label in [
        (true_states, t_s,                        "green",      "Réel"),
        (lr_traj,     t_s[:len(lr_traj)],         "steelblue",  "Linéaire"),
        (mlp_traj,    t_s[:len(mlp_traj)],        "darkorange", "MLP"),
    ]:
        ax_r.plot(t_ax, traj[:, 0], color=color, linewidth=1.5, label=label)

    ax_r.set_title("r(t) en pixels")
    ax_r.set_xlabel("t (s)")
    ax_r.set_ylabel("r (px)")
    ax_r.legend(fontsize=8)
    ax_r.grid(True, alpha=0.25)

    def speed(traj):
        return np.sqrt(traj[:, 2] ** 2 + traj[:, 3] ** 2)

    for traj, t_ax, color, label in [
        (true_states, t_s,                 "green",      "Réel"),
        (lr_traj,     t_s[:len(lr_traj)],  "steelblue",  "Linéaire"),
        (mlp_traj,    t_s[:len(mlp_traj)], "darkorange", "MLP"),
    ]:
        ax_v.plot(t_ax, speed(traj), color=color, linewidth=1.5, label=label)

    ax_v.set_title("|v|(t) en px/unité-temps")
    ax_v.set_xlabel("t (s)")
    ax_v.set_ylabel("|v| (px/t)")
    ax_v.legend(fontsize=8)
    ax_v.grid(True, alpha=0.25)

    n_lr  = min(len(lr_traj),  len(true_states))
    n_mlp = min(len(mlp_traj), len(true_states))
    ax_err.plot(t_s[:n_lr],  np.abs(lr_traj[:n_lr,   0] - true_states[:n_lr,  0]),
                color="steelblue",  linewidth=1.5, label="Linéaire")
    ax_err.plot(t_s[:n_mlp], np.abs(mlp_traj[:n_mlp, 0] - true_states[:n_mlp, 0]),
                color="darkorange", linewidth=1.5, label="MLP")
    ax_err.set_title("|Δr|(t) — erreur sur le rayon (px)")
    ax_err.set_xlabel("t (s)")
    ax_err.set_ylabel("|r_prédit − r_réel| (px)")
    ax_err.legend(fontsize=8)
    ax_err.grid(True, alpha=0.25)

    plt.tight_layout()
    plt.show()


# ── Main ───────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test-id", type=int, default=None,
        help="expID à utiliser comme test (défaut : dernier expID du CSV)",
    )
    parser.add_argument(
        "--passes", type=int, default=3,
        help="Passes d'entraînement (défaut : 3)",
    )
    args = parser.parse_args()

    cfg = load_config("ml")

    tracking = cfg["tracking"]
    csv_path = ROOT / cfg["paths"]["tracking_data"]
    cx, cy   = tracking["center_x"], tracking["center_y"]
    R_px     = cfg["physics"]["R"] * tracking["px_per_meter"]

    print("\nChargement des données de tracking (unités pixels, correction offset caméra)...")
    experiments = load_experiments(csv_path, tracking)
    all_ids     = sorted(experiments.keys())
    test_id     = args.test_id if args.test_id is not None else all_ids[-1]

    if test_id not in experiments:
        print(f"⚠  expID {test_id} introuvable. IDs disponibles : {all_ids}")
        sys.exit(1)

    test_states = experiments[test_id]
    timestamps  = get_timestamps(csv_path, test_id)
    n_train     = len(all_ids) - 1

    print(f"  {len(all_ids)} expériences — test : expID {test_id} "
          f"({len(test_states)} pts)  entraînement : {n_train} expériences")

    init_state = test_states[0].astype(float)
    print(f"\nConditions initiales (expID {test_id}) :")
    print(f"  r0={init_state[0]:.1f} px  θ0={init_state[1]:.4f} rad"
          f"  vr0={init_state[2]:.2f} px/t  vθ0={init_state[3]:.2f} px/t")

    print(f"\nEntraînement sur {n_train} expériences ({args.passes} passes)...")
    lr_model, mlp_model = train_on_experiments(experiments, test_id, args.passes)

    # Seuils en unités pixel : r_min_px, v_stop_px
    r_min_px   = cfg["physics"]["center_radius"] * tracking["px_per_meter"]
    vel_scale  = tracking.get("real_width", 172) / tracking.get("video_width", 960)
    v_stop_px  = cfg["physics"]["v_stop"] * tracking["px_per_meter"] * vel_scale

    # r_max=None : le tracking peut dépasser R (calibration approx.)
    n_steps = len(test_states)
    with cf.ProcessPoolExecutor(max_workers=2) as pool:
        f_lr  = pool.submit(predict_trajectory, lr_model,  init_state, n_steps, r_max=None, r_min=r_min_px, v_stop=v_stop_px)
        f_mlp = pool.submit(predict_trajectory, mlp_model, init_state, n_steps, r_max=None, r_min=r_min_px, v_stop=v_stop_px)
        lr_traj  = f_lr.result()
        mlp_traj = f_mlp.result()

    print(f"\n{'═' * 52}")
    print(f"  Trajectoire test : {len(test_states)} pts"
          f"  (r : {test_states[:,0].min():.0f}→{test_states[:,0].max():.0f} px)")
    print_errors("Régression linéaire", trajectory_errors(lr_traj,  test_states))
    print_errors("MLP",                 trajectory_errors(mlp_traj, test_states))
    print(f"{'═' * 52}\n")

    plot_comparison(test_states, lr_traj, mlp_traj, timestamps, R_px, test_id, n_train)
