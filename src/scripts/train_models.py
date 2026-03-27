"""Entraînement des modèles ML sur données synthétiques.

Entraîne 2 algorithmes × 3 contextes = 6 modèles.
La RAM est libérée entre chaque modèle via gc.collect().
Les scalers sont fittés sur le premier chunk de chaque contexte.

Usage :
    python scripts/train_models.py [--config path/to/ml.toml] [--workers N]

Avec --workers 6, les 6 modèles (linéaire + MLP) × (10%/50%/100%) tournent
en parallèle dans des processus séparés.
"""

import argparse
import logging
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config" / "ml.toml"))
    parser.add_argument(
        "--workers", type=int, default=1,
        help=(
            "Nombre de processus parallèles. "
            f"Max utile = 6 (2 algos × 3 contextes). "
            f"CPUs disponibles : {os.cpu_count()}."
        ),
    )
    args = parser.parse_args()

    with open(args.config, "rb") as f:
        cfg = tomllib.load(f)

    data_dir   = ROOT / cfg["paths"]["synth_data_dir"]
    models_dir = ROOT / cfg["paths"]["models_dir"]

    ctx_names     = cfg["synth"]["contexts"]["names"]
    ctx_fractions = cfg["synth"]["contexts"]["fractions"]
    contexts      = dict(zip(ctx_names, ctx_fractions))

    log.info(
        "Démarrage de l'entraînement — %d contextes × 2 modèles — %d worker(s)",
        len(contexts), args.workers,
    )
    train_synth(data_dir, models_dir, contexts, n_workers=args.workers)
    log.info("Entraînement terminé. Modèles dans : %s", models_dir)


if __name__ == "__main__":
    main()
