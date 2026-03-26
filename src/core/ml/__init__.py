"""ML module — sim-to-real pipeline and trajectory prediction."""

# Re-export directement depuis sim_to_real.py
from .sim_to_real import (
    _N_IN, _N_OUT, _MIN_TRAJ_LEN, _POOL_SIZE,
    _SYNTHETIC_CSV, _SYNTHETIC_NPZ, _PRESETS_NPZ, _MODELS_PKL,
    generate_and_save_pool, pool_is_ready, load_pool,
    train_and_evaluate, save_trained_models, load_trained_models, models_are_ready,
    compute_and_save_presets, presets_are_ready, load_presets,
)

__all__ = [
    "generate_and_save_pool", "pool_is_ready", "load_pool",
    "train_and_evaluate", "save_trained_models", "load_trained_models", "models_are_ready",
    "compute_and_save_presets", "presets_are_ready", "load_presets",
    "_N_IN", "_N_OUT", "_MIN_TRAJ_LEN", "_POOL_SIZE",
    "_SYNTHETIC_CSV", "_SYNTHETIC_NPZ", "_PRESETS_NPZ", "_MODELS_PKL",
]