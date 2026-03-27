#!/usr/bin/env python3
"""Script pour entraîner les modèles ML sur le dataset synthétique.

Entraîne RL et MLP pour les 4 tailles de contexte (_PRESET_N_SIMS = [50, 45_000, 90_000, 1_000_000])
et sauvegarde tous les modèles dans trained_models.pkl sous la structure :
  {n_sims: {lr_x, lr_y, mlp_x, mlp_y, metrics_lr, metrics_mlp, train_trajs}, ...,
   "ref_trajs": {pres_standard: ..., pres_rapide: ..., pres_bord: ...}}
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import numpy as np
    from src.model.ml.sim_to_real.data_utils import (
        _PRESET_N_SIMS,
        _SYNTHETIC_NPZ,
        _MODELS_PKL,
        load_pool,
    )
    from src.model.ml.sim_to_real.model_utils import (
        train_and_evaluate,
        save_trained_models,
    )

    log.info("✓ Imports successful")
except ImportError as e:
    log.error(f"✗ Import failed: {e}")
    sys.exit(1)


def main() -> int:
    log.info("Starting ML model training...")
    log.info(f"Data source: {_SYNTHETIC_NPZ}")
    log.info(f"Model output: {_MODELS_PKL}")
    log.info(f"Context sizes: {_PRESET_N_SIMS}")

    start_time = datetime.now()

    if not os.path.exists(_SYNTHETIC_NPZ):
        log.error(f"✗ Dataset not found: {_SYNTHETIC_NPZ}")
        log.error(
            "Please generate the synthetic data first using generate_synthetic_data.py"
        )
        return 1

    pool_data = load_pool(_SYNTHETIC_NPZ)
    if pool_data is None:
        log.error("✗ Failed to load dataset")
        return 1

    all_trajs = pool_data["trajectories"]
    ref_trajs = pool_data.get("ref_trajs", {})
    log.info(f"✓ Dataset loaded: {len(all_trajs)} trajectories")

    rng = np.random.RandomState(42)
    all_models: dict = {}

    for n_sims in _PRESET_N_SIMS:
        n_available = len(all_trajs)
        n_use = min(n_sims, n_available)
        log.info(
            f"--- Training with n_sims={n_sims} ({n_use}/{n_available} trajectoires) ---"
        )

        if n_use < n_available:
            idx = rng.choice(n_available, n_use, replace=False)
            subset_trajs = all_trajs[idx]
        else:
            subset_trajs = all_trajs

        subset = {"trajectories": subset_trajs, "ref_trajs": ref_trajs}

        # Ajuster le chunk_size en fonction de n_use pour optimiser mémoire/performance
        # - Petits datasets (< 10k): pas de chunking nécessaire
        # - Moyens datasets (10k-100k): chunks de 25k
        # - Grands datasets (> 100k): chunks de 50k
        if n_use < 10_000:
            chunk_size = n_use  # Pas de chunking
        elif n_use < 100_000:
            chunk_size = 25_000
        else:
            chunk_size = 50_000

        log.info(f"  Using chunk_size={chunk_size}")
        t0 = datetime.now()
        result = train_and_evaluate(subset, chunk_size=chunk_size)
        duration = datetime.now() - t0

        m_lr = result["metrics_lr"]
        m_mlp = result["metrics_mlp"]
        log.info(
            f"  ✓ Done in {duration} | "
            f"LR R²=({m_lr['r2_x']:.3f}, {m_lr['r2_y']:.3f}) | "
            f"MLP R²=({m_mlp['r2_x']:.3f}, {m_mlp['r2_y']:.3f})"
        )
        all_models[n_sims] = result

    # Stocker les ref_trajs dans le pkl pour éviter de charger le pool 400 MB au runtime
    all_models["ref_trajs"] = ref_trajs

    log.info(f"Saving all models to {_MODELS_PKL}...")
    save_trained_models(all_models, _MODELS_PKL)

    if not os.path.exists(_MODELS_PKL):
        log.error(f"✗ Failed to save models to {_MODELS_PKL}")
        return 1

    size_mb = os.path.getsize(_MODELS_PKL) / (1024 * 1024)
    total_duration = datetime.now() - start_time
    log.info(f"✓ Models saved: {_MODELS_PKL} ({size_mb:.1f} MB)")
    log.info(f"✓ ML training completed successfully! Total duration: {total_duration}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
