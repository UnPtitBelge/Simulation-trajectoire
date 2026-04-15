"""Étude d'ablation des features ML — justification empirique des 9 features.

Ce script entraîne LinearStepModel avec quatre sous-ensembles croissants de
features en entrée et mesure la dégradation de performance à chaque retrait.
Il répond à la question : pourquoi ne pas se limiter aux 5 features de base ?

Sous-ensembles comparés
─────────────────────────────────────────────────────────────────────────────
  A. Base        : (r, cos θ, sin θ, vr, vθ)                        — 5 features
  B. + Centrifuge: + vθ²/r                                           — 6 features
  C. + Coriolis  : + vr·vθ/r                                         — 7 features
  D. Complet     : + sin θ·vθ/r, cos θ·vθ/r (couplages angulaires)  — 9 features

Justification physique :
  - vθ²/r  apparaît directement dans dvr/dt → la LR ne peut pas l'apprendre
    sans ce produit explicite
  - vr·vθ/r (Coriolis) idem dans dvθ/dt
  - sin θ·vθ/r et cos θ·vθ/r permettent de prédire Δcos θ et Δsin θ
    sans faire tourner l'angle, évitant les oscillations récursives

Métriques
──────────
  - val_loss (MSE normalisé) : mesurée sur un chunk de validation
  - MAE(r) médiane sur N_TEST trajectoires de test
  - Longueur de trajectoire prédite vs vérité terrain (proxy de stabilité)

Prérequis : chunks dans data/synthetic/ (lancer generate_data.py).

Usage :
    python src/scripts/ablation_features.py
    python src/scripts/ablation_features.py --n-chunks 20
    python src/scripts/ablation_features.py --output figures/ablation.png --csv results/ablation.csv
    python src/scripts/ablation_features.py --no-plot
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import (
    N_FEATURES, LinearStepModel, _clip_state, features_to_state, state_to_features,
)
from ml.predict import predict_trajectory
from physics.cone import compute_cone
from scripts.generate_data import _sample_initial_conditions
from utils.angle import v0_dir_to_vr_vtheta


# ── Définition des sous-ensembles de features ────────────────────────────────

SUBSETS = [
    {
        "name":    "A — Base (5)",
        "indices": [0, 1, 2, 3, 4],
        "desc":    "r, cos θ, sin θ, vr, vθ",
        "color":   "tomato",
    },
    {
        "name":    "B — + Centrifuge (6)",
        "indices": [0, 1, 2, 3, 4, 5],
        "desc":    "+ vθ²/r",
        "color":   "darkorange",
    },
    {
        "name":    "C — + Coriolis (7)",
        "indices": [0, 1, 2, 3, 4, 5, 6],
        "desc":    "+ vr·vθ/r",
        "color":   "steelblue",
    },
    {
        "name":    "D — Complet (9)",
        "indices": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "desc":    "+ sin θ·vθ/r, cos θ·vθ/r",
        "color":   "seagreen",
    },
]


# ── Modèle d'ablation ─────────────────────────────────────────────────────────


class _AblationLinearModel:
    """LinearStepModel avec sous-ensemble de features en entrée.

    Même algorithme que LinearStepModel (Ridge, équations normales) mais
    n'utilise qu'un sous-ensemble de features en entrée. La sortie est
    toujours le résidu en espace 9-features (scalé par scaler_y indépendant).
    """

    def __init__(self, feature_indices: list[int], alpha: float = 1e-3) -> None:
        self.feature_indices = np.array(feature_indices)
        self.alpha = alpha
        n = len(feature_indices)
        self._XtX = np.zeros((n + 1, n + 1))
        self._Xty = np.zeros((n + 1, N_FEATURES))
        self._W:   np.ndarray | None = None
        self.scaler_X: StandardScaler = StandardScaler()
        self.scaler_y: StandardScaler = StandardScaler()
        self._fitted = False

    def partial_fit(self, X_full: np.ndarray, y_full: np.ndarray) -> None:
        """X_full, y_full : (N, N_FEATURES) features complètes."""
        X        = X_full[:, self.feature_indices]
        residuals = y_full - X_full
        if not self._fitted:
            self.scaler_X.fit(X)
            self.scaler_y.fit(residuals)
            self._fitted = True
        Xs = self.scaler_X.transform(X)
        ys = self.scaler_y.transform(residuals)
        Xb = np.hstack([Xs, np.ones((Xs.shape[0], 1), dtype=Xs.dtype)])
        self._XtX += Xb.T @ Xb
        self._Xty += Xb.T @ ys
        self._W = None

    def _finalize(self) -> None:
        n = len(self.feature_indices)
        A = self._XtX.copy()
        A[:n, :n] += self.alpha * np.eye(n)
        self._W = np.linalg.solve(A, self._Xty)

    def val_loss(self, X_full: np.ndarray, y_full: np.ndarray) -> float:
        """MSE normalisé — calculé sur tous les résidus (9 dimensions)."""
        if self._W is None:
            self._finalize()
        X         = X_full[:, self.feature_indices]
        residuals = y_full - X_full
        Xs = self.scaler_X.transform(X)
        Xb = np.hstack([Xs, np.ones((Xs.shape[0], 1), dtype=Xs.dtype)])
        ys = self.scaler_y.transform(residuals)
        pred = Xb @ self._W
        return float(np.mean((pred - ys) ** 2))

    def predict_step(self, state: np.ndarray) -> np.ndarray:
        """Interface compatible avec predict_trajectory."""
        if not self._fitted:
            raise RuntimeError("Modèle non entraîné")
        if self._W is None:
            self._finalize()
        feat = state_to_features(state).reshape(1, -1)
        feat_sub = feat[:, self.feature_indices]
        feat_sub_s = self.scaler_X.transform(feat_sub)
        Xb = np.hstack([feat_sub_s, [[1.0]]])
        delta_s = Xb @ self._W
        delta = self.scaler_y.inverse_transform(delta_s)[0]
        if np.isnan(delta).any() or np.isinf(delta).any():
            raise RuntimeError(f"Prédiction instable à state={state}")
        return _clip_state(features_to_state(feat[0] + delta))


# ── Chargement des chunks ─────────────────────────────────────────────────────


def load_chunks(chunk_paths: list[Path]) -> list[tuple[np.ndarray, np.ndarray]]:
    """Charge les chunks et convertit en paires (X_feat, y_feat)."""
    pairs = []
    for p in chunk_paths:
        data = np.load(p)
        X = state_to_features(data["X"].astype(np.float32))
        y = state_to_features(data["y"].astype(np.float32))
        pairs.append((X, y))
    return pairs


# ── Entraînement + évaluation ─────────────────────────────────────────────────


def evaluate_subset(
    subset: dict,
    train_pairs: list[tuple[np.ndarray, np.ndarray]],
    val_pair:    tuple[np.ndarray, np.ndarray],
    test_cases:  list[tuple[np.ndarray, np.ndarray]],  # (init_state, ref_traj)
    phys:        dict,
    n_steps_pred: int,
) -> dict:
    """Entraîne un modèle d'ablation et mesure ses performances.

    Retourne un dict avec val_loss, mae_r, mae_total, n_pred_mean, n_true_mean.
    """
    model = _AblationLinearModel(subset["indices"])

    for X, y in train_pairs:
        model.partial_fit(X, y)

    val_loss = model.val_loss(*val_pair)

    mae_rs: list[float] = []
    mae_tots: list[float] = []
    n_preds:  list[int]  = []
    n_trues:  list[int]  = []

    for init_state, ref_traj in test_cases:
        try:
            pred = predict_trajectory(
                model, init_state, n_steps_pred,
                r_max=phys["R"], r_min=phys["center_radius"], v_stop=phys["v_stop"],
            )
        except RuntimeError:
            continue  # Prédiction instable — ce cas est compté dans la stabilité

        n = min(len(pred), len(ref_traj))
        if n == 0:
            continue
        diff = np.abs(pred[:n] - ref_traj[:n])
        mae_rs.append(float(diff[:, 0].mean()))
        mae_tots.append(float(diff.mean()))
        n_preds.append(len(pred))
        n_trues.append(len(ref_traj))

    return {
        "name":       subset["name"],
        "n_features": len(subset["indices"]),
        "val_loss":   val_loss,
        "mae_r":      float(np.median(mae_rs))  if mae_rs  else float("nan"),
        "mae_total":  float(np.median(mae_tots)) if mae_tots else float("nan"),
        "n_pred":     float(np.mean(n_preds)) if n_preds else float("nan"),
        "n_true":     float(np.mean(n_trues)) if n_trues else float("nan"),
        "n_stable":   len(mae_rs),
    }


# ── Génération du jeu de test ─────────────────────────────────────────────────


def generate_test_cases(
    n: int, phys: dict, gen_cfg: dict, rng: np.random.Generator, n_steps: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Génère n couples (état initial, trajectoire de référence)."""
    merged_cfg = {**phys, **gen_cfg}
    r0s, theta0s, vr0s, vth0s = _sample_initial_conditions(n, merged_cfg, rng)
    cases = []
    for r0, theta0, vr0, vth0 in zip(r0s, theta0s, vr0s, vth0s):
        ref = compute_cone(
            r0=r0, theta0=theta0, vr0=vr0, vtheta0=vth0,
            R=phys["R"], depth=phys["depth"],
            friction=phys["friction"], g=phys["g"],
            dt=phys["dt"], n_steps=n_steps,
            center_radius=phys["center_radius"],
        )
        if len(ref) < 10:
            continue
        init = np.array([r0, theta0, vr0, vth0])
        cases.append((init, ref))
    return cases


# ── Visualisation ─────────────────────────────────────────────────────────────


def plot_ablation(results: list[dict], output: Path | None) -> None:
    """Trois panneaux : val_loss, MAE(r), stabilité (trajectoires stables)."""
    names  = [r["name"] for r in results]
    colors = [s["color"] for s in SUBSETS]

    val_losses = [r["val_loss"] for r in results]
    mae_rs     = [r["mae_r"]    for r in results]
    n_stables  = [r["n_stable"] for r in results]
    n_total    = results[0]["n_stable"] + (results[0]["n_true"] - results[0]["n_stable"])  # approximatif

    x = np.arange(len(results))
    width = 0.55

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle(
        "Ablation des features — LinearStepModel\n"
        "Effet de l'ajout progressif des produits croisés physiques",
        fontsize=12, fontweight="bold",
    )

    # ── Val loss ─────────────────────────────────────────────────────────
    ax = axes[0]
    bars = ax.bar(x, val_losses, width, color=colors, alpha=0.85, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels([r["name"].split(" — ")[0] for r in results])
    ax.set_title("Val loss (MSE normalisé)")
    ax.set_ylabel("MSE (espace normalisé)")
    ax.grid(True, axis="y", alpha=0.3)
    for bar, val in zip(bars, val_losses):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
                f"{val:.4f}", ha="center", va="bottom", fontsize=9)

    # ── MAE(r) ───────────────────────────────────────────────────────────
    ax = axes[1]
    bars = ax.bar(x, mae_rs, width, color=colors, alpha=0.85, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels([r["name"].split(" — ")[0] for r in results])
    ax.set_title("MAE(r) médiane sur les trajectoires de test (m)")
    ax.set_ylabel("MAE r (m)")
    ax.grid(True, axis="y", alpha=0.3)
    for bar, val in zip(bars, mae_rs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
                f"{val:.4f}", ha="center", va="bottom", fontsize=9)

    # ── Stabilité ────────────────────────────────────────────────────────
    ax = axes[2]
    ax.bar(x, n_stables, width, color=colors, alpha=0.85, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels([r["name"].split(" — ")[0] for r in results])
    ax.set_title("Trajectoires stables (sans NaN/Inf)")
    ax.set_ylabel("Nombre de trajectoires stables")
    ax.grid(True, axis="y", alpha=0.3)

    # Légende détaillée
    legend_lines = [
        plt.Line2D([0], [0], color=s["color"], linewidth=6, alpha=0.85,
                   label=f"{s['name']}\n({s['desc']})")
        for s in SUBSETS
    ]
    fig.legend(handles=legend_lines, loc="lower center", ncol=4,
               bbox_to_anchor=(0.5, -0.18), fontsize=8, framealpha=0.9)

    plt.tight_layout()

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"\nFigure sauvegardée : {output}")

    plt.show()


def print_table(results: list[dict]) -> None:
    print(f"\n{'═' * 72}")
    print(f"  {'Sous-ensemble':<28}  {'n_feat':>6}  {'val_loss':>10}  {'MAE r':>10}  {'stables':>8}")
    print(f"{'─' * 72}")
    for r in results:
        print(f"  {r['name']:<28}  {r['n_features']:>6}  {r['val_loss']:>10.5f}"
              f"  {r['mae_r']:>10.5f}  {r['n_stable']:>8}")
    print(f"{'═' * 72}\n")


def save_csv(results: list[dict], csv_path: Path) -> None:
    import csv as csv_module
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        w = csv_module.DictWriter(f, fieldnames=["name", "n_features", "val_loss", "mae_r", "mae_total", "n_pred", "n_stable"])
        w.writeheader()
        for r in results:
            w.writerow({k: r[k] for k in ("name", "n_features", "val_loss", "mae_r", "mae_total", "n_pred", "n_stable")})
    print(f"CSV sauvegardé : {csv_path}")


# ── Main ─────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ablation des features ML — compare 4 sous-ensembles de features."
    )
    parser.add_argument("--n-chunks",  type=int, default=9999,
                        help="Chunks d'entraînement (défaut : tous les chunks disponibles)")
    parser.add_argument("--n-test",    type=int, default=500,
                        help="Trajectoires de test (défaut : 500)")
    parser.add_argument("--seed",      type=int, default=42)
    parser.add_argument("--output",    type=Path, default=ROOT.parent / "figures" / "features.png",
                        help="Chemin de sauvegarde de la figure (défaut : <projet>/figures/features.png)")
    parser.add_argument("--csv",       type=Path, default=ROOT.parent / "results" / "features.csv",
                        help="Chemin de sauvegarde du CSV (défaut : <projet>/results/features.csv)")
    parser.add_argument("--no-plot",   action="store_true",
                        help="Mode batch sans fenêtre graphique")
    args = parser.parse_args()

    cfg      = load_config("ml")
    phys     = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg  = cfg["synth"]["generation"]
    data_dir = ROOT / cfg["paths"]["synth_data_dir"]

    all_chunks = sorted(data_dir.glob("chunk_*.npz"))
    if not all_chunks:
        print(f"⚠  Aucun chunk dans {data_dir} — lancez generate_data.py d'abord")
        sys.exit(1)

    n_avail = len(all_chunks)
    n_train = min(args.n_chunks, n_avail - 1)
    if n_train < 1:
        print(f"⚠  Pas assez de chunks ({n_avail}) — au moins 2 nécessaires (1 train + 1 val)")
        sys.exit(1)

    print(f"\nChargement de {n_train} chunks d'entraînement + 1 chunk de validation...")
    train_pairs = load_chunks(all_chunks[:n_train])
    val_pair    = load_chunks([all_chunks[n_train]])[0]

    print(f"Génération de {args.n_test} trajectoires de test (seed={args.seed})...")
    rng = np.random.default_rng(args.seed)
    n_steps_pred = cfg["display"]["n_steps_pred"]
    test_cases = generate_test_cases(args.n_test, phys, gen_cfg, rng, n_steps_pred)
    print(f"  → {len(test_cases)} trajectoires de test valides\n")

    results = []
    for subset in SUBSETS:
        print(f"Entraînement  {subset['name']}  ({len(subset['indices'])} features)...")
        res = evaluate_subset(subset, train_pairs, val_pair, test_cases, phys, n_steps_pred)
        results.append(res)
        print(f"  val_loss={res['val_loss']:.5f}  MAE(r)={res['mae_r']:.5f} m"
              f"  stables={res['n_stable']}/{len(test_cases)}")

    print_table(results)

    save_csv(results, args.csv)

    if not args.no_plot:
        plot_ablation(results, args.output)
    else:
        plt.close("all")
