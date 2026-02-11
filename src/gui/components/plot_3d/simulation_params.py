"""
simulation_params.py

Centralized dataclass for simulation configuration and constants.

This module defines a single dataclass, SimulationParams, that aggregates all
configurable values used across the simulation and plotting components. It helps
centralize defaults and makes it simple to pass a single object around.

All values are plain Python types (floats, ints, bools, strings) to remain
compatible with Dash/Plotly props and internal computation routines.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import cos, radians, sin, sqrt
from typing import Dict


@dataclass
class SimulationParams:
    """
    Centralized configuration for the membrane-sphere simulation.

    Categories:
      - Time integration
      - Physical constants
      - Geometry (central sphere and membrane surface)
      - Initial state (2D)
      - Friction/dissipation
      - Plotting preferences (for convenience)

    Notes:
      - The "central sphere" parameters (radius, weight) define both the visual
        central body and the force magnitude F used in the surface deformation model.
      - The "surface" parameters define a circular membrane with tension T and radius R.
      - Initial state is given in the plane (x, y) with initial speed-angle (v_i, theta).
      - Plotting options are included for convenience when building figures.
    """

    # Time integration
    time_step: float = 0.01  # Integration dt (s)
    num_steps: int = 800  # Total number of Euler steps

    # Physical constants (SI-like)
    g: float = 9.81  # Gravity magnitude (m/s^2)

    # Geometry: central body (used for collision + deformation model scaling)
    center_radius: float = 0.05  # Central sphere radius (m)
    center_weight: float = 0.5 * 9.81  # Central sphere weight (N) = m * g
    # Geometry: moving particle (trajectory adhesion offset)
    particle_radius: float = 0.01  # Small sphere radius (m) used to offset trajectory z so it adheres to the surface

    # Surface (membrane)
    surface_tension: float = 10.0  # Membrane tension T (N/m or arbitrary units)
    surface_radius: float = 0.5  # Membrane radius R (m)

    # Initial state (2D)
    x0: float = 0.490  # Initial x position (m)
    y0: float = 0.00  # Initial y position (m)
    v_i: float = 0.5  # Initial speed magnitude (m/s)
    theta: float = (
        45  # Angle (degrees) between inward radial unit vector and initial velocity
    )

    # Dissipation
    friction_coef: float = 0.3  # Friction coefficient (dimensionless; scaled in model)

    # Plotting preferences (convenience; used by figure builders)
    plot_title: str = "3D Simulation"
    plot_template: str = "plotly_white"
    plot_showlegend: bool = False
    plot_margin_left: int = 0
    plot_margin_right: int = 0
    plot_margin_top: int = 40
    plot_margin_bottom: int = 0
    plot_samples_surface: int = 36
    plot_rim_samples: int = 64
    plot_traj_line_width: float = 2.0
    plot_traj_marker_size: float = 2.0
    # Animation preferences
    plot_step_interval_ms: int = 30
    plot_traj_color: str = "rgba(50,50,180,1.0)"
    plot_surface_colorscale: str = "Viridis"
    plot_surface_opacity: float = 0.9
    plot_rim_color: str = "rgba(50,50,50,0.6)"
    plot_center_sphere_colorscale: str = "Greys"
    plot_center_sphere_opacity: float = 0.8

    # Reserved for future extensions (kept to preserve forward compatibility)
    extras: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, float | int | bool | str]:
        """
        Return a plain dict representation of the parameters suitable for JSON/Dash.
        """
        return asdict(self)

    @property
    def vx0(self) -> float:
        """
        Derived initial x-velocity from (v_i, theta) relative to inward radial unit vector.
        """
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
        """
        Derived initial y-velocity from (v_i, theta) relative to inward radial unit vector.
        """
        r = sqrt(self.x0 * self.x0 + self.y0 * self.y0)
        if r > 1e-12:
            ry = -self.y0 / r
            ty = self.x0 / r  # CCW tangential y-component
        else:
            ry, ty = 0.0, 1.0
        th = radians(self.theta)
        return self.v_i * (cos(th) * ry + sin(th) * ty)


__all__ = ["SimulationParams"]
