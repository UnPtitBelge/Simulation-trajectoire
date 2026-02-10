"""
Surface 3D trace builder.

This module provides helpers to render the axisymmetric membrane surface used in the
simulation as a Plotly-compatible 3D trace. It samples z = surface.deformation(r)
on a square grid in (x, y) and masks values outside the membrane radius to produce
a visually circular surface (no square edges).

Exports:
- build_surface_trace(surf, extent, samples=60, name="Surface", colorscale="Viridis", showscale=False, opacity=0.9)
- build_surface_rim_trace(surf, samples=128, name="Surface Rim", color="rgba(50,50,50,0.6)", line_width=2)

Notes:
- Functions return plain Python dicts suitable for Plotly/Dash (no external imports required).
- The caller is responsible for adding the returned dict(s) to the figure's "data" list.
"""

from __future__ import annotations

from math import cos, pi, sin, sqrt
from typing import Any, Dict, List

from .model import deformation


def build_surface_trace(
    params: Any,
    samples: int = 60,
    name: str = "Surface",
    colorscale: str = "Viridis",
    showscale: bool = False,
    opacity: float = 0.9,
) -> Dict[str, Any]:
    """
    Build a minimal 3D surface trace by sampling z = deformation(r, R, T, F, center_radius) over a square grid.

    Args:
        surf: Surface-like object exposing attributes R (radius) and method deformation(r: float) -> float.
        extent: Half-size of the square sampling region; typical choice is surf.R.
        samples: Number of samples per axis (>= 10 recommended).
        name: Trace name.
        colorscale: Plotly colorscale name.
        showscale: Whether to display the colorscale.
        opacity: Trace opacity (0..1).

    Returns:
        dict: Plotly-compatible trace dict with type="surface".
    """
    samples = max(10, int(samples))
    R = float(getattr(params, "surface_radius"))
    T = float(getattr(params, "surface_tension"))
    F = float(getattr(params, "center_weight"))
    center_radius = float(getattr(params, "center_radius"))
    extent = R
    xs = [(-extent + (2.0 * extent) * i / (samples - 1)) for i in range(samples)]
    ys = [(-extent + (2.0 * extent) * j / (samples - 1)) for j in range(samples)]

    Z: List[List[float | None]] = []
    for j in range(samples):
        row: List[float | None] = []
        y = ys[j]
        for i in range(samples):
            x = xs[i]
            r = sqrt(x * x + y * y)
            # Mask outside the membrane to ensure a circular boundary
            if r > R:
                z = None
            else:
                z = float(deformation(r, R=R, T=T, F=F, center_radius=center_radius))
            row.append(z)
        Z.append(row)

    return {
        "type": "surface",
        "name": name,
        "x": xs,
        "y": ys,
        "z": Z,
        "colorscale": colorscale,
        "showscale": showscale,
        "opacity": float(opacity),
    }


def build_surface_rim_trace(
    params: Any,
    samples: int = 128,
    name: str = "Surface Rim",
    color: str = "rgba(50,50,50,0.6)",
    line_width: int = 2,
) -> Dict[str, Any]:
    """
    Build a circular rim (perimeter) trace at r = surf.R for border visualization.

    Args:
        surf: Surface-like object exposing attributes R and method deformation(r).
        samples: Number of angular samples along the rim (>= 32 recommended).
        name: Trace name.
        color: Line color (rgba string).
        line_width: Line width in pixels.

    Returns:
        dict: Plotly-compatible trace dict with type="scatter3d" and mode="lines".
    """
    samples = max(32, int(samples))
    angles = [2.0 * pi * i / samples for i in range(samples + 1)]
    R = float(getattr(params, "surface_radius"))
    T = float(getattr(params, "surface_tension"))
    F = float(getattr(params, "center_weight"))
    center_radius = float(getattr(params, "center_radius"))
    r = R
    z = float(deformation(r, R=R, T=T, F=F, center_radius=center_radius))

    xs = [r * cos(a) for a in angles]
    ys = [r * sin(a) for a in angles]
    zs = [z for _ in angles]

    return {
        "type": "scatter3d",
        "name": name,
        "x": xs,
        "y": ys,
        "z": zs,
        "mode": "lines",
        "line": {"color": color, "width": int(line_width)},
        "showlegend": False,
    }


__all__ = ["build_surface_trace", "build_surface_rim_trace"]
