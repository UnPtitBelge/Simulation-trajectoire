"""MCU simulation parameters."""

from dataclasses import dataclass
from typing import ClassVar

from src.model.params.base import BaseParams
from src.model.params.mcu import MCU_PRESETS


@dataclass
class MCUParams(BaseParams):
    """MCU parameters: x=R·cos(ωt), y=R·sin(ωt) with optional exponential drag."""

    n_frames: int = 600
    frame_ms: int = 16
    R: float = 10.0
    omega: float = 1.0
    drag: float = 0.0
    center_radius: float = 1.0

    PARAM_RANGES: ClassVar[dict[str, dict]] = {
        "R":     {"label": "Rayon R",             "min": 2.0, "max": 20.0, "step": 0.5},
        "omega": {"label": "Vitesse angulaire ω", "min": 0.1, "max": 6.0,  "step": 0.1},
        "drag":  {"label": "Amortissement",       "min": 0.0, "max": 1.0,  "step": 0.01},
    }

    PRESETS: ClassVar[dict[str, dict]] = {
        "orbite_stable": {
            "R": 10.0,
            "omega": 1.0,
            "drag": 0.0,
            "label": "Orbite stable (MCU pur)",
        },
        "spirale": {
            "R": 10.0,
            "omega": 1.0,
            "drag": 0.3,
            "label": "Spirale (avec frottement)",
        },
        "rapide": {
            "R": 5.0,
            "omega": 3.0,
            "drag": 0.05,
            "label": "Orbite rapide",
        },
    }

    PRESETS: ClassVar[dict[str, dict]] = MCU_PRESETS
