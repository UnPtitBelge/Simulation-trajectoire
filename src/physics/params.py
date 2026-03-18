"""Single source of truth for all simulation parameter dataclasses.

Every default value lives here and nowhere else.
All other modules import from this file.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import cos, log, pi, radians, sin, sqrt
from typing import Dict


@dataclass
class Cone3dParams:
    """Parameters for the 3D cone-surface simulation (simple/Newton model).

    Surface profile:  z(r) = -cone_slope * (R - r)   [constant slope]
    Gravity:          a_g  = g * sin(arctan(cone_slope))
    Friction:         Coulomb, μ * g * cos(arctan(cone_slope))
    Integration:      semi-implicit (symplectic) Euler
    """

    # Not a dataclass field — hidden from auto-generated UI controls.
    frame_ms: int = 10

    cone_slope:      float = 0.10
    surface_radius:  float = 0.80
    center_radius:   float = 0.035

    time_step:   float = 0.010
    num_steps:   int   = 20000

    g:               float = 9.810
    particle_radius: float = 0.01
    particle_mass:   float = 0.01

    x0:    float = 0.80
    y0:    float = 0.00
    v_i:   float = 0.50
    theta: float = 85.0

    friction_coef: float = 0.01

    def to_dict(self) -> Dict:
        return asdict(self)

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
            ty = self.x0 / r
        else:
            ry, ty = 0.0, 1.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * ry + sin(th) * ty)


@dataclass
class Membrane3dParams:
    """Parameters for the 3D membrane-surface simulation (accurate/Laplace model).

    Surface profile:  z(r) = -(F / 2πT) * ln(R / r)   [logarithmic deformation]
    where F = center_weight [N], T = surface_tension [N/m].
    Gravity:          exact projection onto tangent plane: a = -g * ∇z / (1 + |∇z|²)
    Friction:         Coulomb kinetic, slope-corrected normal force
    Integration:      Velocity-Verlet predictor-corrector
    """

    # Not a dataclass field — hidden from auto-generated UI controls.
    frame_ms: int = 10

    surface_radius:  float = 0.40
    center_radius:   float = 0.05
    surface_tension: float = 10.0
    center_weight:   float = 0.5 * 9.81   # F = m * g  [N]

    time_step: float = 0.005
    num_steps: int   = 5000

    g:               float = 9.81
    particle_radius: float = 0.01

    x0:    float = 0.385
    y0:    float = 0.00
    v_i:   float = 1.0
    theta: float = 45.0

    friction_coef: float = 0.12

    def to_dict(self) -> Dict:
        return asdict(self)

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
            ty = self.x0 / r
        else:
            ry, ty = 0.0, 1.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * ry + sin(th) * ty)


@dataclass
class Newton2dParams:
    """Parameters for the 2D Newtonian orbital simulation.

    Gravity:     F = -G*M*m / r²  (inverse-square)
    Drag:        F = -γ * v        (linear)
    Integration: Velocity-Verlet
    """

    G:     float = 1.0
    M:     float = 1000.0

    r0:        float = 50.0
    v0:        float = 3.0
    theta_deg: float = 90.0

    gamma: float = 0.001

    trail:          int   = 50
    center_radius:  float = 6.0
    particle_radius: float = 2.0

    frame_ms: int   = 10
    dt:       float = 0.02

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SimulationMLParams:
    """Configuration for the ML trajectory demo."""

    # Not a typed field — hidden from auto-generated UI controls.
    frame_ms: int = 30

    test_initial_idx:     int   = 0
    noise_level:          float = 0.0
    marker_size:          int   = 10
    show_true_trajectory: bool  = True

    def to_dict(self) -> Dict:
        return asdict(self)


# Backward-compatible aliases used by legacy gui_Qt imports
Simulation3dParams = Cone3dParams
Simulation2dParams = Newton2dParams

__all__ = [
    "Cone3dParams",
    "Membrane3dParams",
    "Newton2dParams",
    "SimulationMLParams",
    "Simulation3dParams",
    "Simulation2dParams",
]
