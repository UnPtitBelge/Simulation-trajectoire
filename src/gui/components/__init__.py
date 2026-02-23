"""
components package

Convenient exports for geometry primitives, simulation utilities, and 3D plotting helpers.
All figures and utilities return plain Python dicts/lists compatible with Dash/Plotly.

Usage:
    from components import (
        plot_sim_3d,
    )
"""

# Navbar
from .navbar import navbar

# 3D plotting helpers
from .plot_3d import plot as plot_sim_3d

__all__ = [
    # Plotting
    "plot_sim_3d",
    # Nav
    "navbar",
]
