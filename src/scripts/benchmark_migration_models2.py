"""Comparaison LinearRegression vs MLPRegressor sur données synthétiques.

Ce script répond à un scénario de migration pédagogique :
- utiliser la logique de génération de `generate_data.py` (même distribution des CI)
- entraîner un modèle linéaire et un MLP sur des tailles de datasets imposées
- produire les figures de comparaison demandées.

Figures générées :
1) Différence de trajectoire (vérité vs linéaire vs MLP) pour 15, 45 000, 90 000 expériences
2) RMSE des deux modèles après entraînement sur 90 000 expériences
3) Convergence des deux modèles vers 90 000 expériences
4) Training vs validation loss des résidus (pour 90 000 expériences)

Usage :
    python src/scripts/benchmark_migration_models.py
    python src/scripts/benchmark_migration_models.py --workers 8 --mlp-epochs 6
    python src/scripts/benchmark_migration_models.py --no-show
"""

from __future__ import annotations

import argparse
import math
import random
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, MLPStepModel, state_to_features
from ml.predict import predict_trajectory
from physics.cone import compute_cone
from scripts.generate_data import _sample_initial_conditions
from utils.angle import v0_dir_to_vr_vtheta


def _chunk_paths(data_dir: Path) -> list[Path]:
    return sorted(data_dir.glob("chunk_*.npz"))


def _clean_chunk_dir(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for p in data_dir.glob("chunk_*.npz"):
        p.unlink()


def _generate_chunks(
    out_dir: Path,
    n_trajectories: int,
    chunk_size: int,
    phys_cfg: dict,
    gen_cfg: dict,
    seed: int,
) -> list[Path]:
    """Génère des chunks synthétiques (X, y) en reprenant la logique de generate_data.py."""
    _clean_chunk_dir(out_dir)

    rng = np.random.default_rng(seed)
    min_steps = int(gen_cfg.get("min_steps", 50))
    total = 0
    chunk_idx = 0

    while total < n_trajectories:
        n_this = min(chunk_size, n_trajectories - total)
        r0, th0, vr0, vth0 = _sample_initial_conditions(
            n_this, {**phys_cfg, **gen_cfg}, rng
        )

        X_parts: list[np.ndarray] = []
        y_parts: list[np.ndarray] = []
        for i in range(n_this):
            traj = compute_cone(
                r0=float(r0[i]),
                theta0=float(th0[i]),
                vr0=float(vr0[i]),
                vtheta0=float(vth0[i]),
                R=phys_cfg["R"],
                depth=phys_cfg["depth"],
                friction=phys_cfg["friction"],
                g=phys_cfg["g"],
                dt=phys_cfg["dt"],
                n_steps=phys_cfg["n_steps"],
                rolling=bool(phys_cfg.get("rolling", False)),
                rolling_resistance=float(phys_cfg.get("rolling_resistance", 0.0)),
                drag_coeff=float(phys_cfg.get("drag_coeff", 0.0)),
            )
            if len(traj) >= max(2, min_steps):
                X_parts.append(traj[:-1].astype(np.float32))
                y_parts.append(traj[1:].astype(np.float32))

        if not X_parts:
            X = np.empty((0, 4), dtype=np.float32)
            y = np.empty((0, 4), dtype=np.float32)
        else:
            X = np.vstack(X_parts)
            y = np.vstack(y_parts)

        out_path = out_dir / f"chunk_{chunk_idx:05d}.npz"
        np.savez_compressed(out_path, X=X, y=y)
        total += n_this
        chunk_idx += 1

    return _chunk_paths(out_dir)


def _load_chunk_features(path: Path) -> tuple[np.ndarray, np.ndarray]:
    d = np.load(path)
    Xf = state_to_features(d["X"].astype(np.float32))
    yf = state_to_features(d["y"].astype(np.float32))
    return Xf, yf


def _fit_scalers(paths: list[Path]) -> tuple[StandardScaler, StandardScaler]:
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    for p in paths:
        Xf, yf = _load_chunk_features(p)
        residuals = yf - Xf
        if len(Xf) == 0:
            continue
        scaler_X.partial_fit(Xf)
        scaler_y.partial_fit(residuals)
    return scaler_X, scaler_y


def _train_linear(
    paths: list[Path], scaler_X: StandardScaler, scaler_y: StandardScaler
) -> LinearStepModel:
    model = LinearStepModel()
    model.inject_scalers(scaler_X, scaler_y)
    for p in paths:
        Xf, yf = _load_chunk_features(p)
        if len(Xf) == 0:
            continue
        model.partial_fit(Xf, yf)
    return model


def _dataset_loss(model, paths: list[Path]) -> float:
    vals = []
    for p in paths:
        Xf, yf = _load_chunk_features(p)
        if len(Xf) == 0:
            continue
        vals.append(model.val_loss(Xf, yf))
    return float(np.mean(vals)) if vals else float("nan")


def _train_mlp_with_history(
    train_paths: list[Path],
    val_paths: list[Path],
    scaler_X: StandardScaler,
    scaler_y: StandardScaler,
    n_epochs: int,
    seed: int,
) -> tuple[MLPStepModel, list[float], list[float]]:
    model = MLPStepModel()
    model.inject_scalers(scaler_X, scaler_y)

    rng = random.Random(seed)
    train_history: list[float] = []
    val_history: list[float] = []

    for _ in range(n_epochs):
        order = train_paths[:]
        rng.shuffle(order)
        for p in order:
            Xf, yf = _load_chunk_features(path=p)
            if len(Xf) == 0:
                continue
            model.partial_fit(Xf, yf)

        train_history.append(_dataset_loss(model, train_paths))
        val_history.append(_dataset_loss(model, val_paths))

    return model, train_history, val_history


def _build_test_cases(
    n_cases: int,
    phys_cfg: dict,
    gen_cfg: dict,
    seed: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    out: list[tuple[np.ndarray, np.ndarray]] = []

    r0, th0, vr0, vth0 = _sample_initial_conditions(
        n_cases, {**phys_cfg, **gen_cfg}, rng
    )
    for i in range(n_cases):
        traj = compute_cone(
            r0=float(r0[i]),
            theta0=float(th0[i]),
            vr0=float(vr0[i]),
            vtheta0=float(vth0[i]),
            R=phys_cfg["R"],
            depth=phys_cfg["depth"],
            friction=phys_cfg["friction"],
            g=phys_cfg["g"],
            dt=phys_cfg["dt"],
            n_steps=phys_cfg["n_steps"],
            rolling=bool(phys_cfg.get("rolling", False)),
            rolling_resistance=float(phys_cfg.get("rolling_resistance", 0.0)),
            drag_coeff=float(phys_cfg.get("drag_coeff", 0.0)),
        )
        if len(traj) >= 5:
            out.append((traj[0].astype(float), traj.astype(float)))

    if not out:
        raise RuntimeError("Aucun cas de test valide généré.")
    return out


def _evaluate_rmse(
    model,
    test_cases: list[tuple[np.ndarray, np.ndarray]],
    n_steps_pred: int,
    r_max: float,
    r_min: float,
    v_stop: float,
    v_scale: float,
) -> dict[str, float]:
    rmse_r_vals = []
    rmse_theta_vals = []
    rmse_vr_vals = []
    rmse_vtheta_vals = []
    nrmse_state_vals = []

    for init_state, true_traj in test_cases:
        pred = predict_trajectory(
            model,
            init_state,
            n_steps_pred,
            r_max=r_max,
            r_min=r_min,
            v_stop=v_stop,
        )
        n = min(len(pred), len(true_traj))
        if n == 0:
            continue
        diff = pred[:n] - true_traj[:n]

        # Erreur angulaire ramenée dans [-pi, pi] pour éviter les sauts de phase.
        theta_diff = np.arctan2(np.sin(diff[:, 1]), np.cos(diff[:, 1]))

        rmse_r_vals.append(float(np.sqrt(np.mean(diff[:, 0] ** 2))))
        rmse_theta_vals.append(float(np.sqrt(np.mean(theta_diff**2))))
        rmse_vr_vals.append(float(np.sqrt(np.mean(diff[:, 2] ** 2))))
        rmse_vtheta_vals.append(float(np.sqrt(np.mean(diff[:, 3] ** 2))))

        # NRMSE d'etat sans unite: normalisation par echelles physiques.
        r_norm = diff[:, 0] / max(r_max, 1e-9)
        theta_norm = theta_diff / np.pi
        vr_norm = diff[:, 2] / max(v_scale, 1e-9)
        vtheta_norm = diff[:, 3] / max(v_scale, 1e-9)
        normed = np.column_stack([r_norm, theta_norm, vr_norm, vtheta_norm])
        nrmse_state_vals.append(float(np.sqrt(np.mean(normed**2))))

    return {
        "rmse_r": float(np.mean(rmse_r_vals)) if rmse_r_vals else float("nan"),
        "rmse_theta": (
            float(np.mean(rmse_theta_vals)) if rmse_theta_vals else float("nan")
        ),
        "rmse_vr": float(np.mean(rmse_vr_vals)) if rmse_vr_vals else float("nan"),
        "rmse_vtheta": (
            float(np.mean(rmse_vtheta_vals)) if rmse_vtheta_vals else float("nan")
        ),
        "nrmse_state": (
            float(np.mean(nrmse_state_vals)) if nrmse_state_vals else float("nan")
        ),
    }


def _split_train_val(
    paths: list[Path], val_fraction: float
) -> tuple[list[Path], list[Path]]:
    if len(paths) <= 1:
        return paths, []
    n_val = max(1, int(math.floor(len(paths) * val_fraction)))
    n_val = min(n_val, len(paths) - 1)
    return paths[:-n_val], paths[-n_val:]


def _plot_trajectories_for_sizes(
    out_file: Path,
    curves: dict[int, dict[str, np.ndarray]],
    R: float,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharex=True, sharey=True)
    sizes = [15, 45000, 90000]
    for ax, n in zip(axes, sizes):
        d = curves[n]
        true_xy = (
            d["true"][:, 0] * np.cos(d["true"][:, 1]),
            d["true"][:, 0] * np.sin(d["true"][:, 1]),
        )
        lin_xy = (
            d["linear"][:, 0] * np.cos(d["linear"][:, 1]),
            d["linear"][:, 0] * np.sin(d["linear"][:, 1]),
        )
        mlp_xy = (
            d["mlp"][:, 0] * np.cos(d["mlp"][:, 1]),
            d["mlp"][:, 0] * np.sin(d["mlp"][:, 1]),
        )

        t = np.linspace(0, 2 * np.pi, 200)
        ax.plot(R * np.cos(t), R * np.sin(t), "--", color="0.6", linewidth=1)
        ax.plot(*true_xy, color="black", linewidth=2, label="Vérité")
        ax.plot(
            *lin_xy, color="tab:orange", linewidth=1.8, linestyle="--", label="Linéaire"
        )
        ax.plot(*mlp_xy, color="tab:blue", linewidth=1.8, linestyle=":", label="MLP")
        ax.set_title(f"{n:,} expériences")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.25)
        ax.set_xlabel("x (m)")
    axes[0].set_ylabel("y (m)")
    axes[-1].legend(loc="best")
    fig.suptitle("Différence entre trajectoires: vraies vs simulées avec ML")
    fig.tight_layout()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=160, bbox_inches="tight")


def _plot_rmse_90000(
    out_file: Path, rmse_linear: dict[str, float], rmse_mlp: dict[str, float]
) -> None:
    labels = [
        "RMSE rayon (m)",
        "RMSE angle (rad)",
        "RMSE vr (m/s)",
        "RMSE vtheta (m/s)",
        "NRMSE état",
    ]
    lin_vals = [
        rmse_linear["rmse_r"],
        rmse_linear["rmse_theta"],
        rmse_linear["rmse_vr"],
        rmse_linear["rmse_vtheta"],
        rmse_linear["nrmse_state"],
    ]
    mlp_vals = [
        rmse_mlp["rmse_r"],
        rmse_mlp["rmse_theta"],
        rmse_mlp["rmse_vr"],
        rmse_mlp["rmse_vtheta"],
        rmse_mlp["nrmse_state"],
    ]

    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(x - width / 2, lin_vals, width, label="Linéaire", color="tab:orange")
    ax.bar(x + width / 2, mlp_vals, width, label="MLP", color="tab:blue")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("RMSE")
    ax.set_title("RMSE/NRMSE des modèles sur 90 000 expériences")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=160, bbox_inches="tight")


def _plot_convergence_90000(
    out_file: Path,
    traj_counts: list[int],
    rmse_linear: list[float],
    rmse_mlp: list[float],
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(traj_counts, rmse_linear, marker="o", color="tab:orange", label="Linéaire")
    ax.plot(traj_counts, rmse_mlp, marker="o", color="tab:blue", label="MLP")
    ax.set_xscale("log")
    ax.set_xlabel("Nombre d'expériences d'entraînement")
    ax.set_ylabel("RMSE rayon")
    ax.set_title("Convergence des modèles jusqu'à 90 000 expériences")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=160, bbox_inches="tight")


def _plot_residual_losses_90000(
    out_file: Path,
    mlp_train: list[float],
    mlp_val: list[float],
    linear_train: float,
    linear_val: float,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    epochs = np.arange(1, len(mlp_train) + 1)
    # Validation en premier puis train au-dessus : évite de masquer la courbe train
    # quand les deux séries sont quasi identiques.
    ax.plot(
        epochs,
        mlp_val,
        marker="o",
        color="tab:cyan",
        linewidth=2,
        alpha=0.8,
        label="MLP validation (résidus)",
        zorder=2,
    )
    ax.plot(
        epochs,
        mlp_train,
        marker="o",
        markersize=5,
        markerfacecolor="white",
        markeredgewidth=1.5,
        color="tab:blue",
        linestyle="--",
        linewidth=2,
        label="MLP train (résidus)",
        zorder=3,
    )

    if not math.isnan(linear_train):
        ax.axhline(
            linear_train, color="tab:orange", linestyle="--", label="Linéaire train"
        )
    if not math.isnan(linear_val):
        ax.axhline(
            linear_val, color="tab:red", linestyle=":", label="Linéaire validation"
        )

    ax.set_xlabel("Epoch")
    ax.set_ylabel("MSE résiduelle (espace normalisé)")
    ax.set_title("Training vs validation loss avec 90 000 expériences")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=160, bbox_inches="tight")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[15, 45000, 90000])
    parser.add_argument("--chunk-size", type=int, default=5000)
    parser.add_argument("--mlp-epochs", type=int, default=50)
    parser.add_argument("--k-folds", type=int, default=5)  
    parser.add_argument("--n-test", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT.parent / "figures" / "migration"
    )
    parser.add_argument(
        "--work-dir", type=Path, default=ROOT.parent / "data" / "synthetic_migration"
    )
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    sizes = sorted(set(args.sizes))
    if 90000 not in sizes:
        raise ValueError("La cross-validation est faite sur 90 000 expériences.")

    cfg = load_config("ml")
    phys_cfg = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg = cfg["synth"]["generation"]

    display_cfg = cfg["display"]
    n_steps_pred = int(display_cfg["n_steps_pred"])
    r_max = float(phys_cfg["R"])
    r_min = float(phys_cfg["center_radius"])
    v_stop = float(phys_cfg["v_stop"])
    v_scale = float(gen_cfg.get("v_max", 1.0))

    n_exp = 90000
    data_dir = args.work_dir / f"n_{n_exp}"

    paths = _generate_chunks(
        out_dir=data_dir,
        n_trajectories=n_exp,
        chunk_size=args.chunk_size,
        phys_cfg=phys_cfg,
        gen_cfg=gen_cfg,
        seed=args.seed,
    )

    rng = np.random.default_rng(args.seed)
    rng.shuffle(paths)

    k = args.k_folds
    folds = np.array_split(paths, k)

    test_cases = _build_test_cases(
        args.n_test, phys_cfg, gen_cfg, seed=args.seed + 1000
    )

    rmse_linear_all = []
    rmse_mlp_all = []

    # =========================
    # K-FOLD LOOP
    # =========================
    for i in range(k):
        print(f"\n=== Fold {i+1}/{k} ===")

        val_paths = list(folds[i])
        train_paths = [p for j in range(k) if j != i for p in folds[j]]

        # ---- SCALERS (train only)
        scaler_X, scaler_y = _fit_scalers(train_paths)

        # ---- TRAIN
        linear = _train_linear(train_paths, scaler_X, scaler_y)
        mlp, _, _ = _train_mlp_with_history(
            train_paths, val_paths, scaler_X, scaler_y, args.mlp_epochs, seed=args.seed
        )

        # ---- EVAL (sur test indépendant)
        rmse_lin = _evaluate_rmse(
            linear, test_cases, n_steps_pred, r_max, r_min, v_stop, v_scale
        )
        rmse_mlp = _evaluate_rmse(
            mlp, test_cases, n_steps_pred, r_max, r_min, v_stop, v_scale
        )

        rmse_linear_all.append(rmse_lin["rmse_r"])
        rmse_mlp_all.append(rmse_mlp["rmse_r"])

        print(f"Linéaire RMSE_r: {rmse_lin['rmse_r']:.6f}")
        print(f"MLP RMSE_r:      {rmse_mlp['rmse_r']:.6f}")

    # =========================
    # Résultats globaux
    # =========================
    lin_mean = np.mean(rmse_linear_all)
    lin_std = np.std(rmse_linear_all)

    mlp_mean = np.mean(rmse_mlp_all)
    mlp_std = np.std(rmse_mlp_all)

    print("\n=== CROSS-VALIDATION RESULTS ===")
    print(f"Linéaire : mean={lin_mean:.6f}, std={lin_std:.6f}")
    print(f"MLP      : mean={mlp_mean:.6f}, std={mlp_std:.6f}")

    # =========================
    # Plot résumé
    # =========================
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))

    ax.bar(
        ["Linéaire", "MLP"], [lin_mean, mlp_mean], yerr=[lin_std, mlp_std], capsize=5
    )

    ax.set_ylabel("RMSE rayon")
    ax.set_title(f"{k}-Fold Cross Validation avec 90 000 expériences")
    ax.grid(True, axis="y", alpha=0.3)

    out_file = args.output_dir / "cv_results.png"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=160, bbox_inches="tight")

    print(f"\nFigure sauvegardée : {out_file}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
