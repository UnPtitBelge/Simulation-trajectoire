"""Simulation parameter dataclasses.

Each dataclass contains all physical, numerical and initial-condition
parameters for one simulation type.  Fields with a type annotation are
exposed as UI controls by ParamsController; fields without one (e.g.
``frame_ms``) are class-level constants hidden from the control panel.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import cos, radians, sin, sqrt
from typing import Dict


# ---------------------------------------------------------------------------
# Shared velocity-decomposition mixin
# ---------------------------------------------------------------------------

class _InitialVelocityMixin:
    """Decomposes (v_i, theta) into (vx0, vy0) for surface simulations.

    Convention: at initial position (x0, y0), r̂ points **inward** and t̂
    points **CCW tangentially**.  theta=0 → purely radially inward;
    theta=90 → purely CCW tangential.
    """

    x0: float
    y0: float
    v_i: float
    theta: float

    @property
    def vx0(self) -> float:
        r = sqrt(self.x0 * self.x0 + self.y0 * self.y0)
        if r > 1e-12:
            rx = -self.x0 / r
            tx = -self.y0 / r
        else:
            rx, tx = -1.0, 0.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * rx + sin(th) * tx)

    @property
    def vy0(self) -> float:
        r = sqrt(self.x0 * self.x0 + self.y0 * self.y0)
        if r > 1e-12:
            ry = -self.y0 / r
            ty =  self.x0 / r
        else:
            ry, ty = 0.0, 1.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * ry + sin(th) * ty)


# ---------------------------------------------------------------------------
# 3-D cone (Newton) simulation
# ---------------------------------------------------------------------------

@dataclass
class SimulationConeParams(_InitialVelocityMixin):
    """Parameters for the 3-D conical surface (Newton) simulation."""

    frame_ms = 10  # hidden from UI: animation frame interval [ms]

    cone_slope:      float = field(default=0.10,    metadata={"label": "Pente α",         "unit": ""})
    surface_radius:  float = field(default=0.80,    metadata={"label": "Rayon R",          "unit": "m"})
    center_radius:   float = field(default=0.035,   metadata={"label": "Rayon central",    "unit": "m"})

    time_step:  float = field(default=0.010,    metadata={"label": "Pas de temps dt",  "unit": "s"})
    num_steps:  int   = field(default=20_000,   metadata={"label": "Étapes max",       "unit": ""})

    g:               float = field(default=9.810,   metadata={"label": "Gravité g",        "unit": "m/s²"})
    particle_radius: float = field(default=0.010,   metadata={"label": "Rayon bille",      "unit": "m"})
    particle_mass:   float = field(default=0.010,   metadata={"label": "Masse m",          "unit": "kg"})

    x0:    float = field(default=0.80,   metadata={"label": "Position x₀",     "unit": "m"})
    y0:    float = field(default=0.00,   metadata={"label": "Position y₀",     "unit": "m"})
    v_i:   float = field(default=0.50,   metadata={"label": "Vitesse v₀",      "unit": "m/s"})
    theta: float = field(default=85.0,   metadata={"label": "Angle θ",         "unit": "°"})

    friction_coef: float = field(default=0.01,   metadata={"label": "Frottement μ",    "unit": ""})

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 3-D membrane (Laplace) simulation
# ---------------------------------------------------------------------------

@dataclass
class SimulationMembraneParams(_InitialVelocityMixin):
    """Parameters for the 3-D Laplace membrane simulation."""

    frame_ms = 10  # hidden from UI

    surface_tension: float = field(default=10.0,    metadata={"label": "Tension T",        "unit": "N/m"})
    center_weight:   float = field(default=4.905,   metadata={"label": "Poids central F",  "unit": "N"})
    surface_radius:  float = field(default=0.40,    metadata={"label": "Rayon R",          "unit": "m"})
    center_radius:   float = field(default=0.035,   metadata={"label": "Rayon central",    "unit": "m"})

    time_step:  float = field(default=0.010,    metadata={"label": "Pas de temps dt",  "unit": "s"})
    num_steps:  int   = field(default=20_000,   metadata={"label": "Étapes max",       "unit": ""})

    g:               float = field(default=9.810,   metadata={"label": "Gravité g",        "unit": "m/s²"})
    particle_radius: float = field(default=0.010,   metadata={"label": "Rayon bille",      "unit": "m"})
    particle_mass:   float = field(default=0.010,   metadata={"label": "Masse m",          "unit": "kg"})

    x0:    float = field(default=0.385,  metadata={"label": "Position x₀",     "unit": "m"})
    y0:    float = field(default=0.00,   metadata={"label": "Position y₀",     "unit": "m"})
    v_i:   float = field(default=1.00,   metadata={"label": "Vitesse v₀",      "unit": "m/s"})
    theta: float = field(default=45.0,   metadata={"label": "Angle θ",         "unit": "°"})

    friction_coef: float = field(default=0.12,   metadata={"label": "Frottement μ",    "unit": ""})

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 2-D MCU simulation
# ---------------------------------------------------------------------------

@dataclass
class SimulationMCUParams:
    """Parameters for the 2-D uniform circular motion (MCU) simulation."""

    frame_ms = 20  # hidden from UI

    R:               float = field(default=50.0,   metadata={"label": "Rayon orbital R",   "unit": "m"})
    omega:           float = field(default=0.50,   metadata={"label": "Vitesse ω",         "unit": "rad/s"})
    n_orbits:        float = field(default=3.0,    metadata={"label": "Nombre d'orbites",  "unit": ""})
    initial_angle:   float = field(default=0.0,    metadata={"label": "Angle initial φ₀",  "unit": "°"})
    center_radius:   float = field(default=6.0,    metadata={"label": "Rayon central",     "unit": "m"})
    particle_radius: float = field(default=2.0,    metadata={"label": "Rayon bille",       "unit": "m"})

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# ML simulation
# ---------------------------------------------------------------------------

@dataclass
class SimulationMLParams:
    """Configuration for the machine-learning trajectory demo."""

    frame_ms = 30  # hidden from UI

    test_initial_idx:     int   = field(default=0,     metadata={"label": "Échantillon",           "unit": ""})
    noise_level:          float = field(default=0.0,   metadata={"label": "Bruit σ",               "unit": ""})
    marker_size:          int   = field(default=10,    metadata={"label": "Taille marqueur",        "unit": "px"})
    show_true_trajectory: bool  = field(default=True,  metadata={"label": "Afficher vraie trajectoire", "unit": ""})

    def to_dict(self) -> Dict:
        return asdict(self)
