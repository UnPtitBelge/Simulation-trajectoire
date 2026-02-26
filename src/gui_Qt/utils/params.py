from dataclasses import asdict, dataclass
from math import cos, radians, sin, sqrt
from typing import Dict


@dataclass
class PlotParams:
    # Geometry / model scaling
    surface_tension: float = 13.0
    surface_radius: float = 0.8
    center_radius: float = 0.05
    center_weight: float = 0.8 * 9.81


@dataclass
class Simulation3dParams:
    # Time integration
    time_step: float = 0.01
    num_steps: int = 800

    # Physical constants
    g: float = 9.81

    # Moving particle (used to offset z in the 3D view so it visually "touches" the surface)
    particle_radius: float = 0.05

    # Initial state (2D)
    x0: float = 0.8
    y0: float = 0.00
    v_i: float = 0.5
    theta: float = 45.0

    # Dissipation
    friction_coef: float = 0.3

    def to_dict(self) -> Dict[str, float | int | bool | str]:
        return asdict(self)

    @property
    def vx0(self) -> float:
        r = sqrt(self.x0 * self.x0 + self.y0 * self.y0)
        if r > 1e-12:
            rx = -self.x0 / r
            tx = -self.y0 / r  # CCW tangential x-component
        else:
            rx, tx = -1.0, 0.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * rx + sin(th) * tx)

    @property
    def vy0(self) -> float:
        r = sqrt(self.x0 * self.x0 + self.y0 * self.y0)
        if r > 1e-12:
            ry = -self.y0 / r
            ty = self.x0 / r  # CCW tangential y-component
        else:
            ry, ty = 0.0, 1.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * ry + sin(th) * ty)


@dataclass
class Simulation2dParams:
    G = 9.81
    M = 1000.0
    r0 = 50.0
    v0 = 10.0
    theta_deg = 90
    gamma = 0.001
    trail = 50
    center_radius = 6.0
    particle_radius = 2.0
    frame_ms = 5
    dt = 0.02
