#!/usr/bin/env python3
"""Script pour générer le dataset synthétique avec la structure correcte.

Génère 1 000 000 trajectoires de simulation cône (durée ≥ 8 s chacune)
et les sauvegarde dans le format attendu par l'application.
"""

import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Racine du projet (parent de scripts/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.model.ml.sim_to_real.data_utils import (
        _SYNTHETIC_CSV,
        _SYNTHETIC_NPZ,
        _POOL_SIZE,
        generate_and_save_pool,
    )
    log.info("✓ Import successful")
except ImportError as e:
    log.error(f"✗ Import failed: {e}")
    sys.exit(1)


def progress_callback(current: int, total: int) -> None:
    if current % 2000 == 0 or current == total:
        pct = current / max(total, 1) * 100
        log.info(f"Progression : {current} / {total} ({pct:.1f}%)")


def main() -> int:
    log.info("Démarrage de la génération du dataset synthétique...")
    log.info(f"Cible       : {_SYNTHETIC_NPZ}")
    log.info(f"CSV         : {_SYNTHETIC_CSV}")
    log.info(f"Trajectoires: {_POOL_SIZE} (durée min. 8 s chacune)")

    start_time = datetime.now()

    try:
        generate_and_save_pool(
            path=_SYNTHETIC_NPZ,
            csv_path=_SYNTHETIC_CSV,
            progress_cb=progress_callback,
            n_target=_POOL_SIZE,
        )
    except Exception as e:
        log.error(f"✗ Génération échouée : {e}")
        import traceback
        traceback.print_exc()
        return 1

    duration = datetime.now() - start_time
    log.info(f"✓ Génération terminée en {duration}")

    for fpath in (_SYNTHETIC_NPZ, _SYNTHETIC_CSV):
        if fpath and os.path.exists(fpath):
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            log.info(f"✓ {fpath} ({size_mb:.1f} MB)")
        elif fpath:
            log.warning(f"✗ Fichier absent : {fpath}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
