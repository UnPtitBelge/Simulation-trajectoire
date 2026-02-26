"""Dataclasses for plot and simulation parameters.

This module defines simple dataclasses that hold configuration parameters for
the different simulation views (plot-level, 2D, 3D and ML). These dataclasses
are used by the UI controller code to automatically generate controls and to
pass values into the simulation/plot implementations.

Keep these classes as plain dataclasses so tools like `dataclasses.fields()` can
discover their fields for dynamic UI generation.
"""

from dataclasses import asdict, dataclass
from math import cos, radians, sin, sqrt
from typing import Dict


@dataclass
class PlotParams:
    """Plot-level parameters used to scale and style visual elements."""

    # Geometry / model scaling
    surface_tension: float = 13.0
    surface_radius: float = 0.8
    center_radius: float = 0.05
    center_weight: float = 0.8 * 9.81


@dataclass
class Simulation3dParams:
    """Parameters controlling the 3D simulation and initial conditions."""

    # Time integration
    time_step: float = 0.01
    num_steps: int = 800

    # Physical constants
    g: float = 9.81

    # Moving particle (used to offset z in the 3D view so it visually "touches" the surface)
    particle_radius: float = 0.05

    # Initial state (2D projected)
    x0: float = 0.8
    y0: float = 0.00
    v_i: float = 0.5
    theta: float = 45.0

    # Dissipation
    friction_coef: float = 0.3

    def to_dict(self) -> Dict[str, float | int | bool | str]:
        """Return a plain dict representation of the params (helper)."""
        return asdict(self)

    @property
    def vx0(self) -> float:
        """Computed initial x-velocity from polar decomposition of (x0, y0) and theta."""
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
        """Computed initial y-velocity from polar decomposition of (x0, y0) and theta."""
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
    """Parameters for the 2D (planar) simulation.

    These values are intentionally simple numeric fields used by the simulation
    code and exposed in the UI for tuning.
    """

    G: float = 9.81
    M: float = 1000.0
    r0: float = 50.0
    v0: float = 10.0
    theta_deg: float = 90
    gamma: float = 0.001
    trail: int = 50
    center_radius: float = 6.0
    particle_radius: float = 2.0
    frame_ms: int = 5
    dt: float = 0.02


@dataclass
class SimulationMLParams:
    """
    Parameters for the machine-learning simulation visualization.

    - frame_ms: milliseconds between animation frames
    - test_initial_idx: index of the training sample to use for prediction/visualization
    - retrain_on_update: whether to retrain the model when params are updated
    - model_type: integer identifier of model to use (e.g. 0 == linear)
    - noise_level: synthetic noise level to add to predictions (for demo purposes)
    - marker_size: size (pixels) of the moving marker shown on the ML plot
    """

    frame_ms: int = 100
    test_initial_idx: int = 0
    retrain_on_update: bool = False
    model_type: int = 0  # 0 == Linear
    noise_level: float = 0.0
    marker_size: int = 10
