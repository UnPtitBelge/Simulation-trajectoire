#!/usr/bin/env python3
"""Script pour générer le dataset synthétique avec la structure correcte.

Ce script génère 100 000 trajectoires de simulation cône et les sauvegarde
dans le format attendu par l'application (avec les clés 'trajectories' et 'ref_trajs').
"""

import logging
import os
import sys
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.model.ml.sim_to_real.data_utils import (
        _SYNTHETIC_CSV,
        _SYNTHETIC_NPZ,
        generate_and_save_pool,
    )

    log.info("✓ Import successful")
except ImportError as e:
    log.error(f"✗ Import failed: {e}")
    sys.exit(1)


def progress_callback(current, total):
    """Callback pour afficher la progression."""
    if current % 1000 == 0 or current == total:
        percentage = (current / total) * 100
        log.info(f"Progress: {current}/{total} ({percentage:.1f}%)")


def main():
    log.info("Starting synthetic data generation...")
    log.info(f"Target: {_SYNTHETIC_NPZ}")
    log.info(f"CSV output: {_SYNTHETIC_CSV}")

    start_time = datetime.now()
    log.info(f"Start time: {start_time}")

    try:
        # Générer et sauvegarder le pool
        generate_and_save_pool(
            path=_SYNTHETIC_NPZ, csv_path=_SYNTHETIC_CSV, progress_cb=progress_callback
        )

        end_time = datetime.now()
        duration = end_time - start_time

        log.info("✓ Data generation completed successfully!")
        log.info(f"Start time: {start_time}")
        log.info(f"End time: {end_time}")
        log.info(f"Duration: {duration}")

        # Vérifier que les fichiers ont été créés
        if os.path.exists(_SYNTHETIC_NPZ):
            size_mb = os.path.getsize(_SYNTHETIC_NPZ) / (1024 * 1024)
            log.info(f"✓ NPZ file created: {_SYNTHETIC_NPZ} ({size_mb:.1f} MB)")
        else:
            log.error(f"✗ NPZ file not created: {_SYNTHETIC_NPZ}")

        if os.path.exists(_SYNTHETIC_CSV):
            size_mb = os.path.getsize(_SYNTHETIC_CSV) / (1024 * 1024)
            log.info(f"✓ CSV file created: {_SYNTHETIC_CSV} ({size_mb:.1f} MB)")
        else:
            log.error(f"✗ CSV file not created: {_SYNTHETIC_CSV}")

        return 0

    except Exception as e:
        log.error(f"✗ Data generation failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
