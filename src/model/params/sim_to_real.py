"""Paramètres pour la simulation Sim-to-Real (présentation + mode libre)."""

from dataclasses import dataclass, field
from typing import ClassVar

from src.model.params.base import BaseParams
from src.model.params.integrators import MLModel
from src.model.params.physics_constants import LAUNCH_ANGLE, LAUNCH_R0, LAUNCH_SPEED


@dataclass
class SimToRealParams(BaseParams):
    """Paramètres de la simulation Sim-to-Real.

    model_type : modèle ML (régression linéaire ou MLP)
    r0         : position radiale initiale (m) — condition initiale de test
    v0         : vitesse initiale (m/s)        — condition initiale de test
    phi0       : angle initial (°)             — condition initiale de test
    frame_ms   : intervalle entre frames d'animation (ms)

    model_type déclenche un réentraînement.
    r0/v0/phi0 ne font que relancer la prédiction (instantané) via la CI bar.
    """

    model_type: MLModel = field(default=MLModel.LINEAR)
    n_sims:     int     = 90_000       # trajectoires d'entraînement chargées du pool
    r0:         float   = LAUNCH_R0    # m   — CI de présentation (cône)
    v0:         float   = LAUNCH_SPEED # m/s — CI de présentation (cône)
    phi0:       float   = LAUNCH_ANGLE # °   — angle de la vitesse initiale
    frame_ms:   int     = 16

    # model_type apparaît dans le _ParamsPanel du mode libre.
    # r0/v0/phi0 sont gérés exclusivement par la CI bar intégrée au widget.
    PARAM_RANGES: ClassVar[dict] = {
        "model_type": {
            "label": "Modèle",
            "type": "discrete",
            "choices": list(MLModel),
            "choice_labels": ["Régr. linéaire", "MLP"],
        },
    }

    PRESETS: ClassVar[dict] = {}

    # CI alignées avec les presets du cône (même F1/F2/F3 conceptuels).
    # Changer uniquement r0/v0/phi0 — model_type est contrôlé
    # séparément par T (toggle RL/MLP).
    PRESENTATION_PRESETS: ClassVar[dict] = {
        "pres_standard": {
            "r0": LAUNCH_R0, "v0": LAUNCH_SPEED, "phi0": LAUNCH_ANGLE,
            "label": "CI standard",
        },
        "pres_rapide": {
            "r0": LAUNCH_R0, "v0": 1.5, "phi0": LAUNCH_ANGLE,
            "label": "CI rapide",
        },
        "pres_bord": {
            "r0": 0.38, "v0": LAUNCH_SPEED, "phi0": LAUNCH_ANGLE,
            "label": "CI proche du bord",
        },
    }
