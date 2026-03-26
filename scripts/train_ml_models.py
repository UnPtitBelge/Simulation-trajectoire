#!/usr/bin/env python3
"""Script pour entraîner les modèles ML sur le dataset synthétique.

Ce script entraîne deux modèles (Régression Linéaire et MLP) sur les données
générées et les sauvegarde dans le format attendu par l'application.
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
    from src.model.ml.sim_to_real.data_utils import _SYNTHETIC_NPZ, load_pool
    from src.model.ml.sim_to_real.model_utils import _MODELS_PKL

    log.info("✓ Imports successful")
except ImportError as e:
    log.error(f"✗ Import failed: {e}")
    sys.exit(1)


def main():
    log.info("Starting ML model training...")
    log.info(f"Data source: {_SYNTHETIC_NPZ}")
    log.info(f"Model output: {_MODELS_PKL}")

    start_time = datetime.now()
    log.info(f"Start time: {start_time}")

    try:
        # Vérifier que le dataset existe
        if not os.path.exists(_SYNTHETIC_NPZ):
            log.error(f"✗ Dataset not found: {_SYNTHETIC_NPZ}")
            log.error(
                "Please generate the synthetic data first using generate_synthetic_data.py"
            )
            return 1

        log.info("✓ Dataset found, loading...")

        # Charger le pool de données
        pool_data = load_pool(_SYNTHETIC_NPZ)
        if pool_data is None:
            log.error("✗ Failed to load dataset")
            return 1

        n_trajs = len(pool_data["trajectories"])
        log.info(f"✓ Dataset loaded: {n_trajs} trajectories")

        # Entraîner et évaluer les modèles
        log.info("Training models...")
        log.info("This may take several minutes depending on your hardware...")

        start_training = datetime.now()

        # La fonction train_and_evaluate entraîne les deux modèles
        # et retourne un dictionnaire avec les modèles entraînés
        models_dict = train_and_evaluate(pool_data)

        training_duration = datetime.now() - start_training
        log.info(f"✓ Training completed in {training_duration}")
        log.info(f"Trained models: {list(models_dict.keys())}")

        # Sauvegarder les modèles
        log.info(f"Saving models to {_MODELS_PKL}...")

        # La fonction train_and_evaluate sauvegarde déjà les modèles,
        # mais nous pouvons vérifier que le fichier existe
        if os.path.exists(_MODELS_PKL):
            size_mb = os.path.getsize(_MODELS_PKL) / (1024 * 1024)
            log.info(f"✓ Models saved: {_MODELS_PKL} ({size_mb:.1f} MB)")
        else:
            log.error(f"✗ Models file not created: {_MODELS_PKL}")
            return 1

        end_time = datetime.now()
        total_duration = end_time - start_time

        log.info(f"✓ ML training completed successfully!")
        log.info(f"Start time: {start_time}")
        log.info(f"End time: {end_time}")
        log.info(f"Total duration: {total_duration}")

        return 0

    except Exception as e:
        log.error(f"✗ Training failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
