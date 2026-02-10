"""
plot_3d package

Public exports for 3D plotting helpers and figure assembly used by the
axisymmetric surface simulation. All functions return plain Python dicts/lists
compatible with Plotly/Dash.

Usage:
    from components.plot_3d import (
        build_trajectory_trace_3d,
        build_surface_trace,
        build_surface_rim_trace,
        build_center_sphere_trace,
        assemble_figure_3d,
    )
"""

from .center_body import build_center_sphere_trace
from .figure import assemble_figure_3d
from .surface import build_surface_rim_trace, build_surface_trace
from .trajectory import build_trajectory_trace_3d

__all__ = [
    "build_trajectory_trace_3d",
    "build_surface_trace",
    "build_surface_rim_trace",
    "build_center_sphere_trace",
    "assemble_figure_3d",
]
