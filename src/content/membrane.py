"""Membrane presentation presets — 3 configurations for classroom demos."""

from src.model.params.physics_constants import (
    GRAVITY,
    LAUNCH_ANGLE,
    LAUNCH_R0,
    LAUNCH_SPEED,
    MEMBRANE_DEFAULT_F,
    MEMBRANE_DEFAULT_T,
    SURFACE_RADIUS,
)

MEMBRANE_PRESENTATION_PRESETS: dict[str, dict] = {
    "demo_orbite": {
        "F": MEMBRANE_DEFAULT_F,
        "T": MEMBRANE_DEFAULT_T,
        "R_membrane": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.005,
        "r0": LAUNCH_R0,
        "v0": LAUNCH_SPEED,
        "phi0": LAUNCH_ANGLE,
        "label": "Orbite gravitationnelle",
    },
    "demo_spirale": {
        "F": MEMBRANE_DEFAULT_F * 4,   # A ≈ 0.08
        "T": MEMBRANE_DEFAULT_T,
        "R_membrane": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.015,
        "r0": LAUNCH_R0,
        "v0": LAUNCH_SPEED,
        "phi0": LAUNCH_ANGLE,
        "label": "Spirale vers le centre",
    },
    "demo_puits_profond": {
        "F": MEMBRANE_DEFAULT_F * 6,   # A ≈ 0.12
        "T": MEMBRANE_DEFAULT_T,
        "R_membrane": SURFACE_RADIUS,
        "gravity": GRAVITY,
        "friction": 0.008,
        "r0": LAUNCH_R0,
        "v0": LAUNCH_SPEED,
        "phi0": LAUNCH_ANGLE,
        "label": "Puits profond",
    },
}
