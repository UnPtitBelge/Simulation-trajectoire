"""
sim_3d.py

Animated 3D simulation figure (Plotly-compatible dict) using frames.

Keeps the API similar to plot_2d modules:
- build_animated_figure_3d(...) builds and returns a figure dict
- plot(...) is a convenience wrapper using default parameters

Rendering traces (surface / rim / center sphere / moving particle) are built locally
to avoid spreading the 3D plotting logic across many small modules.
"""

from __future__ import annotations

from math import cos, pi, sin, sqrt
from typing import Any, Dict, List, Optional

from utils.ui.plots import build_layout

from .iterations import iterations
from .model import deformation
from .simulation_params import SimulationParams


def _moving_particle_trace(
    x: float,
    y: float,
    z: float,
    *,
    name: str = "Particle",
    color: str = "rgba(200, 50, 50, 1.0)",
    size: float = 6.0,
) -> Dict[str, Any]:
    return {
        "type": "scatter3d",
        "name": name,
        "x": [float(x)],
        "y": [float(y)],
        "z": [float(z)],
        "mode": "markers",
        "marker": {"size": float(size), "color": color},
        "showlegend": False,
    }


def _surface_trace(
    params: SimulationParams,
    *,
    samples: int = 60,
    name: str = "Surface",
    colorscale: str = "Viridis",
    showscale: bool = False,
    opacity: float = 0.9,
) -> Dict[str, Any]:
    samples = max(10, int(samples))
    R = float(params.surface_radius)
    T = float(params.surface_tension)
    F = float(params.center_weight)
    center_radius = float(params.center_radius)

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
        "showscale": bool(showscale),
        "opacity": float(opacity),
        "showlegend": False,
    }


def _rim_trace(
    params: SimulationParams,
    *,
    samples: int = 128,
    name: str = "Surface Rim",
    color: str = "rgba(50,50,50,0.6)",
    line_width: int = 2,
) -> Dict[str, Any]:
    samples = max(32, int(samples))
    R = float(params.surface_radius)
    T = float(params.surface_tension)
    F = float(params.center_weight)
    center_radius = float(params.center_radius)

    angles = [2.0 * pi * i / samples for i in range(samples + 1)]
    z = float(deformation(R, R=R, T=T, F=F, center_radius=center_radius))

    xs = [R * cos(a) for a in angles]
    ys = [R * sin(a) for a in angles]
    zs = [z for _ in angles]

    return {
        "type": "scatter3d",
        "name": name,
        "x": xs,
        "y": ys,
        "z": zs,
        "mode": "lines",
        "line": {"color": str(color), "width": int(line_width)},
        "showlegend": False,
    }


def _center_sphere_trace(
    params: SimulationParams,
    *,
    samples_theta: int = 32,
    samples_phi: int = 32,
    name: str = "Center Sphere",
    colorscale: str = "Greys",
    showscale: bool = False,
    opacity: float = 0.8,
) -> Dict[str, Any]:
    samples_theta = max(8, int(samples_theta))
    samples_phi = max(8, int(samples_phi))

    R = float(params.surface_radius)
    T = float(params.surface_tension)
    F = float(params.center_weight)
    center_radius = float(params.center_radius)

    center_z0 = float(deformation(0.0, R=R, T=T, F=F, center_radius=center_radius))
    z_offset = center_z0 + center_radius

    thetas = [pi * i / (samples_theta - 1) for i in range(samples_theta)]
    phis = [2.0 * pi * j / (samples_phi - 1) for j in range(samples_phi)]

    X: List[List[float]] = []
    Y: List[List[float]] = []
    Z: List[List[float]] = []

    for theta in thetas:
        st = sin(theta)
        ct = cos(theta)
        row_x: List[float] = []
        row_y: List[float] = []
        row_z: List[float] = []
        for phi in phis:
            cphi = cos(phi)
            sphi = sin(phi)
            x = center_radius * st * cphi
            y = center_radius * st * sphi
            z = z_offset + center_radius * ct
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
        "colorscale": str(colorscale),
        "showscale": bool(showscale),
        "opacity": float(opacity),
        "showlegend": False,
    }


def _base_traces(
    params: SimulationParams,
    *,
    surface_samples: int,
    rim_samples: int,
    surface_colorscale: str,
    surface_opacity: float,
    rim_color: str,
    center_sphere_colorscale: str,
    center_sphere_opacity: float,
) -> List[Dict[str, Any]]:
    surface = _surface_trace(
        params,
        samples=int(surface_samples),
        name="Surface",
        colorscale=str(surface_colorscale),
        opacity=float(surface_opacity),
        showscale=False,
    )
    rim = _rim_trace(
        params,
        samples=int(rim_samples),
        name="Surface Rim",
        color=str(rim_color),
        line_width=2,
    )
    center_sphere = _center_sphere_trace(
        params,
        samples_theta=32,
        samples_phi=32,
        name="Center Sphere",
        colorscale=str(center_sphere_colorscale),
        opacity=float(center_sphere_opacity),
        showscale=False,
    )
    return [surface, rim, center_sphere]


def build_animated_figure_3d(
    params: Optional[SimulationParams] = None,
    *,
    # Rendering / animation options (plot_2d-like: passed as function args, not stored in params)
    title: str = "3D Simulation",
    template: str = "plotly_white",
    showlegend: bool = False,
    margin: Optional[Dict[str, int]] = None,
    surface_samples: int = 60,
    rim_samples: int = 128,
    max_frames: int = 600,
    step_interval_ms: int = 30,
    particle_color: str = "rgba(200, 50, 50, 1.0)",
    particle_marker_size: float = 8.0,
    surface_colorscale: str = "Viridis",
    surface_opacity: float = 0.9,
    rim_color: str = "rgba(50,50,50,0.6)",
    center_sphere_colorscale: str = "Greys",
    center_sphere_opacity: float = 0.8,
) -> Dict[str, Any]:
    params = params or SimulationParams()
    results = iterations(params)

    xs: List[float] = list(results.get("xs", []))
    ys: List[float] = list(results.get("ys", []))
    zs: List[float] = list(results.get("zs", []))

    base_traces = _base_traces(
        params,
        surface_samples=int(surface_samples),
        rim_samples=int(rim_samples),
        surface_colorscale=str(surface_colorscale),
        surface_opacity=float(surface_opacity),
        rim_color=str(rim_color),
        center_sphere_colorscale=str(center_sphere_colorscale),
        center_sphere_opacity=float(center_sphere_opacity),
    )

    particle_radius = float(params.particle_radius)

    if xs and ys and zs:
        start_x, start_y, start_z = xs[0], ys[0], zs[0] + particle_radius
    else:
        start_x, start_y, start_z = float(params.x0), float(params.y0), particle_radius

    moving_particle = _moving_particle_trace(
        start_x,
        start_y,
        start_z,
        name="Particle",
        color=str(particle_color),
        size=float(particle_marker_size),
    )

    max_frames = max(1, int(max_frames))
    n_points = len(xs)
    stride = max(1, n_points // max_frames)

    frames: List[Dict[str, Any]] = []
    for i in range(0, n_points, stride):
        frames.append(
            {
                "name": f"f{i}",
                "data": [
                    _moving_particle_trace(
                        xs[i],
                        ys[i],
                        zs[i] + particle_radius,
                        name="Particle",
                        color=str(particle_color),
                        size=float(particle_marker_size),
                    )
                ],
                "traces": [len(base_traces)],
            }
        )

    steps_run = int(results.get("steps_run", len(xs)))
    layout: Dict[str, Any] = build_layout(
        title=f"{title} — steps: {steps_run}",
        template=str(template),
        showlegend=bool(showlegend),
        margin=margin if margin is not None else {"l": 0, "r": 0, "t": 40, "b": 0},
    )

    layout["uirevision"] = "keep"
    layout["scene"] = {
        "xaxis": {"title": {"text": "x"}},
        "yaxis": {"title": {"text": "y"}},
        "zaxis": {"title": {"text": "z"}},
        "aspectmode": "data",
    }

    frame_ms = int(step_interval_ms)
    layout["updatemenus"] = [
        {
            "type": "buttons",
            "showactive": False,
            "x": 0,
            "y": 1,
            "xanchor": "left",
            "yanchor": "top",
            "pad": {"r": 10, "t": 10},
            "buttons": [
                {
                    "label": "▶",
                    "method": "animate",
                    "args": [
                        None,
                        {
                            "frame": {"duration": frame_ms, "redraw": True},
                            "fromcurrent": True,
                            "transition": {"duration": 0},
                            "mode": "immediate",
                        },
                    ],
                }
            ],
        },
        {
            "type": "buttons",
            "showactive": False,
            "x": 0,
            "y": 1,
            "xanchor": "left",
            "yanchor": "top",
            "pad": {"l": 50, "t": 10},
            "buttons": [
                {
                    "label": "⏸",
                    "method": "animate",
                    "args": [
                        [None],
                        {
                            "frame": {"duration": 0, "redraw": False},
                            "mode": "immediate",
                            "transition": {"duration": 0},
                        },
                    ],
                }
            ],
        },
    ]
    layout["sliders"] = []

    return {
        "data": base_traces + [moving_particle],
        "layout": layout,
        "frames": frames,
    }


def plot(step_interval_ms: Optional[int] = None) -> Dict[str, Any]:
    return build_animated_figure_3d(
        SimulationParams(),
        step_interval_ms=30 if step_interval_ms is None else int(step_interval_ms),
    )
