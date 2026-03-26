"""Cone simulation parameters."""

from dataclasses import dataclass, field
from typing import ClassVar

from src.model.params.base import BaseParams
from src.model.params.integrators import Integrator
from src.model.params.physics_constants import (
    CONE_DEFAULT_SLOPE,
    GRAVITY,
    LAUNCH_ANGLE,
    LAUNCH_R0,
    LAUNCH_SPEED,
    SURFACE_RADIUS,
)
from src.model.params.cone import CONE_PRESENTATION_PRESETS


@dataclass
class ConeParams(BaseParams):
    """Cone with constant slope: z(r) = -slope*(R_cone - r).
    Gravity component along surface = g*sin(alpha), constant everywhere.
    Coulomb friction opposing velocity."""

    n_frames: int = 3000
    frame_ms: int = 16
    dt: float = 0.01
    slope: float = CONE_DEFAULT_SLOPE
    R_cone: float = SURFACE_RADIUS
    gravity: float = GRAVITY
    friction: float = 0.012
    r0: float = LAUNCH_R0
    v0: float = LAUNCH_SPEED
    phi0: float = LAUNCH_ANGLE
    integrator: Integrator = field(default=Integrator.EULER_SEMI_IMPLICIT)
    compare_integrators: bool = False

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
        "slope": {"label": "Pente α", "min": 0.05, "max": 0.50, "step": 0.005},
        "friction": {"label": "Frottement μ", "min": 0.0, "max": 0.30, "step": 0.002},
        "r0": {"label": "Position r₀ (m)", "min": 0.05, "max": 0.39, "step": 0.01},
        "v0": {"label": "Vitesse v₀ (m/s)", "min": 0.0, "max": 3.0, "step": 0.05},
        "phi0": {"label": "Angle φ₀ (°)", "min": 0.0, "max": 360.0, "step": 5.0},
    }

    PRESETS: ClassVar[dict[str, dict]] = {
        "presentation": {
            "slope": CONE_DEFAULT_SLOPE,
            "R_cone": SURFACE_RADIUS,
            "friction": 0.012,
            "r0": LAUNCH_R0,
            "v0": LAUNCH_SPEED,
            "phi0": LAUNCH_ANGLE,
            "label": "Conditions de présentation",
        },
        "sans_frottement": {
            "slope": 0.15,
            "R_cone": SURFACE_RADIUS,
            "friction": 0.0,
            "r0": LAUNCH_R0,
            "v0": LAUNCH_SPEED,
            "phi0": LAUNCH_ANGLE,
            "label": "Sans frottement",
        },
        "pente_forte": {
            "slope": 0.30,
            "R_cone": SURFACE_RADIUS,
            "friction": 0.012,
            "r0": LAUNCH_R0,
            "v0": LAUNCH_SPEED,
            "phi0": LAUNCH_ANGLE,
            "label": "Pente forte",
        },
        # Intégration numérique ch.6
        "euler": {
            "integrator": Integrator.EULER_SEMI_IMPLICIT,
            "compare_integrators": False,
            "label": "Euler semi-implicite",
        },
        "verlet": {
            "integrator": Integrator.VERLET,
            "compare_integrators": False,
            "label": "Verlet",
        },
        "rk4": {
            "integrator": Integrator.RK4,
            "compare_integrators": False,
            "label": "RK4",
        },
        "compare": {
            "integrator": Integrator.EULER_SEMI_IMPLICIT,
            "compare_integrators": True,
            "label": "Superposition intégrateurs",
        },
    }

    PRESENTATION_PRESETS: ClassVar[dict[str, dict]] = CONE_PRESENTATION_PRESETS
