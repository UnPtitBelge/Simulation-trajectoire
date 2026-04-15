"""MLP direct CI → trajectoire (version corrigée).

Reproduction pédagogique du modèle original de la branche main, avec 5 corrections :

  1. Séparation train/test   : une expérience tenue à l'écart (leave-one-out).
  2. Centrage par endpoint   : médiane des 15 dernières positions par expérience
                               (position d'arrêt ≈ centre du cône), avec rejet des
                               outliers par MAD.
  3. Normalisation des CI    : StandardScaler fitté sur le train uniquement.
  4. Troncature à la médiane : toutes les trajectoires sont tronquées à la longueur
                               médiane du jeu d'entraînement (vs. le minimum qui
                               jetait la quasi-totalité des données longues).
  5. Évaluation correcte     : MSE / MAE sur le jeu de test + tracé de la trajectoire
                               de l'expérience tenue à l'écart.

Paradigme conservé (intentionnellement simple) :
  Entrée  : conditions initiales (x0, y0, vx0, vy0)  — 4 scalaires
  Sortie  : trajectoire aplatie (x1,y1, x2,y2, …)    — 2 × target_len scalaires

Différences par rapport à la version main :
  - hidden_layer_sizes=(64, 32) au lieu de (100,) : réduit le sur-apprentissage
    et correspond à la capacité réellement utile pour 4 entrées → 2×N sorties.
  - max_iter=500, early_stopping=True, validation_fraction=0.1 :
    arrête l'entraînement quand la perte de validation cesse de baisser.
  - random_state fixé pour la reproductibilité.

Limites connues de ce paradigme (non corrigées ici, voir ml/models.py) :
  - Taille de sortie fixe : impossible de prédire au-delà de target_len pas.
  - Le MLP ne capte pas mieux la physique rotationnelle que la LR avec 4 entrées
    brutes — pour cela, il faudrait des features polaires + produits croisés.

Usage :
    python src/scripts/demo_mlp_direct.py
    python src/scripts/demo_mlp_direct.py --test-id 5
    python src/scripts/demo_mlp_direct.py --no-plot
"""

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config


# ── Chargement des données ─────────────────────────────────────────────────────


def parse_tracking_csv(csv_path: Path) -> dict[int, list[dict]]:
    """Lit le CSV de tracking et retourne {expID: [lignes triées par temps]}."""
    grouped: dict[int, list[dict]] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            exp_id = int(row["expID"])
            grouped.setdefault(exp_id, []).append({
                "temps":  float(row["temps"]),
                "x":      float(row["x"]),
                "y":      float(row["y"]),
                "speedX": float(row["speedX"]),
                "speedY": float(row["speedY"]),
            })
    for rows in grouped.values():
        rows.sort(key=lambda r: r["temps"])
    return grouped


# ── Correction 2 : centrage par endpoint ──────────────────────────────────────


def compute_centers(grouped: dict[int, list[dict]], last_n: int = 15) -> dict[int, tuple[float, float]]:
    """Estime le centre du cône pour chaque expérience depuis sa position d'arrêt.

    Algorithme :
      1. Médiane des `last_n` dernières positions de chaque expérience → endpoint_i
      2. Centre de référence global = médiane de tous les endpoints
      3. Outliers (distance > 2 × MAD) → remplacés par le centre de référence

    Bien supérieur à la médiane globale de tous les points (biaiserait vers les
    trajectoires longues qui passent plus de temps loin du centre).
    """
    raw: dict[int, tuple[float, float]] = {}
    for exp_id, rows in grouped.items():
        tail = rows[-last_n:]
        raw[exp_id] = (
            float(np.median([r["x"] for r in tail])),
            float(np.median([r["y"] for r in tail])),
        )

    exp_ids = list(raw)
    cx_vals = np.array([raw[eid][0] for eid in exp_ids])
    cy_vals = np.array([raw[eid][1] for eid in exp_ids])
    cx_ref  = float(np.median(cx_vals))
    cy_ref  = float(np.median(cy_vals))

    dists  = np.sqrt((cx_vals - cx_ref) ** 2 + (cy_vals - cy_ref) ** 2)
    mad    = float(np.median(np.abs(dists - np.median(dists))))
    thresh = max(2.0 * mad, 50.0)   # au moins 50 px ≈ 3.7 cm @ 1350 px/m

    return {
        eid: raw[eid] if dist <= thresh else (cx_ref, cy_ref)
        for eid, dist in zip(exp_ids, dists)
    }


# ── Correction 4 : troncature à la longueur médiane ───────────────────────────


def choose_target_len(grouped: dict, centers: dict, test_id: int) -> int:
    """Retourne la longueur cible des trajectoires.

    Calculée comme la médiane des trajectoires d'entraînement, puis plafonnée
    à la longueur de la trajectoire de test pour garantir que celle-ci est
    toujours assez longue.
    """
    lengths = [len(rows) for exp_id, rows in grouped.items() if exp_id != test_id]
    median_len = int(np.median(lengths))
    test_len   = len(grouped[test_id])
    return min(median_len, test_len)


# ── Construction du jeu de données ────────────────────────────────────────────


def build_dataset(
    grouped:    dict[int, list[dict]],
    centers:    dict[int, tuple[float, float]],
    test_id:    int,
    target_len: int,
) -> tuple:
    """Construit X (4 CI) et Y (trajectoire aplatie) avec séparation train/test.

    Correction 1 : l'expérience test_id est isolée et jamais vue par le modèle.
    Correction 4 : toutes les trajectoires sont tronquées à target_len ; les
                   expériences plus courtes que target_len sont ignorées.

    Retourne (X_train, Y_train, X_test, Y_test, traj_test_vraie).
    """
    X_train, Y_train = [], []
    X_test: np.ndarray | None = None
    Y_test: np.ndarray | None = None
    traj_test_vraie: np.ndarray | None = None

    for exp_id in sorted(grouped.keys()):
        rows = grouped[exp_id]
        if len(rows) < target_len:
            continue                     # trajectoire trop courte — ignorée

        cx, cy = centers[exp_id]
        ci = [
            rows[0]["x"] - cx,
            rows[0]["y"] - cy,
            rows[0]["speedX"],
            rows[0]["speedY"],
        ]
        traj_xy = [(r["x"] - cx, r["y"] - cy) for r in rows[:target_len]]
        flat    = [coord for pt in traj_xy for coord in pt]

        if exp_id == test_id:
            X_test = np.array([ci],   dtype=np.float32)
            Y_test = np.array([flat], dtype=np.float32)
            traj_test_vraie = np.array(traj_xy, dtype=np.float32)
        else:
            X_train.append(ci)
            Y_train.append(flat)

    if not X_train:
        raise ValueError("Aucune trajectoire d'entraînement valide après filtrage.")
    if X_test is None:
        raise ValueError(f"expID {test_id} introuvable ou trop courte (< {target_len} pas).")

    return (
        np.array(X_train, dtype=np.float32),
        np.array(Y_train, dtype=np.float32),
        X_test,
        Y_test,
        traj_test_vraie,
    )


# ── Visualisation ─────────────────────────────────────────────────────────────


def plot_result(
    traj_vraie:   np.ndarray,
    traj_pred:    np.ndarray,
    loss_curve:   list[float],
    test_id:      int,
    n_train:      int,
    mae_px:       float,
    target_len:   int,
    output:       Path | None,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    fig.suptitle(
        f"MLP direct CI → trajectoire — expID {test_id} (test)\n"
        f"{n_train} expériences d'entraînement · {target_len} pas · MAE = {mae_px:.1f} px",
        fontsize=11, fontweight="bold",
    )

    # ── Panel 1 : trajectoire XY ──────────────────────────────────────────────
    ax = axes[0]
    ax.plot(traj_vraie[:, 0], traj_vraie[:, 1],
            label="Vraie", linewidth=2, color="steelblue")
    ax.plot(traj_pred[:, 0],  traj_pred[:, 1],
            label="Prédite", linewidth=2, linestyle="--", color="crimson")
    ax.scatter([0], [0], s=80, color="black", zorder=5, label="Centre (0,0)")
    ax.set_aspect("equal")
    ax.set_title("Trajectoire XY (pixels centrés)")
    ax.set_xlabel("x (px)")
    ax.set_ylabel("y (px)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ── Panel 2 : r(t) ────────────────────────────────────────────────────────
    ax2 = axes[1]
    r_vraie = np.sqrt(traj_vraie[:, 0] ** 2 + traj_vraie[:, 1] ** 2)
    r_pred  = np.sqrt(traj_pred[:, 0]  ** 2 + traj_pred[:, 1]  ** 2)
    t = np.arange(len(r_vraie))
    ax2.plot(t, r_vraie, label="Vraie",   linewidth=2, color="steelblue")
    ax2.plot(t, r_pred,  label="Prédite", linewidth=2, linestyle="--", color="crimson")
    ax2.fill_between(t, r_vraie, r_pred, alpha=0.15, color="gray", label="|erreur r|")
    ax2.set_title("r(t) — rayon en pixels")
    ax2.set_xlabel("pas (frame)")
    ax2.set_ylabel("r (px)")
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    # ── Panel 3 : courbe de perte (early stopping visible) ───────────────────
    ax3 = axes[2]
    if loss_curve:
        ax3.plot(loss_curve, color="darkorange", linewidth=1.5, label="loss train")
        ax3.set_yscale("log")
        ax3.set_title("Courbe de perte (entraînement)")
        ax3.set_xlabel("itération")
        ax3.set_ylabel("MSE (log)")
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, "loss_curve non disponible",
                 ha="center", va="center", transform=ax3.transAxes)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Figure sauvegardée : {output}")

    plt.show()


# ── Sauvegarde CSV ─────────────────────────────────────────────────────────────


def save_csv(metrics: dict, csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
        writer.writeheader()
        writer.writerow(metrics)
    print(f"CSV sauvegardé : {csv_path}")


# ── Main ───────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MLP direct CI→trajectoire (version corrigée)."
    )
    parser.add_argument("--test-id", type=int, default=None,
                        help="expID réservé au test (défaut : dernier)")
    parser.add_argument("--output",  type=Path,
                        default=ROOT.parent / "figures" / "demo_mlp_direct.png",
                        help="Chemin de la figure (défaut : figures/demo_mlp_direct.png)")
    parser.add_argument("--csv",     type=Path,
                        default=ROOT.parent / "results" / "demo_mlp_direct.csv",
                        help="Chemin du CSV de métriques (défaut : results/demo_mlp_direct.csv)")
    parser.add_argument("--no-plot", action="store_true",
                        help="Mode batch sans fenêtre graphique")
    args = parser.parse_args()

    cfg      = load_config("ml")
    csv_path = ROOT / cfg["paths"]["tracking_data"]

    if not csv_path.exists():
        print(f"⚠  Fichier manquant : {csv_path}")
        sys.exit(1)

    # ── Chargement ────────────────────────────────────────────────────────────
    print("\nChargement du CSV de tracking...")
    grouped = parse_tracking_csv(csv_path)
    all_ids = sorted(grouped.keys())
    print(f"  {len(all_ids)} expériences — IDs : {all_ids}")

    # Correction 1 : choix du jeu de test
    test_id = args.test_id if args.test_id is not None else all_ids[-1]
    if test_id not in all_ids:
        print(f"⚠  expID {test_id} introuvable. IDs disponibles : {all_ids}")
        sys.exit(1)
    print(f"  Test : expID {test_id}   Entraînement : {len(all_ids) - 1} expériences")

    # Correction 2 : centrage par endpoint
    print("\nCalcul des centres par endpoint...")
    centers = compute_centers(grouped)
    for eid, (cx, cy) in centers.items():
        print(f"  expID {eid:2d} → centre ({cx:.1f}, {cy:.1f}) px")

    # Correction 4 : longueur cible = médiane des trajectoires d'entraînement
    target_len = choose_target_len(grouped, centers, test_id)
    print(f"\nLongueur cible (médiane train) : {target_len} pas")

    # ── Construction du dataset ───────────────────────────────────────────────
    # Affiche les expériences trop courtes avant d'appeler build_dataset
    skipped = [
        (eid, len(rows))
        for eid, rows in grouped.items()
        if eid != test_id and len(rows) < target_len
    ]
    if skipped:
        print(f"\n⚠  {len(skipped)} expérience(s) écartée(s) (trop courtes < {target_len} pas) :")
        for eid, n in sorted(skipped):
            print(f"     expID {eid:2d} : {n} pas")

    X_train, Y_train, X_test, Y_test, traj_vraie = build_dataset(
        grouped, centers, test_id, target_len
    )
    print(f"\nDataset : X_train {X_train.shape}  Y_train {Y_train.shape}")
    print(f"          X_test  {X_test.shape}   Y_test  {Y_test.shape}")

    # Correction 3 : normalisation — fitté sur le train uniquement
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # ── Entraînement ──────────────────────────────────────────────────────────
    # Corrections apportées vs version main :
    #   - hidden_layer_sizes=(64, 32) : adapté à la complexité réelle du problème
    #   - early_stopping=True         : arrêt automatique sur validation interne
    #   - validation_fraction=0.15    : 15 % du train réservé à la validation interne
    #   - max_iter=500                : limite haute de sécurité
    #   - random_state=42             : reproductibilité
    print("\nEntraînement du MLP (early stopping activé)...")
    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        learning_rate_init=1e-3,
        alpha=0.01,                  # L2 plus fort pour limiter le sur-apprentissage
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=15,
        random_state=42,
    )
    model.fit(X_train_s, Y_train)
    n_iter = model.n_iter_
    print(f"  Convergence en {n_iter} itérations")

    # ── Correction 5 : évaluation sur le jeu de TEST ──────────────────────────
    Y_pred_train = model.predict(X_train_s)
    Y_pred_test  = model.predict(X_test_s)

    mse_train = mean_squared_error(Y_train, Y_pred_train)
    mse_test  = mean_squared_error(Y_test,  Y_pred_test)

    traj_pred = Y_pred_test[0].reshape(-1, 2).astype(np.float32)

    r_vraie = np.sqrt(traj_vraie[:, 0] ** 2 + traj_vraie[:, 1] ** 2)
    r_pred  = np.sqrt(traj_pred[:, 0]  ** 2 + traj_pred[:, 1]  ** 2)
    mae_r   = float(mean_absolute_error(r_vraie, r_pred))
    mae_xy  = float(mean_absolute_error(traj_vraie.flatten(), traj_pred.flatten()))

    print(f"\n{'═' * 48}")
    print(f"  MSE train  (sur-apprentissage visible) : {mse_train:.2f} px²")
    print(f"  MSE test   (généralisation réelle)     : {mse_test:.2f} px²")
    print(f"  MAE r test                             : {mae_r:.1f} px")
    print(f"  MAE XY test                            : {mae_xy:.1f} px")
    print(f"{'═' * 48}\n")

    # ── Sauvegarde ────────────────────────────────────────────────────────────
    metrics = {
        "model":        "MLPRegressor",
        "test_id":      test_id,
        "n_train":      len(X_train),
        "target_len":   target_len,
        "n_iter":       n_iter,
        "mse_train":    round(float(mse_train), 4),
        "mse_test":     round(float(mse_test),  4),
        "mae_r_px":     round(mae_r,  2),
        "mae_xy_px":    round(mae_xy, 2),
    }
    save_csv(metrics, args.csv)

    loss_curve = model.loss_curve_ if hasattr(model, "loss_curve_") else []

    if not args.no_plot:
        plot_result(
            traj_vraie, traj_pred, loss_curve,
            test_id, len(X_train), mae_r, target_len, args.output,
        )
    else:
        plt.close("all")
