"""
Figure assembly for 3D simulation using standardized layout.

This module builds a Plotly-compatible figure dict for the axisymmetric membrane simulation:
- Surface (membrane) as a 3D surface sampled on a square grid, masked outside circular boundary.
- Center sphere positioned so its bottom touches the surface at r=0.
- Trajectory of the small sphere with markers, Z offset so bottom touches the surface.
- Optional circular rim at r=R to improve border visibility.

All returns are plain Python dicts/lists (Dash-friendly). The figure layout uses
the shared UI standardization via utils.ui.plots.build_layout.
"""

from __future__ import annotations

from math import cos, pi, sin, sqrt
from typing import Any, Dict, List, Optional, Sequence

from .model import deformation
from .surface import build_surface_trace as build_surface_trace_polar

# Standardized layout builder
try:
    from utils.ui.plots import build_layout
except Exception:
    # Fallback minimal layout builder if shared utils are not available
    def build_layout(
        title: str = "Figure",
        width: Optional[int] = None,
        height: Optional[int] = None,
        showlegend: Optional[bool] = None,
        xaxis: Optional[Dict[str, Any]] = None,
        yaxis: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None,
        margin: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        layout: Dict[str, Any] = {"title": {"text": title}}
        if width is not None:
            layout["width"] = int(width)
        if height is not None:
            layout["height"] = int(height)
        if showlegend is not None:
            layout["showlegend"] = bool(showlegend)
        if xaxis is not None:
            layout["xaxis"] = xaxis
        if yaxis is not None:
            layout["yaxis"] = yaxis
        if template is not None:
            layout["template"] = template
        if margin is not None:
            layout["margin"] = margin
        return layout


# -----------------------------------------------------------------------------
# Trace builders (plain dicts)
# -----------------------------------------------------------------------------


def build_trajectory_trace(
    xs: Sequence[float],
    ys: Sequence[float],
    zs: Sequence[float],
    name: str = "Trajectory",
    color: str = "rgba(50,50,180,1.0)",
    line_width: float = 2.0,
    marker_size: float = 3.0,
) -> Dict[str, Any]:
    """
    Build a minimal 3D scatter trace for the trajectory (lines + markers).
    """
    return {
        "type": "scatter3d",
        "name": name,
        "x": list(xs),
        "y": list(ys),
        "z": list(zs),
        "mode": "lines+markers",
        "line": {"color": color, "width": float(line_width)},
        "marker": {"size": float(marker_size), "color": color},
        "showlegend": False,
    }


def build_surface_trace(
    surf: Any,
    extent: float,
    samples: int = 60,
    name: str = "Surface",
    colorscale: str = "Viridis",
    opacity: float = 0.9,
    showscale: bool = False,
) -> Dict[str, Any]:
    """
    Build a 3D surface trace by sampling z = deformation(r) over a square grid.

    - Grid spans [-extent, extent] in both x and y.
    - Values outside the circular boundary (r > R) are masked (z=None),
      ensuring the rendered surface looks circular (no square edges).

    Args:
        surf: Surface-like object exposing R (radius) and deformation(r)->z.
        extent: Half-size of the sampling square (use surf.R).
        samples: Number of points per axis (>= 10).
    """
    samples = max(10, int(samples))
    xs = [(-extent + (2 * extent) * i / (samples - 1)) for i in range(samples)]
    ys = [(-extent + (2 * extent) * j / (samples - 1)) for j in range(samples)]

    Z: List[List[Optional[float]]] = []
    for j in range(samples):
        row: List[Optional[float]] = []
        y = ys[j]
        for i in range(samples):
            x = xs[i]
            r = sqrt(x * x + y * y)
            if r > surf.R:
                z = None  # Mask outside the membrane disc
            else:
                z = float(surf.deformation(r))
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


def build_center_sphere_trace(
    radius: float,
    z_offset: float = 0.0,
    samples_theta: int = 32,
    samples_phi: int = 32,
    name: str = "Center Sphere",
    colorscale: str = "Greys",
    opacity: float = 0.8,
    showscale: bool = False,
) -> Dict[str, Any]:
    """
    Build a parametric sphere surface centered at (0,0,z_offset) with the given radius.

    Sphere parameterization:
        x = R * sin(theta) * cos(phi)
        y = R * sin(theta) * sin(phi)
        z = z_offset + R * cos(theta)
    where theta ∈ [0, π], phi ∈ [0, 2π].
    """
    samples_theta = max(8, int(samples_theta))
    samples_phi = max(8, int(samples_phi))

    thetas = [pi * i / (samples_theta - 1) for i in range(samples_theta)]
    phis = [2.0 * pi * j / (samples_phi - 1) for j in range(samples_phi)]

    X: List[List[float]] = []
    Y: List[List[float]] = []
    Z: List[List[float]] = []
    for theta in thetas:
        row_x: List[float] = []
        row_y: List[float] = []
        row_z: List[float] = []
        for phi in phis:
            x = radius * sin(theta) * cos(phi)
            y = radius * sin(theta) * sin(phi)
            z = z_offset + radius * cos(theta)
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


def build_rim_trace(
    radius: float,
    z: float,
    samples: int = 128,
    name: str = "Surface Rim",
    color: str = "rgba(50,50,50,0.6)",
    line_width: float = 2.0,
) -> Dict[str, Any]:
    """
    Build a circular rim trace at r=radius, z constant, to visualize the border of the surface.
    """
    samples = max(32, int(samples))
    angles = [2.0 * pi * i / samples for i in range(samples + 1)]
    xs = [radius * cos(a) for a in angles]
    ys = [radius * sin(a) for a in angles]
    zs = [z for _ in angles]
    return {
        "type": "scatter3d",
        "name": name,
        "x": xs,
        "y": ys,
        "z": zs,
        "mode": "lines",
        "line": {"color": color, "width": float(line_width)},
        "showlegend": False,
    }


# -----------------------------------------------------------------------------
# Figure assembly
# -----------------------------------------------------------------------------


def assemble_figure_3d(
    params: Any,
    result: Dict[str, Any],
    *,
    template: str = "plotly_white",
    margin: Optional[Dict[str, int]] = None,
    showlegend: bool = False,
    title_prefix: str = "3D Simulation",
) -> Dict[str, Any]:
    """
    Assemble a full 3D figure dict from simulation params and result.

    Expects:
      - params.surface: object with R and deformation(r)
      - params.surface.sphere.R: center sphere radius
      - result: dict with "xs", "ys", "zs", "steps_run"

    Behavior:
      - Uses standardized build_layout()
      - Positions center sphere at z = deformation(0) + R so the bottom touches the surface.
      - Offsets trajectory Z by +R so the small sphere's bottom touches the surface.
      - Adds an optional rim trace for clearer border visualization.
    """
    xs: List[float] = list(result.get("xs", []))
    ys: List[float] = list(result.get("ys", []))
    zs: List[float] = list(result.get("zs", []))
    steps_run: int = int(result.get("steps_run", 0))

    # Surface trace using centralized params (no geometry objects)
    R = float(getattr(params, "surface_radius"))
    extent = R
    surface = build_surface_trace_polar(params, samples=60, name="Surface")

    # Center sphere trace (at origin), z-offset so its bottom touches the surface at r=0
    center_radius = float(getattr(params, "center_radius"))
    T = float(getattr(params, "surface_tension"))
    R = float(getattr(params, "surface_radius"))
    F = float(getattr(params, "center_weight"))
    center_z0 = float(deformation(0.0, R=R, T=T, F=F, center_radius=center_radius))
    center_sphere = build_center_sphere_trace(
        radius=center_radius, z_offset=center_z0 + center_radius
    )

    # Trajectory (offset Z so the particle visually adheres to the surface)
    particle_radius = float(getattr(params, "particle_radius", center_radius))
    offset_zs = [z + particle_radius for z in zs]
    traj = build_trajectory_trace(xs, ys, offset_zs, line_width=2.0, marker_size=3.0)

    # Rim at r=R using centralized params and shared model
    rim_z = float(deformation(extent, R=R, T=T, F=F, center_radius=center_radius))
    rim = build_rim_trace(radius=extent, z=rim_z)

    # Layout (standardized)
    layout: Dict[str, Any] = build_layout(
        title=f"{title_prefix} — steps: {steps_run}",
        template=template,
        showlegend=showlegend,
        margin=margin if margin is not None else {"l": 0, "r": 0, "t": 40, "b": 0},
    )
    layout["scene"] = {
        "xaxis": {"title": {"text": "x"}},
        "yaxis": {"title": {"text": "y"}},
        "zaxis": {"title": {"text": "z"}},
        "aspectmode": "data",
    }

    return {"data": [surface, rim, center_sphere, traj], "layout": layout}


__all__ = [
    "build_trajectory_trace",
    "build_surface_trace",
    "build_center_sphere_trace",
    "build_rim_trace",
    "assemble_figure_3d",
]
