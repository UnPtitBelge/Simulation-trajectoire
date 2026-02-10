"""
components package

Convenient exports for geometry primitives, simulation utilities, and 3D plotting helpers.
All figures and utilities return plain Python dicts/lists compatible with Dash/Plotly.

Usage:
    from components import (
        SimulationParams, iterations,
        build_figure_3d, plot_3d,
    )
"""

# Navbar
from .navbar import navbar

# 3D plotting helpers
from .plot_3D import build_figure_3d as build_figure_3d
from .plot_3D import plot as plot_3d
from .sim_3d import plot as plot_sim_3d

__all__ = [
    # Plotting
    "build_figure_3d",
    "plot_3d",
    "plot_sim_3d",
    # Nav
    "navbar",
]
