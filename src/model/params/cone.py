"""Cone presets — 3 configurations par défaut."""

from src.model.params.physics_constants import (
    CONE_DEFAULT_SLOPE,
    GRAVITY,
    LAUNCH_ANGLE,
    LAUNCH_R0,
    LAUNCH_SPEED,
    SURFACE_RADIUS,
)

CONE_PRESETS: dict[str, dict] = {
    "demo_standard": {
        "slope": CONE_DEFAULT_SLOPE,
        "R_cone": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.012,
        "r0": LAUNCH_R0,
        "v0": LAUNCH_SPEED,
        "phi0": LAUNCH_ANGLE,
        "label": "Conditions standard",
    },
    "demo_63": {
        "slope": CONE_DEFAULT_SLOPE,
        "R_cone": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.012,
        "r0": LAUNCH_R0,
        "v0": 0.63,
        "phi0": LAUNCH_ANGLE,
        "label": "Vitesse 0.63 m/s",
    },
    "demo_angle": {
        "slope": CONE_DEFAULT_SLOPE,
        "R_cone": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.012,
        "r0": LAUNCH_R0,
        "v0": 0.63,
        "phi0": 135,
        "label": "Vitesse 0;63 m/s  - Angle 135°",
    },
}
