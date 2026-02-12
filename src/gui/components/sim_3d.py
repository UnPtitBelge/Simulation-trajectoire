"""
sim_3d.py

Create an animated 3D trajectory figure (Plotly-compatible dict) using frames.
The animation reuses the rendering components (surface, rim, center sphere, trajectory)
and advances a moving marker along the simulated path.

Usage:
    from .sim_3d import build_animated_figure_3d, plot

Notes:
- Returns plain Python dicts/lists for Dash/Plotly compatibility.
- Uses the centralized SimulationParams and plot_3d.iterations for the motion.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from utils.ui.plots import build_layout

from .plot_3d.figure import (
    build_center_sphere_trace,
    build_rim_trace,
)
from .plot_3d.iterations import iterations
from .plot_3d.simulation_params import SimulationParams
from .plot_3d.surface import build_surface_trace


def _moving_particle_trace(
    x: float,
    y: float,
    z: float,
    name: str = "Particle",
    color: str = "rgba(200, 50, 50, 1.0)",
    size: float = 6.0,
) -> Dict[str, Any]:
    """
    Return a minimal scatter3d trace representing the moving particle as a single marker.
    """
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


def _base_traces(
    params: SimulationParams, results: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Build static base traces: surface, rim, center sphere.
    """
    # Surface (grid sampling masked outside radius; circular boundary)
    surface = build_surface_trace(
        params, samples=int(getattr(params, "plot_samples_surface", 60)), name="Surface"
    )

    # Rim at r=R
    R = float(params.surface_radius)
    T = float(params.surface_tension)
    F = float(params.center_weight)
    center_radius = float(params.center_radius)
    # For rim z, reuse deformation via surface trace builder's parameters and a single call:
    # build_rim_trace will compute z using shared model through surface builder inputs.
    # Here we simply pass r=R and z from deformation evaluated within the builder.
    # Since build_rim_trace expects radius and z directly, compute z consistently:
    from .plot_3d.model import deformation

    rim_z = deformation(R, R=R, T=T, F=F, center_radius=center_radius)
    rim = build_rim_trace(
        radius=R,
        z=rim_z,
        samples=int(getattr(params, "plot_rim_samples", 128)),
        name="Surface Rim",
        color=str(getattr(params, "plot_rim_color", "rgba(50,50,50,0.6)")),
        line_width=2.0,
    )

    # Center sphere at z = deformation(0) + center_radius
    center_z0 = deformation(0.0, R=R, T=T, F=F, center_radius=center_radius)
    center_sphere = build_center_sphere_trace(
        radius=center_radius,
        z_offset=center_z0 + center_radius,
        samples_theta=32,
        samples_phi=32,
        name="Center Sphere",
        colorscale=str(getattr(params, "plot_center_sphere_colorscale", "Greys")),
        opacity=float(getattr(params, "plot_center_sphere_opacity", 0.8)),
        showscale=False,
    )

    return [surface, rim, center_sphere]


def build_animated_figure_3d(
    params: Optional[SimulationParams] = None,
    step_interval_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build an animated 3D figure dict with:
      - Static traces: surface, rim, center sphere, trajectory lines
      - Animated moving marker along the trajectory (frames)
      - Play/Pause controls and a slider

    Args:
        params: Optional SimulationParams; if None, uses defaults.
        step_interval_ms: Frame duration in milliseconds for the animation.

    Returns:
        A Plotly-compatible figure dict with "data", "layout", "frames".
    """
    params = params or SimulationParams()
    # Run iterations to get trajectory
    results = iterations(params)

    # Base static traces
    base_traces = _base_traces(params, results)

    xs: List[float] = list(results.get("xs", []))
    ys: List[float] = list(results.get("ys", []))
    zs: List[float] = list(results.get("zs", []))
    center_radius = float(params.center_radius)
    particle_radius = float(getattr(params, "particle_radius", center_radius))

    # Initial marker position (first step or origin if empty)
    if xs and ys and zs:
        start_x, start_y, start_z = xs[0], ys[0], zs[0] + particle_radius
    else:
        start_x, start_y, start_z = float(params.x0), float(params.y0), particle_radius

    moving_particle = _moving_particle_trace(
        start_x,
        start_y,
        start_z,
        name="Particle",
        color="rgba(200, 50, 50, 1.0)",
        size=float(getattr(params, "plot_traj_marker_size", 6.0)) + 2.0,
    )

    # Build frames: adapt stride so total frames <= max_frames
    max_frames = int(getattr(params, "plot_max_frames", 600))
    n_points = len(xs)
    stride = max(1, n_points // max_frames)  # at least 1
    frames: List[Dict[str, Any]] = []
    for i in range(0, n_points, stride):
        fx = xs[i]
        fy = ys[i]
        fz = zs[i] + particle_radius
        frame = {
            "name": f"f{i}",
            "data": [
                _moving_particle_trace(
                    fx,
                    fy,
                    fz,
                    name="Particle",
                    color="rgba(200, 50, 50, 1.0)",
                    size=float(getattr(params, "plot_traj_marker_size", 6.0)) + 2.0,
                )
            ],
            "traces": [len(base_traces)],
        }
        frames.append(frame)

    # Layout (standardized) with scene and animation controls
    steps_run = int(results.get("steps_run", len(xs)))
    frame_ms = (
        int(step_interval_ms)
        if step_interval_ms is not None
        else int(getattr(params, "plot_step_interval_ms", 30))
    )
    layout: Dict[str, Any] = build_layout(
        title=f"{getattr(params, 'plot_title', '3D Simulation')} — steps: {steps_run}",
        template=str(getattr(params, "plot_template", "plotly_white")),
        showlegend=bool(getattr(params, "plot_showlegend", False)),
        margin={
            "l": int(getattr(params, "plot_margin_left", 0)),
            "r": int(getattr(params, "plot_margin_right", 0)),
            "t": int(getattr(params, "plot_margin_top", 40)),
            "b": int(getattr(params, "plot_margin_bottom", 0)),
        },
    )
    # Preserve user camera/zoom/rotation across updates
    layout["uirevision"] = "keep"
    layout["scene"] = {
        "xaxis": {"title": {"text": "x"}},
        "yaxis": {"title": {"text": "y"}},
        "zaxis": {"title": {"text": "z"}},
        "aspectmode": "data",
    }
    # Add animation controls (updatemenus and sliders)
    layout["updatemenus"] = [
        {
            "type": "buttons",
            "showactive": False,
            "buttons": [
                {
                    "label": "Play",
                    "method": "animate",
                    "args": [
                        None,
                        {
                            "frame": {
                                "duration": frame_ms,
                                "redraw": True,
                            },
                            "fromcurrent": True,
                            "transition": {"duration": 0},
                        },
                    ],
                },
                {
                    "label": "Pause",
                    "method": "animate",
                    "args": [
                        [None],
                        {
                            "frame": {"duration": 0, "redraw": False},
                            "mode": "immediate",
                            "transition": {"duration": 0},
                        },
                    ],
                },
            ],
        }
    ]

    # Remove steps slider for cleaner UI; keep play/pause controls
    layout["sliders"] = []

    # Assemble final figure dict
    figure = {
        "data": base_traces + [moving_particle],
        "layout": layout,
        "frames": frames,
    }
    return figure


def plot(step_interval_ms: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience entry point returning an animated 3D figure dict with default parameters.
    """
    return build_animated_figure_3d(
        SimulationParams(), step_interval_ms=step_interval_ms
    )
