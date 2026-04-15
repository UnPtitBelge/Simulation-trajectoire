"""Entraîne les modèles directs CI → trajectoire sur données synthétiques.

Paradigme direct :
  Entrée  : (r0, cos θ0, sin θ0, vr0, vθ0)   — 5 scalaires (état initial encodé)
  Sortie  : trajectoire polaire aplatie
            (r0, θ0, vr0, vθ0, r1, θ1, …)     — 4 × target_len scalaires

Modèles entraînés pour 4 contextes d'entraînement :
  1pct, 10pct, 50pct, 100pct

Sauvegardés dans data/models/ :
  direct_linear_1pct.pkl  direct_mlp_1pct.pkl
  direct_linear_10pct.pkl direct_mlp_10pct.pkl
  direct_linear_50pct.pkl direct_mlp_50pct.pkl
  direct_linear_100pct.pkl direct_mlp_100pct.pkl

Chaque .pkl est un dict :
  {
    "model":       Ridge | MLPRegressor,
    "scaler_X":    StandardScaler (fit sur les CI),
    "target_len":  int,
    "context":     str ("1pct", …),
    "model_type":  "Ridge" | "MLP",
    "n_train":     int,
    "mae_r_train": float,  # MAE r sur le train (en mètres)
  }

Usage :
    python src/scripts/train_direct_models.py
    python src/scripts/train_direct_models.py --n-trajectories 20000
    python src/scripts/train_direct_models.py --max-steps 500
    python src/scripts/train_direct_models.py --workers 4
    python src/scripts/train_direct_models.py --no-save   # dry-run
"""

import argparse
import gc
import os
import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from physics.cone import compute_cone
from scripts.generate_data import _sample_initial_conditions


# ── Génération de trajectoires complètes ──────────────────────────────────────


def generate_trajectories(
    n: int,
    phys_cfg: dict,
    gen_cfg: dict,
    rng: np.random.Generator,
) -> list[np.ndarray]:
    """Génère n trajectoires complètes en (r, θ, vr, vθ).

    Retourne une liste d'arrays de forme (T, 4) — longueur T variable.
    Les trajectoires plus courtes que min_steps sont ignorées.
    """
    merged = {**phys_cfg, **gen_cfg}
    r0s, theta0s, vr0s, vth0s = _sample_initial_conditions(n, merged, rng)
    min_steps = gen_cfg.get("min_steps", 50)

    # Paramètres physiques optionnels
    rolling            = bool(phys_cfg.get("rolling", False))
    rolling_resistance = float(phys_cfg.get("rolling_resistance", 0.0))
    drag_coeff         = float(phys_cfg.get("drag_coeff", 0.0))

    trajs: list[np.ndarray] = []
    for i in range(n):
        traj = compute_cone(
            r0=float(r0s[i]),
            theta0=float(theta0s[i]),
            vr0=float(vr0s[i]),
            vtheta0=float(vth0s[i]),
            R=float(phys_cfg["R"]),
            depth=float(phys_cfg["depth"]),
            friction=float(phys_cfg["friction"]),
            g=float(phys_cfg["g"]),
            dt=float(phys_cfg["dt"]),
            n_steps=int(phys_cfg["n_steps"]),
            rolling=rolling,
            rolling_resistance=rolling_resistance,
            drag_coeff=drag_coeff,
        )
        if len(traj) >= max(2, min_steps):
            trajs.append(traj.astype(np.float32))

    return trajs


# ── Encodage CI → features ─────────────────────────────────────────────────────


def ci_to_features(state: np.ndarray) -> np.ndarray:
    """(r, θ, vr, vθ) → (r, cos θ, sin θ, vr, vθ) — 5 features pour les CI.

    Encode θ comme (cos θ, sin θ) pour éviter la discontinuité à ±π et
    pour que la régression linéaire puisse capturer les symétries polaires.
    """
    r, theta, vr, vtheta = float(state[0]), float(state[1]), float(state[2]), float(state[3])
    return np.array([r, np.cos(theta), np.sin(theta), vr, vtheta], dtype=np.float32)


# ── Construction du dataset ────────────────────────────────────────────────────


def choose_target_len(trajs: list[np.ndarray], max_steps: int) -> int:
    """Longueur cible = médiane des longueurs, plafonnée à max_steps."""
    lengths = [len(t) for t in trajs]
    median = int(np.median(lengths))
    return min(median, max_steps)


def build_dataset(
    trajs: list[np.ndarray],
    target_len: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Construit X (5 features CI) et Y (trajectoire aplatie 4 × target_len).

    Les trajectoires plus courtes que target_len sont ignorées.
    Y contient la trajectoire depuis t=0 inclus :
      Y = [r0, θ0, vr0, vθ0, r1, θ1, vr1, vθ1, …, r_{T-1}, …]
    """
    X_list: list[np.ndarray] = []
    Y_list: list[np.ndarray] = []

    for traj in trajs:
        if len(traj) < target_len:
            continue
        x = ci_to_features(traj[0])
        y = traj[:target_len].flatten()       # (4 × target_len,)
        X_list.append(x)
        Y_list.append(y)

    if not X_list:
        n_out = target_len * 4
        return np.empty((0, 5), np.float32), np.empty((0, n_out), np.float32)

    return np.array(X_list, dtype=np.float32), np.array(Y_list, dtype=np.float32)


# ── Entraînement ───────────────────────────────────────────────────────────────


def train_ridge(
    X_train: np.ndarray,
    Y_train: np.ndarray,
    scaler_X: StandardScaler,
    context: str,
) -> dict:
    """Entraîne Ridge et retourne le dict de sauvegarde."""
    target_len = Y_train.shape[1] // 4

    X_s = scaler_X.transform(X_train)
    model = Ridge(alpha=1.0)
    model.fit(X_s, Y_train)

    Y_pred_train = model.predict(X_s)
    # MAE sur r uniquement (indices 0, 4, 8, …)
    r_true = Y_train[:, 0::4]
    r_pred = Y_pred_train[:, 0::4]
    mae_r  = float(mean_absolute_error(r_true.flatten(), r_pred.flatten()))

    print(f"  Ridge [{context}] — {len(X_train)} traj, target_len={target_len}, MAE r={mae_r:.5f} m")
    return {
        "model":       model,
        "scaler_X":    scaler_X,
        "target_len":  target_len,
        "context":     context,
        "model_type":  "Ridge",
        "n_train":     len(X_train),
        "mae_r_train": mae_r,
    }


def train_mlp(
    X_train: np.ndarray,
    Y_train: np.ndarray,
    scaler_X: StandardScaler,
    context: str,
) -> dict:
    """Entraîne MLPRegressor avec early stopping et retourne le dict de sauvegarde."""
    target_len = Y_train.shape[1] // 4

    X_s = scaler_X.transform(X_train)

    # early_stopping nécessite validation_fraction > 0 et au moins 2 exemples
    use_early = len(X_train) >= 10
    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        learning_rate_init=1e-3,
        alpha=0.01,
        max_iter=500,
        early_stopping=use_early,
        validation_fraction=0.1 if use_early else 0.0,
        n_iter_no_change=15,
        random_state=42,
    )
    model.fit(X_s, Y_train)
    n_iter = model.n_iter_

    Y_pred_train = model.predict(X_s)
    r_true = Y_train[:, 0::4]
    r_pred = Y_pred_train[:, 0::4]
    mae_r  = float(mean_absolute_error(r_true.flatten(), r_pred.flatten()))

    print(f"  MLP  [{context}] — {len(X_train)} traj, target_len={target_len}, "
          f"iters={n_iter}, MAE r={mae_r:.5f} m")
    return {
        "model":       model,
        "scaler_X":    scaler_X,
        "target_len":  target_len,
        "context":     context,
        "model_type":  "MLP",
        "n_train":     len(X_train),
        "mae_r_train": mae_r,
        "n_iter":      n_iter,
    }


# ── Main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entraîne les modèles directs CI→trajectoire sur données synthétiques."
    )
    parser.add_argument(
        "--n-trajectories", type=int, default=50_000,
        help="Nombre total de trajectoires à générer pour le contexte 100pct (défaut : 50000).",
    )
    parser.add_argument(
        "--max-steps", type=int, default=1_000,
        help="Longueur max de la trajectoire cible en pas (défaut : 1000, soit 10 s à dt=0.01).",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=None,
        help="Dossier de sauvegarde des .pkl (défaut : data/models/ de la config).",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Mode dry-run : entraîne mais ne sauvegarde pas les modèles.",
    )
    args = parser.parse_args()

    cfg        = load_config("ml")
    phys_cfg   = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg    = cfg["synth"]["generation"]
    ctx_names  = cfg["synth"]["contexts"]["names"]
    ctx_fracs  = cfg["synth"]["contexts"]["fractions"]
    models_dir = (
        args.output_dir
        if args.output_dir is not None
        else ROOT / cfg["paths"]["models_dir"]
    )
    models_dir.mkdir(parents=True, exist_ok=True)

    n_total = args.n_trajectories
    max_steps = args.max_steps

    print(f"\n{'═' * 60}")
    print(f"  Modèles directs CI → trajectoire")
    print(f"  {n_total:,} trajectoires (100pct), max_steps={max_steps}")
    print(f"  Contextes : {list(zip(ctx_names, ctx_fracs))}")
    print(f"{'═' * 60}\n")

    # ── Génération du jeu complet (100pct) ────────────────────────────────────
    print(f"Génération de {n_total:,} trajectoires synthétiques (seed=0)...")
    rng = np.random.default_rng(0)
    all_trajs = generate_trajectories(n_total, phys_cfg, gen_cfg, rng)
    n_generated = len(all_trajs)
    lengths = [len(t) for t in all_trajs]
    print(f"  {n_generated:,} trajectoires gardées "
          f"(lon. : méd={int(np.median(lengths))}, "
          f"p5={int(np.percentile(lengths, 5))}, "
          f"p95={int(np.percentile(lengths, 95))})")
    gc.collect()

    # target_len partagé pour tous les contextes → même output dimension
    target_len = choose_target_len(all_trajs, max_steps)
    print(f"  target_len = {target_len} pas ({target_len * cfg['physics']['dt']:.1f} s)\n")

    # Filtrage — exclure les trajectoires trop courtes
    all_trajs_ok = [t for t in all_trajs if len(t) >= target_len]
    print(f"  {len(all_trajs_ok):,}/{n_generated:,} trajectoires ≥ target_len")

    # Scaler commun, fitté sur 100pct
    print("\nCalibration du scaler sur 100pct...")
    X_all, Y_all = build_dataset(all_trajs_ok, target_len)
    if len(X_all) == 0:
        print("⚠  Aucune trajectoire assez longue — réduire --max-steps.")
        return
    scaler_X = StandardScaler().fit(X_all)
    print(f"  Scaler fitté sur {len(X_all):,} trajectoires")
    del Y_all  # libérer la RAM
    gc.collect()

    # ── Entraînement par contexte ──────────────────────────────────────────────
    print()
    results: dict[str, dict] = {}

    for ctx_name, ctx_frac in zip(ctx_names, ctx_fracs):
        n_ctx = max(1, int(len(all_trajs_ok) * ctx_frac))
        trajs_ctx = all_trajs_ok[:n_ctx]
        X_ctx, Y_ctx = build_dataset(trajs_ctx, target_len)

        print(f"[{ctx_name}] — {len(X_ctx):,} trajectoires d'entraînement")

        if len(X_ctx) == 0:
            print(f"  ⚠  Aucune trajectoire valide pour {ctx_name} — ignoré.")
            continue

        # Ridge
        ridge_data = train_ridge(X_ctx, Y_ctx, scaler_X, ctx_name)
        results[f"direct_linear_{ctx_name}"] = ridge_data

        # MLP
        mlp_data = train_mlp(X_ctx, Y_ctx, scaler_X, ctx_name)
        results[f"direct_mlp_{ctx_name}"] = mlp_data

        del X_ctx, Y_ctx
        gc.collect()
        print()

    # ── Sauvegarde ────────────────────────────────────────────────────────────
    if args.no_save:
        print("Mode --no-save : modèles non sauvegardés.")
    else:
        print("Sauvegarde des modèles...")
        for fname, data in results.items():
            path = models_dir / f"{fname}.pkl"
            with open(path, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"  ✓ {path.name}  "
                  f"(n_train={data['n_train']}, "
                  f"MAE r_train={data['mae_r_train']:.5f} m)")

    print(f"\n{'═' * 60}")
    print(f"  {len(results)} modèles traités — dossier : {models_dir}")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
