"""ML module — sim-to-real pipeline and trajectory prediction."""

# Re-export des constantes et fonctions depuis les modules dédiés
from .data_utils import (
    _N_IN, _N_OUT, _MIN_TRAJ_LEN, _POOL_SIZE,
    _SYNTHETIC_CSV, _SYNTHETIC_NPZ, _PRESETS_NPZ, _MODELS_PKL,
    generate_and_save_pool, pool_is_ready, load_pool,
)
from .model_utils import (
    train_and_evaluate, save_trained_models, load_trained_models, models_are_ready,
    get_cached_models, set_cached_models,
)
from .preset_utils import (
    compute_and_save_presets, presets_are_ready, load_presets,
)
from .sim_to_real import PlotSimToReal

__all__ = [
    # Constantes
    "_N_IN", "_N_OUT", "_MIN_TRAJ_LEN", "_POOL_SIZE",
    "_SYNTHETIC_CSV", "_SYNTHETIC_NPZ", "_PRESETS_NPZ", "_MODELS_PKL",
    # Génération de données
    "generate_and_save_pool", "pool_is_ready", "load_pool",
    # Modèles et entraînement
    "train_and_evaluate", "save_trained_models", "load_trained_models", "models_are_ready",
    "get_cached_models", "set_cached_models",
    # Presets
    "compute_and_save_presets", "presets_are_ready", "load_presets",
    # Visualisation
    "PlotSimToReal",
]