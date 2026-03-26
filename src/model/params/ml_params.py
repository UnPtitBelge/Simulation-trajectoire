"""ML simulation parameters — régression linéaire / MLP IC → trajectoire complète."""

from dataclasses import dataclass, field
from typing import ClassVar

from src.model.params.base import BaseParams
from src.model.params.integrators import MLModel
from src.model.params.ml import ML_PRESETS


# Conditions initiales de test :
# 0, 1 — trajectoires 16 et 17 (retenues, vérité terrain disponible)
# 2, 3 — conditions initiales hors distribution (inconnues du modèle)
TEST_ICS: list[dict] = [
    {"x": 725.0, "y":   0.0, "vx": -16.1, "vy":   0.0},  # traj 16 (retenu)
    {"x": 717.0, "y":   2.0, "vx": -28.2, "vy":  37.5},  # traj 17 (retenu)
    {"x": 640.0, "y": 300.0, "vx": -30.0, "vy": -20.0},  # mi-terrain (HT)
    {"x": 600.0, "y": 400.0, "vx":  50.0, "vy": -80.0},  # extrême (HT)
]


@dataclass
class MLParams(BaseParams):
    """Paramètres ML : régression linéaire (x₀, y₀, vx₀, vy₀) → 350 positions.

    n_train trajectoires servent à l'entraînement (max 15 ; 16 et 17 toujours holdout).
    test_ic sélectionne les conditions initiales du test parmi TEST_ICS.
    frame_ms contrôle la vitesse de l'animation des 350 points prédits.
    """

    n_train:    int     = 15  # trajectoires 1..n_train pour l'entraînement (max 15)
    test_ic:    int     = 0   # indice dans TEST_ICS (0-3)
    model_type: MLModel = field(default=MLModel.LINEAR)
    frame_ms:   int     = 16  # 16 ms par point → ~5.6 s pour 350 points (60 fps)

    PARAM_RANGES: ClassVar[dict[str, dict]] = {
        "model_type": {
            "label": "Modèle",
            "type": "discrete",
            "choices": list(MLModel),
            "choice_labels": ["Régr. linéaire", "MLP"],
        },
        "n_train": {
            "label": "Trajectoires entraînement",
            "min": 1, "max": 15, "step": 1,
        },
        "test_ic": {
            "label": "C.I. de test (0-3)",
            "min": 0, "max": 3, "step": 1,
        },
    }

    PRESETS: ClassVar[dict[str, dict]] = {
        "peu_donnees": {
            "n_train": 3,
            "test_ic": 0,
            "label": "Peu de données",
        },
        "donnees_completes": {
            "n_train": 15,
            "test_ic": 0,
            "label": "Données complètes",
        },
        "hors_distribution": {
            "n_train": 15,
            "test_ic": 2,
            "label": "Hors distribution",
        },
    }

    PRESETS: ClassVar[dict[str, dict]] = ML_PRESETS
