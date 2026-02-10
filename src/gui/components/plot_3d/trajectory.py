"""
trajectory.py

Minimal builder for a 3D trajectory trace (Plotly-compatible dict).

This module provides a single function `build_trajectory_trace_3d` that takes
x, y, z sequences and returns a dict suitable for inclusion in a Plotly figure.
It aims to keep the plotting layer simple and independent of Plotly's Python API,
using only native Python types (dicts/lists).

Usage:
    from .trajectory import build_trajectory_trace_3d

    trace = build_trajectory_trace_3d(xs, ys, zs, name="Trajectory")

Notes:
- This module does not import Plotly; it returns plain dicts for Dash/Plotly props.
- Default styling emphasizes visibility for small particles (lines+markers).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def build_trajectory_trace_3d(
    xs: Iterable[float],
    ys: Iterable[float],
    zs: Iterable[float],
    *,
    name: str = "Trajectory",
    line_color: str = "rgba(50, 50, 180, 1.0)",
    line_width: float = 4.0,
    marker_size: float = 6.0,
    marker_color: Optional[str] = None,
    showlegend: bool = False,
) -> Dict[str, Any]:
    """
    Build a minimal 3D trajectory trace dict (Plotly-compatible).

    Args:
        xs, ys, zs: Sequences of positions along the trajectory.
        name: Trace name.
        line_color: Color for the trajectory line (rgba or hex).
        line_width: Width of the trajectory line.
        marker_size: Size of markers along the trajectory.
        marker_color: Optional color for markers (defaults to line_color).
        showlegend: Whether the trace should be shown in the legend.

    Returns:
        A dict representing a Plotly scatter3d trace suitable for figure["data"].
    """
    x_list = list(xs)
    y_list = list(ys)
    z_list = list(zs)

    trace: Dict[str, Any] = {
        "type": "scatter3d",
        "name": name,
        "x": x_list,
        "y": y_list,
        "z": z_list,
        "mode": "lines+markers",
        "line": {"color": line_color, "width": float(line_width)},
        "marker": {
            "size": float(marker_size),
            "color": marker_color if marker_color is not None else line_color,
        },
        "showlegend": bool(showlegend),
    }
    return trace


__all__ = ["build_trajectory_trace_3d"]
