"""Comparaison physique / ML-linéaire / ML-MLP / tracking réel.

Ce script constitue la démonstration centrale du projet :
pour les mêmes conditions initiales (issues d'une expérience réelle),
il superpose sur un seul graphique les quatre approches de simulation :
  1. Simulation physique déterministe (Euler-Cromer)
  2. Régression linéaire ML (entraînée sur les autres expériences)
  3. MLP ML (même entraînement)
  4. Tracking réel (caméra) — trajectoire de référence

Toutes les courbes sont normalisées par R (rayon du cône) pour permettre
la comparaison directe entre l'espace physique (mètres) et l'espace
pixel (coordonnées caméra).

Usage :
    python src/scripts/compare_approaches.py
    python src/scripts/compare_approaches.py --test-id 9
    python src/scripts/compare_approaches.py --passes 5 --output figures/compare.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, MLPStepModel, state_to_features
from ml.predict import predict_trajectory
from ml.train import compute_exp_centers
from physics.cone import compute_cone
from utils.angle import v0_dir_to_vr_vtheta  # noqa: F401  (non utilisé ici mais documenté)


# ── Chargement des expériences ──────────────────────────────────────────────────


def load_experiments(
    csv_path: Path, tracking: dict,
) -> tuple[dict[int, np.ndarray], pd.DataFrame]:
    """Charge toutes les expériences en unités pixels centrés.

    Retourne ({expID: states (N,4)}, df brut).
    states = (r_px, θ, vr_px, vθ_px) dans le repère centré sur le cône.
    """
    df = pd.read_csv(csv_path, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()
    centers = compute_exp_centers(df, tracking)
    r_min_px = tracking["center_radius"] * tracking["px_per_meter"]

    experiments: dict[int, np.ndarray] = {}
    for exp_id, grp in df.groupby("expID"):
        grp = grp.sort_values("temps")
        cx, cy = centers[exp_id]
        xc = grp["x"].values      - cx
        yc = grp["y"].values      - cy
        vx = grp["speedX"].values
        vy = grp["speedY"].values

        r      = np.sqrt(xc**2 + yc**2)
        theta  = np.arctan2(yc, xc)
        vr     = (xc * vx + yc * vy) / np.maximum(r, r_min_px)
        vtheta = (xc * vy - yc * vx) / np.maximum(r, r_min_px)
        experiments[int(exp_id)] = np.column_stack([r, theta, vr, vtheta]).astype(np.float64)

    return experiments, df


def get_timestamps_s(df: pd.DataFrame, exp_id: int) -> np.ndarray:
    """Timestamps de l'expérience en secondes, normalisés à 0."""
    grp = df[df["expID"] == exp_id].sort_values("temps")
    t = grp["temps"].values.astype(float)
    return (t - t[0]) / 1000.0  # ms → s


# ── Entraînement ML réel ────────────────────────────────────────────────────────


def train_real_models(
    experiments: dict[int, np.ndarray],
    test_id: int,
    n_passes: int,
) -> tuple[LinearStepModel, MLPStepModel]:
    """Entraîne LinearStepModel et MLPStepModel sur toutes les exp. sauf test_id."""
    train_ids = sorted(k for k in experiments if k != test_id)

    pairs = [
        (state_to_features(s[:-1]), state_to_features(s[1:]))
        for eid in train_ids
        for s in (experiments[eid],)
        if len(s) >= 2
    ]

    X_all   = np.vstack([X for X, _ in pairs])
    res_all = np.vstack([y - X for X, y in pairs])
    scaler_X = StandardScaler().fit(X_all)
    scaler_y = StandardScaler().fit(res_all)

    lr  = LinearStepModel()
    mlp = MLPStepModel()
    lr.inject_scalers(scaler_X, scaler_y)
    mlp.inject_scalers(scaler_X, scaler_y)

    for X, y in pairs:
        lr.partial_fit(X, y)

    rng = np.random.default_rng(0)
    for _ in range(n_passes):
        for i in rng.permutation(len(pairs)):
            mlp.partial_fit(*pairs[int(i)])

    return lr, mlp


# ── Conversion pixels ↔ mètres ─────────────────────────────────────────────────


def px_to_physics(state_px: np.ndarray, px_per_meter: float, vel_scale: float) -> np.ndarray:
    """Convertit un état (r_px, θ, vr_px, vθ_px) → (r_m, θ, vr_m/s, vθ_m/s).

    vel_scale = real_width / video_width : facteur de conversion vitesse tracking → px/s.
    Division supplémentaire par px_per_meter pour obtenir des m/s.
    """
    r_m  = state_px[0] / px_per_meter
    vr_m  = state_px[2] / (px_per_meter * vel_scale)
    vth_m = state_px[3] / (px_per_meter * vel_scale)
    return np.array([r_m, state_px[1], vr_m, vth_m])


# ── Visualisation ───────────────────────────────────────────────────────────────


def _draw_circle(ax, radius_norm: float = 1.0, **kw) -> None:
    ang = np.linspace(0, 2 * np.pi, 300)
    ax.plot(radius_norm * np.cos(ang), radius_norm * np.sin(ang), **kw)


def plot_comparison(
    real_states:  np.ndarray,     # (N, 4) en pixels
    phys_traj:    np.ndarray,     # (P, 4) en mètres
    lr_traj:      np.ndarray,     # (L, 4) en pixels
    mlp_traj:     np.ndarray,     # (M, 4) en pixels
    timestamps_s: np.ndarray,     # (N,) en secondes
    R_px:         float,
    R_m:          float,
    dt_phys:      float,
    fps:          float,
    test_id:      int,
    n_train:      int,
    output:       Path | None,
) -> None:
    """Figure 2×2 : XY normalisé, r/R vs t, |v|/v0 vs t, erreur r vs t."""

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"Comparaison des approches — expID {test_id} (test, {n_train} exp. entraînement)\n"
        "Toutes les courbes normalisées par R (sans dimension)",
        fontsize=12, fontweight="bold",
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32)
    ax_xy  = fig.add_subplot(gs[0, 0])
    ax_r   = fig.add_subplot(gs[0, 1])
    ax_v   = fig.add_subplot(gs[1, 0])
    ax_err = fig.add_subplot(gs[1, 1])

    # Normalisation temporelle
    t_real_s  = timestamps_s                                        # tracking : timestamps réels
    t_phys_s  = np.arange(len(phys_traj)) * dt_phys                # physique : t = i * dt
    t_lr_s    = np.arange(len(lr_traj))   / fps                    # ML : 1 pas = 1 frame
    t_mlp_s   = np.arange(len(mlp_traj))  / fps

    # Normalisation spatiale par R dans chaque espace
    def norm_r_real(traj):   return traj[:, 0] / R_px   # pixels → [0, 1]
    def norm_r_phys(traj):   return traj[:, 0] / R_m    # mètres → [0, 1]
    def norm_xy_real(traj):  return traj[:, 0] * np.cos(traj[:, 1]) / R_px, traj[:, 0] * np.sin(traj[:, 1]) / R_px
    def norm_xy_phys(traj):  return traj[:, 0] * np.cos(traj[:, 1]) / R_m,  traj[:, 0] * np.sin(traj[:, 1]) / R_m

    STYLES = [
        (real_states, norm_r_real, norm_xy_real, t_real_s,  "green",       "Tracking réel",    "-",  2.5),
        (phys_traj,   norm_r_phys, norm_xy_phys, t_phys_s,  "royalblue",   "Simulation phys.", "--", 1.8),
        (lr_traj,     norm_r_real, norm_xy_real, t_lr_s,    "darkorange",  "ML Linéaire",      "-.", 1.8),
        (mlp_traj,    norm_r_real, norm_xy_real, t_mlp_s,   "crimson",     "ML MLP",           ":",  1.8),
    ]

    # ── Panel 1 : XY normalisé ────────────────────────────────────────────────
    _draw_circle(ax_xy, color="gray", linestyle="--", linewidth=1, label="bord (r/R = 1)")
    for traj, _, xy_fn, _, color, label, ls, lw in STYLES:
        x, y = xy_fn(traj)
        ax_xy.plot(x, y, color=color, label=label, linestyle=ls, linewidth=lw)
        ax_xy.plot(x[0], y[0], "o", color=color, markersize=6)

    ax_xy.set_aspect("equal")
    ax_xy.set_title("Trajectoire (vue de dessus, r/R normalisé)")
    ax_xy.set_xlabel("x / R")
    ax_xy.set_ylabel("y / R")
    ax_xy.legend(fontsize=8)
    ax_xy.grid(True, alpha=0.25)

    # ── Panel 2 : r/R vs temps ────────────────────────────────────────────────
    for traj, r_fn, _, t_ax, color, label, ls, lw in STYLES:
        ax_r.plot(t_ax, r_fn(traj), color=color, label=label, linestyle=ls, linewidth=lw)

    ax_r.set_title("r/R en fonction du temps")
    ax_r.set_xlabel("t (s)")
    ax_r.set_ylabel("r / R")
    ax_r.legend(fontsize=8)
    ax_r.grid(True, alpha=0.25)

    # ── Panel 3 : vitesse normalisée ──────────────────────────────────────────
    def speed(traj):
        return np.sqrt(traj[:, 2]**2 + traj[:, 3]**2)

    # Normalise chaque courbe par sa vitesse initiale
    for traj, _, _, t_ax, color, label, ls, lw in STYLES:
        v = speed(traj)
        v0 = v[0] if v[0] > 0 else 1.0
        ax_v.plot(t_ax, v / v0, color=color, label=label, linestyle=ls, linewidth=lw)

    ax_v.set_title("|v|(t) / v₀ — vitesse normalisée")
    ax_v.set_xlabel("t (s)")
    ax_v.set_ylabel("|v| / v₀")
    ax_v.legend(fontsize=8)
    ax_v.grid(True, alpha=0.25)

    # ── Panel 4 : erreur |r_pred − r_réel| / R ───────────────────────────────
    for traj, r_fn, _, t_ax, color, label, ls, lw in STYLES[1:]:   # skip real
        n = min(len(traj), len(real_states))
        t_cmp = t_ax[:n]
        t_ref = t_real_s[:n]
        # Ré-échantillonne la référence sur la grille temporelle de la prédiction
        r_ref_interp = np.interp(t_cmp, t_ref, norm_r_real(real_states))
        err = np.abs(r_fn(traj)[:n] - r_ref_interp)
        ax_err.plot(t_cmp, err, color=color, label=label, linestyle=ls, linewidth=lw)

    ax_err.set_title("|r_pred − r_réel| / R — erreur sur le rayon")
    ax_err.set_xlabel("t (s)")
    ax_err.set_ylabel("|r_pred/R − r_réel/R|")
    ax_err.legend(fontsize=8)
    ax_err.grid(True, alpha=0.25)

    plt.tight_layout()

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"\nFigure sauvegardée : {output}")

    plt.show()


# ── Main ────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare simulation physique, ML (linéaire + MLP) et tracking réel."
    )
    parser.add_argument("--test-id", type=int, default=None,
                        help="expID utilisé comme test (défaut : dernier)")
    parser.add_argument("--passes",  type=int, default=3,
                        help="Passes d'entraînement ML (défaut : 3)")
    parser.add_argument("--output",  type=str, default=None,
                        help="Chemin de sauvegarde de la figure (ex. figures/compare.png)")
    args = parser.parse_args()

    cfg      = load_config("ml")
    phys_cfg = cfg["physics"]
    tracking = cfg["tracking"]
    synth    = cfg["synth"]["physics"]

    csv_path     = ROOT / cfg["paths"]["tracking_data"]
    px_per_meter = tracking["px_per_meter"]
    fps          = tracking["fps"]
    vel_scale    = tracking["real_width"] / tracking["video_width"]
    R_px         = phys_cfg["R"] * px_per_meter
    R_m          = phys_cfg["R"]

    # ── Chargement tracking ──────────────────────────────────────────────────
    print("\nChargement des expériences de tracking...")
    experiments, df = load_experiments(csv_path, tracking)
    all_ids  = sorted(experiments.keys())
    test_id  = args.test_id if args.test_id is not None else all_ids[-1]

    if test_id not in experiments:
        print(f"⚠  expID {test_id} introuvable. IDs disponibles : {all_ids}")
        sys.exit(1)

    test_states  = experiments[test_id]
    timestamps_s = get_timestamps_s(df, test_id)
    n_train      = len(all_ids) - 1
    init_px      = test_states[0].astype(float)

    print(f"  {len(all_ids)} expériences — test : expID {test_id} "
          f"({len(test_states)} pts)  entraînement : {n_train} exp.")
    print(f"\nConditions initiales (pixels) :"
          f"  r0={init_px[0]:.1f} px  θ0={init_px[1]:.4f} rad"
          f"  vr0={init_px[2]:.2f}  vθ0={init_px[3]:.2f} px/frame")

    # ── Simulation physique ───────────────────────────────────────────────────
    # Conversion des CI pixels → mètres pour la simulation physique
    init_m = px_to_physics(init_px, px_per_meter, vel_scale)
    print(f"\nConditions initiales (mètres) :"
          f"  r0={init_m[0]:.4f} m  θ0={init_m[1]:.4f} rad"
          f"  vr0={init_m[2]:.4f} m/s  vθ0={init_m[3]:.4f} m/s")

    print("\nSimulation physique (Euler-Cromer)...")
    phys_traj = compute_cone(
        r0=init_m[0], theta0=init_m[1], vr0=init_m[2], vtheta0=init_m[3],
        R=R_m, depth=synth["depth"],
        friction=phys_cfg["friction"], g=phys_cfg["g"],
        dt=phys_cfg["dt"], n_steps=phys_cfg["n_steps"],
        center_radius=phys_cfg["center_radius"],
        method="euler_cromer",
    )
    print(f"  → {len(phys_traj)} pas ({len(phys_traj) * phys_cfg['dt']:.1f} s simulées)")

    # ── Entraînement ML réel ──────────────────────────────────────────────────
    print(f"\nEntraînement ML sur {n_train} expériences ({args.passes} passes)...")
    lr_model, mlp_model = train_real_models(experiments, test_id, args.passes)

    # Seuils de stop en unités pixels
    r_min_px  = phys_cfg["center_radius"] * px_per_meter
    v_stop_px = phys_cfg["v_stop"] * px_per_meter * vel_scale
    n_steps   = len(test_states)

    print("Prédictions ML (linéaire + MLP)...")
    lr_traj  = predict_trajectory(lr_model,  init_px, n_steps, r_max=None, r_min=r_min_px, v_stop=v_stop_px)
    mlp_traj = predict_trajectory(mlp_model, init_px, n_steps, r_max=None, r_min=r_min_px, v_stop=v_stop_px)
    print(f"  Linéaire : {len(lr_traj)} pas   MLP : {len(mlp_traj)} pas")

    # ── Résumé erreurs ────────────────────────────────────────────────────────
    print(f"\n{'═' * 54}")
    print(f"  {'Approche':<22}  {'MAE r (px)':<12}  {'MAE r / R'}")
    for label, traj in [("ML Linéaire", lr_traj), ("ML MLP", mlp_traj)]:
        n = min(len(traj), len(test_states))
        mae_r = float(np.abs(traj[:n, 0] - test_states[:n, 0]).mean())
        print(f"  {label:<22}  {mae_r:<12.2f}  {mae_r / R_px:.4f}")
    print(f"{'═' * 54}\n")

    # ── Affichage ─────────────────────────────────────────────────────────────
    output_path = Path(args.output) if args.output else None
    plot_comparison(
        real_states=test_states,
        phys_traj=phys_traj,
        lr_traj=lr_traj,
        mlp_traj=mlp_traj,
        timestamps_s=timestamps_s,
        R_px=R_px,
        R_m=R_m,
        dt_phys=phys_cfg["dt"],
        fps=float(fps),
        test_id=test_id,
        n_train=n_train,
        output=output_path,
    )
