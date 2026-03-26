"""Cone presentation presets — 3 configurations pour la présentation.

F1 — vitesse standard : CI nominales (LAUNCH_SPEED, LAUNCH_R0)
F2 — vitesse rapide   : même r0, v0 plus élevée
F3 — proche du bord   : même vitesse que F1, r0 plus grand (proche de R_cone)
"""

from src.model.params.physics_constants import (
    CONE_DEFAULT_SLOPE,
    GRAVITY,
    LAUNCH_ANGLE,
    LAUNCH_R0,
    LAUNCH_SPEED,
    SURFACE_RADIUS,
)

CONE_PRESENTATION_PRESETS: dict[str, dict] = {
    "pres_standard": {
        "slope": CONE_DEFAULT_SLOPE,
        "R_cone": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.012,
        "r0": LAUNCH_R0,
        "v0": LAUNCH_SPEED,
        "phi0": LAUNCH_ANGLE,
        "label": "Vitesse standard",
    },
    "pres_rapide": {
        "slope": CONE_DEFAULT_SLOPE,
        "R_cone": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.012,
        "r0": LAUNCH_R0,
        "v0": 1.5,
        "phi0": LAUNCH_ANGLE,
        "label": "Vitesse rapide",
    },
    "pres_bord": {
        "slope": CONE_DEFAULT_SLOPE,
        "R_cone": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.012,
        "r0": 0.38,
        "v0": LAUNCH_SPEED,
        "phi0": LAUNCH_ANGLE,
        "label": "Proche du bord",
    },
}
