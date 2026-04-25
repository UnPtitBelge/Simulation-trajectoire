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

    fig, ax = plt.subplots(figsize=(7, 5))

    # Données
    data = [rmse_linear_all, rmse_mlp_all]

    # Boxplot (distribution complète)
    box = ax.boxplot(
    data,
    labels=["Linéaire", "MLP"],
    patch_artist=True,
    widths=0.5,
)

# Couleurs
    colors = ["tab:orange", "tab:blue"]
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)

# Points individuels (folds visibles)
    for i, values in enumerate(data, start=1):
        x = np.random.normal(i, 0.04, size=len(values))  # jitter
        ax.scatter(x, values, color="black", s=30, zorder=3)

    # Moyenne + std affichées explicitement
    means = [np.mean(d) for d in data]
    stds = [np.std(d) for d in data]

    for i, (mean, std) in enumerate(zip(means, stds), start=1):
        ax.errorbar(
        i,
        mean,
        yerr=std,
        fmt="o",
        color="black",
        capsize=6,
        label="Moyenne ± écart-type" if i == 1 else None,
    )

# Texte statistique sur le graphe
    textstr = (
    f"Linéaire:\n"
    f"  μ = {lin_mean:.5f}\n"
    f"  σ = {lin_std:.5f}\n"
    f"  Var = {lin_std**2:.6f}\n\n"
    f"MLP:\n"
    f"  μ = {mlp_mean:.5f}\n"
    f"  σ = {mlp_std:.5f}\n"
    f"  Var = {mlp_std**2:.6f}"
)

    ax.text(
    1.55,
    max(max(rmse_linear_all), max(rmse_mlp_all)) * 0.95,
    textstr,
    fontsize=10,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

    ax.set_ylabel("RMSE rayon")
    ax.set_title(f"{k}-Fold Cross Validation (90 000 expériences)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()

    out_file = args.output_dir / "cv_results_improved.png"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file, dpi=160, bbox_inches="tight")

    print(f"\nFigure améliorée sauvegardée : {out_file}")


if __name__ == "__main__":
    main()
