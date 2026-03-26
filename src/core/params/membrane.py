"""Membrane simulation parameters."""

import math
from dataclasses import dataclass, field
from typing import ClassVar

from src.core.params.base import BaseParams
from src.core.params.integrators import Integrator
from src.core.params.presets.membrane import MEMBRANE_PRESENTATION_PRESETS
from src.core.params.physics_constants import (
    GRAVITY,
    LAUNCH_ANGLE,
    LAUNCH_R0,
    LAUNCH_SPEED,
    MEMBRANE_DEFAULT_F,
    MEMBRANE_DEFAULT_T,
    SURFACE_RADIUS,
)


@dataclass
class MembraneParams(BaseParams):
    """Laplace membrane: z(r) = -(F/2πT)*ln(R/r).
    Slope = dz/dr = A/r where A = F/(2πT) → force grows near center.
    Coulomb friction opposing velocity."""

    n_frames: int = 3000
    frame_ms: int = 16
    dt: float = 0.01
    F: float = MEMBRANE_DEFAULT_F
    T: float = MEMBRANE_DEFAULT_T
    R_membrane: float = SURFACE_RADIUS
    gravity: float = GRAVITY
    friction: float = 0.012
    r0: float = LAUNCH_R0
    v0: float = LAUNCH_SPEED
    phi0: float = LAUNCH_ANGLE
    integrator: Integrator = field(default=Integrator.VERLET)
    compare_integrators: bool = False

    @property
    def A(self) -> float:
        """Derived coefficient A = F/(2πT) used in z(r) = -A·ln(R/r)."""
        return self.F / (2 * math.pi * self.T)

    PARAM_RANGES: ClassVar[dict[str, dict]] = {
        "integrator": {
            "label": "Intégrateur",
            "type": "discrete",
            "choices": list(Integrator),
            "choice_labels": ["Euler", "Verlet", "RK4"],
        },
        "compare_integrators": {
            "label": "Superposer intégrateurs",
            "type": "bool",
        },
        "F":        {"label": "Force F (N)",       "min": 0.1,  "max": 15.0, "step": 0.1},
        "T":        {"label": "Tension T (N/m)",   "min": 1.0,  "max": 50.0, "step": 0.5},
        "friction": {"label": "Frottement μ",      "min": 0.0,  "max": 0.30, "step": 0.002},
        "r0":       {"label": "Position r₀ (m)",   "min": 0.05, "max": 0.39, "step": 0.01},
        "v0":       {"label": "Vitesse v₀ (m/s)",  "min": 0.0,  "max": 3.0,  "step": 0.05},
        "phi0":     {"label": "Angle φ₀ (°)",      "min": 0.0,  "max": 360.0,"step": 5.0},
    }

    PRESETS: ClassVar[dict[str, dict]] = {
        "presentation": {
            "F": MEMBRANE_DEFAULT_F,
            "T": MEMBRANE_DEFAULT_T,
            "R_membrane": SURFACE_RADIUS,
            "friction": 0.012,
            "r0": LAUNCH_R0,
            "v0": LAUNCH_SPEED,
            "phi0": LAUNCH_ANGLE,
            "label": "Conditions de présentation",
        },
        "puits_profond": {
            "F": MEMBRANE_DEFAULT_F * 5,   # A ≈ 0.10
            "T": MEMBRANE_DEFAULT_T,
            "R_membrane": SURFACE_RADIUS,
            "friction": 0.012,
            "r0": LAUNCH_R0,
            "v0": LAUNCH_SPEED,
            "phi0": LAUNCH_ANGLE,
            "label": "Puits profond",
        },
        "sans_frottement": {
            "F": MEMBRANE_DEFAULT_F,
            "T": MEMBRANE_DEFAULT_T,
            "R_membrane": SURFACE_RADIUS,
            "friction": 0.0,
            "r0": LAUNCH_R0,
            "v0": LAUNCH_SPEED,
            "phi0": LAUNCH_ANGLE,
            "label": "Sans frottement",
        },
    }

    PRESENTATION_PRESETS: ClassVar[dict[str, dict]] = MEMBRANE_PRESENTATION_PRESETS
