"""Test du cycle complet entraînement → prédiction sur données synthétiques.

Entraîne LinearStepModel et MLPStepModel sur un sous-ensemble des chunks
synthétiques existants, puis compare les prédictions avec la vérité terrain
issue du simulateur physique.

Usage :
    python src/scripts/test_synth_training.py
    python src/scripts/test_synth_training.py --chunks 5
"""

import argparse
import concurrent.futures as cf
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, MLPStepModel, state_to_features
from ml.train import fit_shared_scalers
from ml.predict import predict_trajectory
from physics.cone import compute_cone
from utils.angle import v0_dir_to_vr_vtheta

warnings.filterwarnings("ignore")


# ── Entraînement ──────────────────────────────────────────────────────────────


def _load_chunk(path: Path):
    """Charge un chunk .npz → (X_feat, y_feat)."""
    data = np.load(path)
    X = state_to_features(data["X"].astype(np.float32))
    y = state_to_features(data["y"].astype(np.float32))
    return X, y


def _val_loss_chunks(model, val_paths: list[Path]) -> float:
    """MSE moyen en espace normalisé sur les chunks de validation."""
    if not val_paths:
        return float("nan")
    losses = []
    for path in val_paths:
        X, y = _load_chunk(path)
        losses.append(model.val_loss(X, y))
    return float(np.mean(losses))


def train_on_chunks(
    chunk_paths: list[Path],
    n_epochs: int = 3,
    val_fraction: float = 0.1,
) -> tuple[LinearStepModel, MLPStepModel]:
    """Entraîne LR et MLP selon les specs du pipeline complet.

    - Scalers partagés calibrés sur un échantillon uniforme de tous les chunks.
    - LR : 1 seule passe (équations normales exactes, répétitions inutiles).
    - MLP : n_epochs passes avec shuffle des chunks + val_loss après chaque epoch.
    - val_fraction : fraction de chunks réservée à la validation.
    """
    n_val       = max(0, min(int(len(chunk_paths) * val_fraction), len(chunk_paths) - 1))
    train_paths = chunk_paths[:len(chunk_paths) - n_val]
    val_paths   = chunk_paths[len(chunk_paths) - n_val:]

    print(f"  Split : {len(train_paths)} chunks train, {len(val_paths)} chunks val")

    # Scalers calibrés sur un échantillon uniforme de tous les chunks (train + val)
    scaler_X, scaler_y = fit_shared_scalers(chunk_paths, n_sample=max(3, len(chunk_paths)))

    lr_model  = LinearStepModel()
    mlp_model = MLPStepModel()
    lr_model.inject_scalers(scaler_X, scaler_y)
    mlp_model.inject_scalers(scaler_X, scaler_y)

    # ── LR : 1 passe ──────────────────────────────────────────────────────────
    print("  LR — 1 passe (solution exacte)...")
    for i, path in enumerate(train_paths):
        X, y = _load_chunk(path)
        lr_model.partial_fit(X, y)
        print(f"    chunk {i + 1}/{len(train_paths)}  ({len(X):,} paires)")
    if val_paths:
        print(f"  LR   val MSE = {_val_loss_chunks(lr_model, val_paths):.6f}")

    # ── MLP : n_epochs passes avec shuffle ────────────────────────────────────
    rng = np.random.default_rng(0)
    for epoch in range(n_epochs):
        order = rng.permutation(len(train_paths))
        print(f"  MLP — epoch {epoch + 1}/{n_epochs} (chunks shufflés)...")
        for idx in order:
            X, y = _load_chunk(train_paths[int(idx)])
            mlp_model.partial_fit(X, y)
        if val_paths:
            print(f"  MLP  val MSE = {_val_loss_chunks(mlp_model, val_paths):.6f}")

    return lr_model, mlp_model


# ── Métriques ─────────────────────────────────────────────────────────────────


def trajectory_errors(
    pred: np.ndarray, true: np.ndarray, n_steps_max: int
) -> dict[str, float]:
    """Calcule MAE sur r, θ, vr, vθ sur les pas communs."""
    n = min(len(pred), len(true))
    diff = np.abs(pred[:n] - true[:n])
    return {
        "n_steps_pred": len(pred),
        "n_steps_true": len(true),
        "n_steps_max":  n_steps_max,
        "r_final":      float(pred[-1, 0]),
        "mae_r":        float(diff[:, 0].mean()),
        "mae_theta":    float(diff[:, 1].mean()),
        "mae_vr":       float(diff[:, 2].mean()),
        "mae_vtheta":   float(diff[:, 3].mean()),
        "mae_total":    float(diff.mean()),
    }


def print_errors(label: str, errs: dict, R: float) -> None:
    n_pred  = errs["n_steps_pred"]
    n_true  = errs["n_steps_true"]
    r_final = errs["r_final"]
    if n_pred >= errs["n_steps_max"]:
        status = "(borne atteinte)"
    elif r_final >= R - 1e-6:
        status = "(sortie bord)"
    else:
        status = "(bille arrêtée)"
    print(f"\n  {label}")
    print(f"    Pas prédits / vrais : {n_pred} / {n_true}  {status}")
    print(f"    MAE r      : {errs['mae_r']:.5f} m")
    print(f"    MAE θ      : {errs['mae_theta']:.5f} rad")
    print(f"    MAE vr     : {errs['mae_vr']:.5f} m/s")
    print(f"    MAE vθ     : {errs['mae_vtheta']:.5f} m/s")
    print(f"    MAE global : {errs['mae_total']:.5f}")


# ── Visualisation ─────────────────────────────────────────────────────────────


def plot_comparison(
    true_traj: np.ndarray,
    lr_traj:   np.ndarray,
    mlp_traj:  np.ndarray,
    dt: float,
    R: float,
    n_chunks: int,
) -> None:
    """Figure 2×2 : XY (dessus) + r(t) + |v|(t) + erreur r cumulée."""
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"Test entraînement synthétique — {n_chunks} chunk(s)\n"
        "Vert = vérité terrain (physique)  |  Bleu = Linéaire  |  Orange = MLP",
        fontsize=12,
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    ax_xy  = fig.add_subplot(gs[0, 0])
    ax_r   = fig.add_subplot(gs[0, 1])
    ax_v   = fig.add_subplot(gs[1, 0])
    ax_err = fig.add_subplot(gs[1, 1])

    def to_xy(traj):
        r, theta = traj[:, 0], traj[:, 1]
        return r * np.cos(theta), r * np.sin(theta)

    def t_axis(traj):
        return np.arange(len(traj)) * dt

    # Cercle de bord
    ang = np.linspace(0, 2 * np.pi, 300)
    for ax in [ax_xy]:
        ax.plot(R * np.cos(ang), R * np.sin(ang),
                color="gray", linestyle="--", linewidth=1, label="bord R")

    # XY — vue dessus
    for traj, color, label in [
        (true_traj, "green",      "Vrai (physique)"),
        (lr_traj,   "steelblue",  "Linéaire"),
        (mlp_traj,  "darkorange", "MLP"),
    ]:
        x, y = to_xy(traj)
        ax_xy.plot(x, y, color=color, linewidth=1.5, label=label)
        ax_xy.plot(x[0], y[0], "o", color=color, markersize=6)
        ax_xy.plot(x[-1], y[-1], "x", color=color, markersize=8, markeredgewidth=2)

    ax_xy.set_aspect("equal")
    ax_xy.set_title("Trajectoire — vue de dessus")
    ax_xy.set_xlabel("x (m)")
    ax_xy.set_ylabel("y (m)")
    ax_xy.legend(fontsize=8)
    ax_xy.grid(True, alpha=0.25)

    # r(t)
    for traj, color, label in [
        (true_traj, "green",      "Vrai"),
        (lr_traj,   "steelblue",  "Linéaire"),
        (mlp_traj,  "darkorange", "MLP"),
    ]:
        ax_r.plot(t_axis(traj), traj[:, 0], color=color, linewidth=1.5, label=label)

    ax_r.set_title("r(t)")
    ax_r.set_xlabel("t (s)")
    ax_r.set_ylabel("r (m)")
    ax_r.legend(fontsize=8)
    ax_r.grid(True, alpha=0.25)

    # |v|(t)
    def speed(traj):
        return np.sqrt(traj[:, 2] ** 2 + traj[:, 3] ** 2)

    for traj, color, label in [
        (true_traj, "green",      "Vrai"),
        (lr_traj,   "steelblue",  "Linéaire"),
        (mlp_traj,  "darkorange", "MLP"),
    ]:
        ax_v.plot(t_axis(traj), speed(traj), color=color, linewidth=1.5, label=label)

    ax_v.set_title("|v|(t)")
    ax_v.set_xlabel("t (s)")
    ax_v.set_ylabel("|v| (m/s)")
    ax_v.legend(fontsize=8)
    ax_v.grid(True, alpha=0.25)

    # Erreur |r_pred - r_true| en fonction du pas
    n_lr  = min(len(lr_traj),  len(true_traj))
    n_mlp = min(len(mlp_traj), len(true_traj))
    ax_err.plot(
        np.arange(n_lr)  * dt,
        np.abs(lr_traj[:n_lr, 0]   - true_traj[:n_lr, 0]),
        color="steelblue",  linewidth=1.5, label="Linéaire",
    )
    ax_err.plot(
        np.arange(n_mlp) * dt,
        np.abs(mlp_traj[:n_mlp, 0] - true_traj[:n_mlp, 0]),
        color="darkorange", linewidth=1.5, label="MLP",
    )
    ax_err.set_title("|Δr|(t) — erreur sur le rayon")
    ax_err.set_xlabel("t (s)")
    ax_err.set_ylabel("|r_prédit − r_vrai| (m)")
    ax_err.legend(fontsize=8)
    ax_err.grid(True, alpha=0.25)

    plt.show()


# ── Main ──────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chunks", type=int, default=10,
        help="Nombre de chunks synthétiques à utiliser pour l'entraînement (défaut : 10)",
    )
    parser.add_argument(
        "--epochs", type=int, default=3,
        help="Nombre d'epochs MLP (défaut : 3)",
    )
    args = parser.parse_args()

    cfg = load_config("ml")

    phys         = {**cfg["physics"], **cfg["synth"]["physics"]}
    dt           = phys["dt"]
    n_steps_pred = cfg["display"]["n_steps_pred"]  # borne affichage/prédiction
    R            = phys["R"]
    data_dir     = ROOT / cfg["paths"]["synth_data_dir"]
    preset       = cfg["preset"]["default"]

    # Conditions initiales
    vr0, vtheta0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    init_state   = np.array([preset["r0"], preset["theta0"], vr0, vtheta0])

    print(f"\nConditions initiales : r0={preset['r0']} m  θ0={preset['theta0']} rad"
          f"  v0={preset['v0']} m/s  dir={preset['direction_deg']}°"
          f"  → vr0={vr0:.4f} m/s  vθ0={vtheta0:.4f} m/s")

    # Chunks disponibles
    all_chunks = sorted(data_dir.glob("chunk_*.npz"))
    if not all_chunks:
        print(f"\n⚠  Aucun chunk trouvé dans {data_dir}")
        print("   Lancez d'abord : python src/scripts/generate_data.py")
        sys.exit(1)

    n_use = min(args.chunks, len(all_chunks))
    print(f"\nEntraînement sur {n_use} chunk(s) / {len(all_chunks)} disponibles...")

    lr_model, mlp_model = train_on_chunks(all_chunks[:n_use], n_epochs=args.epochs)

    # Vérité terrain (n_steps_pred comme borne — arrêt anticipé par les conditions physiques)
    true_traj = compute_cone(
        r0=float(init_state[0]), theta0=float(init_state[1]),
        vr0=float(init_state[2]), vtheta0=float(init_state[3]),
        R=R, depth=phys["depth"], friction=phys["friction"],
        g=phys["g"], dt=dt, n_steps=n_steps_pred,
    )

    r_min  = phys.get("center_radius", 0.03)
    v_stop = phys.get("v_stop", 0.002)

    # Prédictions LR et MLP en parallèle
    with cf.ProcessPoolExecutor(max_workers=2) as pool:
        f_lr  = pool.submit(predict_trajectory, lr_model,  init_state, n_steps_pred, r_max=R, r_min=r_min, v_stop=v_stop)
        f_mlp = pool.submit(predict_trajectory, mlp_model, init_state, n_steps_pred, r_max=R, r_min=r_min, v_stop=v_stop)
        lr_traj  = f_lr.result()
        mlp_traj = f_mlp.result()

    # Métriques
    print(f"\n{'═' * 52}")
    print(f"  Vérité terrain : {len(true_traj)} pas")
    print_errors("Régression linéaire", trajectory_errors(lr_traj,  true_traj, n_steps_pred), R)
    print_errors("MLP",                 trajectory_errors(mlp_traj, true_traj, n_steps_pred), R)
    print(f"{'═' * 52}\n")

    plot_comparison(true_traj, lr_traj, mlp_traj, dt, R, n_use)
