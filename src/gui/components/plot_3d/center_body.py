"""
center_body.py

Create a Plotly-compatible 3D trace for the central body (sphere) used to visualize
collisions and spatial context in the simulation view.

This module exposes:
- build_center_sphere_trace(...): returns a dict representing a 3D surface trace
  for a sphere centered at (0, 0, z_offset) with a given radius.

The function returns plain Python dicts/lists, suitable for direct use with Dash/Plotly.
"""

from __future__ import annotations

from math import cos, pi, sin
from typing import Any, Dict, List


def build_center_sphere_trace(
    radius: float,
    z_offset: float = 0.0,
    samples_theta: int = 32,
    samples_phi: int = 32,
    name: str = "Center Sphere",
    colorscale: str = "Greys",
    showscale: bool = False,
    opacity: float = 0.8,
) -> Dict[str, Any]:
    """
    Build a parametric sphere surface at the origin (x=0, y=0) with the given radius.

    The sphere center is positioned at z = z_offset, so its lower pole (z = z_offset - radius)
    can be aligned to touch a surface when desired.

    Args:
        radius: Sphere radius (must be > 0).
        z_offset: Vertical offset of the sphere center (default 0.0).
        samples_theta: Number of samples along polar angle theta in [0, pi].
        samples_phi: Number of samples along azimuthal angle phi in [0, 2*pi].
        name: Plotly trace name.
        colorscale: Plotly colorscale for the surface.
        showscale: Whether to show the colorscale legend.
        opacity: Surface opacity (0..1).

    Returns:
        A dict representing a Plotly "surface" trace with x/y/z gridded coordinates.
    """
    samples_theta = max(8, int(samples_theta))
    samples_phi = max(8, int(samples_phi))
    r = float(radius)
    z0 = float(z_offset)

    # Prepare parameterization grids
    thetas = [pi * i / (samples_theta - 1) for i in range(samples_theta)]
    phis = [2.0 * pi * j / (samples_phi - 1) for j in range(samples_phi)]

    X: List[List[float]] = []
    Y: List[List[float]] = []
    Z: List[List[float]] = []

    # Spherical coordinates:
    # x = r * sin(theta) * cos(phi)
    # y = r * sin(theta) * sin(phi)
    # z = z0 + r * cos(theta)
    for ti in range(samples_theta):
        theta = thetas[ti]
        row_x: List[float] = []
        row_y: List[float] = []
        row_z: List[float] = []
        st = sin(theta)
        ct = cos(theta)
        for pj in range(samples_phi):
            phi = phis[pj]
            cphi = cos(phi)
            sphi = sin(phi)
            x = r * st * cphi
            y = r * st * sphi
            z = z0 + r * ct
            row_x.append(x)
            row_y.append(y)
            row_z.append(z)
        X.append(row_x)
        Y.append(row_y)
        Z.append(row_z)

    return {
        "type": "surface",
        "name": name,
        "x": X,
        "y": Y,
        "z": Z,
        "colorscale": colorscale,
        "showscale": showscale,
        "opacity": float(opacity),
    }


__all__ = ["build_center_sphere_trace"]
