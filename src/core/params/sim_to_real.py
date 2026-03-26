"""Paramètres pour la simulation Sim-to-Real (présentation + mode libre)."""

from dataclasses import dataclass, field
from typing import ClassVar

from src.core.params.base import BaseParams
from src.core.params.integrators import MLModel
from src.core.params.physics_constants import LAUNCH_ANGLE, LAUNCH_R0, LAUNCH_SPEED


@dataclass
class SimToRealParams(BaseParams):
    """Paramètres de la simulation Sim-to-Real.

    n_sims     : taille du jeu de données synthétique (déclenche un réentraînement)
    model_type : modèle ML (régression linéaire ou MLP)
    r0         : position radiale initiale (m) — condition initiale de test
    v0         : vitesse initiale (m/s)        — condition initiale de test
    phi0       : angle initial (°)             — condition initiale de test
    frame_ms   : intervalle entre frames d'animation (ms)

    n_sims et model_type déclenchent un réentraînement.
    r0/v0/phi0 ne font que relancer la prédiction (instantané) via la CI bar.
    """

    n_sims:     int     = 150
    model_type: MLModel = field(default=MLModel.LINEAR)
    r0:         float   = LAUNCH_R0    # m   — CI de présentation (cône)
    v0:         float   = LAUNCH_SPEED # m/s — CI de présentation (cône)
    phi0:       float   = LAUNCH_ANGLE # °   — angle de la vitesse initiale
    frame_ms:   int     = 16

    # n_sims et model_type apparaissent dans le _ParamsPanel du mode libre.
    # r0/v0/phi0 sont gérés exclusivement par la CI bar intégrée au widget.
    PARAM_RANGES: ClassVar[dict] = {
        "model_type": {
            "label": "Modèle",
            "type": "discrete",
            "choices": list(MLModel),
            "choice_labels": ["Régr. linéaire", "MLP"],
        },
        "n_sims": {
            "label": "Simulations (entr.)",
            "min": 50, "max": 100_000, "step": 50,
            "scale": "log",
        },
    }

    PRESETS: ClassVar[dict] = {}

    PRESENTATION_PRESETS: ClassVar[dict] = {
        # Mêmes CI que le preset "présentation" du cône — trajectoire de référence
        "nominale": {
            "r0": LAUNCH_R0, "v0": LAUNCH_SPEED, "phi0": LAUNCH_ANGLE,
            "label": "CI de présentation",
        },
        # Hors distribution (r0 > plage d'entraînement [0.08, 0.35])
        "hors_distrib": {
            "r0": 0.34, "v0": 2.4, "phi0": 0.0,
            "label": "Hors distribution",
        },
        "lente": {
            "r0": 0.12, "v0": 0.35, "phi0": 135.0,
            "label": "CI lente",
        },
    }
