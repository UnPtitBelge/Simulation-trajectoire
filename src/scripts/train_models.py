"""Entraînement des modèles ML sur données synthétiques.

Entraîne 2 algorithmes × 4 contextes = 8 modèles.
Les contextes (fractions des chunks) sont lus depuis [synth.contexts] de ml.toml.
La RAM est libérée entre chaque modèle via gc.collect().

Usage :
    python scripts/train_models.py [--workers N]

Avec --workers 8, les 8 modèles tournent en parallèle dans des processus séparés.
"""

import argparse
import logging
import math
import os
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.train import train_synth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def _print_summary(summary: dict) -> None:
    """Tableau récapitulatif des val MSE après entraînement."""
    contexts = sorted({lbl.split("_", 1)[1] for lbl in summary})
    algos    = sorted({lbl.split("_", 1)[0] for lbl in summary})

    col = 14
    header = f"  {'Contexte':<12}" + "".join(f"  {a.upper():>{col}}" for a in algos)
    print(f"\n{'═' * len(header)}")
    print(header)
    print(f"{'─' * len(header)}")

    for ctx in contexts:
        row = f"  {ctx:<12}"
        for algo in algos:
            lbl   = f"{algo}_{ctx}"
            stats = summary.get(lbl, {})
            if "val_history" in stats:          # MLP
                val = stats.get("best_val", float("nan"))
                ep  = stats.get("stopped_epoch", stats.get("n_epochs", "?"))
                cell = f"{val:.5f} (ep{ep})" if not math.isnan(val) else "n/a"
            else:                               # LR
                val  = stats.get("val_mse", float("nan"))
                cell = f"{val:.5f} (exact)" if not math.isnan(val) else "n/a"
            row += f"  {cell:>{col}}"
        print(row)

    print(f"{'═' * len(header)}\n")


def _plot_training_summary(summary: dict) -> None:
    """Courbes de convergence val MSE par epoch pour chaque contexte MLP."""
    import matplotlib.pyplot as plt

    mlp_items = {
        lbl: stats for lbl, stats in summary.items()
        if "val_history" in stats and stats["val_history"]
    }
    if not mlp_items:
        print("Aucune courbe de convergence disponible (pas de chunks de validation).")
        return

    contexts = sorted({lbl.split("_", 1)[1] for lbl in mlp_items})
    palette  = ["steelblue", "darkorange", "seagreen", "crimson", "mediumpurple"]
    colors   = {ctx: palette[i % len(palette)] for i, ctx in enumerate(contexts)}

    fig, ax = plt.subplots(figsize=(9, 5))
    for lbl, stats in sorted(mlp_items.items()):
        ctx     = lbl.split("_", 1)[1]
        history = stats["val_history"]
        epochs  = list(range(1, len(history) + 1))
        ax.plot(epochs, history, marker="o", linewidth=1.8, markersize=5,
                color=colors[ctx], label=f"MLP [{ctx}]")
        best_ep = int(history.index(min(history))) + 1
        ax.axvline(best_ep, color=colors[ctx], linestyle="--", linewidth=0.8, alpha=0.6)

    ax.set_title("Convergence MLP — val MSE par epoch")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Val MSE (espace normalisé)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config" / "ml.toml"))
    parser.add_argument(
        "--workers", type=int, default=1,
        help=(
            "Nombre de processus parallèles. "
            f"Max utile = 8 (2 algos × 4 contextes). "
            f"CPUs disponibles : {os.cpu_count()}."
        ),
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Afficher les courbes de convergence MLP après l'entraînement",
    )
    args = parser.parse_args()

    with open(args.config, "rb") as f:
        cfg = tomllib.load(f)

    data_dir   = ROOT / cfg["paths"]["synth_data_dir"]
    models_dir = ROOT / cfg["paths"]["models_dir"]

    ctx_names     = cfg["synth"]["contexts"]["names"]
    ctx_fractions = cfg["synth"]["contexts"]["fractions"]
    contexts      = dict(zip(ctx_names, ctx_fractions))

    model_cfg = cfg.get("model", {})
    log.info(
        "Démarrage de l'entraînement — %d contextes × 2 modèles — %d worker(s)",
        len(contexts), args.workers,
    )
    summary = train_synth(
        data_dir, models_dir, contexts,
        n_workers=args.workers,
        n_scaler_chunks=model_cfg.get("n_scaler_chunks", 10),
        val_fraction=model_cfg.get("val_fraction", 0.05),
        n_epochs=model_cfg.get("mlp_n_epochs", 5),
        patience=model_cfg.get("mlp_patience", 2),
    )
    log.info("Entraînement terminé. Modèles dans : %s", models_dir)

    _print_summary(summary)

    if args.plot:
        _plot_training_summary(summary)


if __name__ == "__main__":
    main()
