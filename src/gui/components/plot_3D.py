"""
Simple 3D plotting wrapper for the axisymmetric surface simulation.

This module delegates figure construction to the `plot_3d` package for clarity and
modularity. It exposes the same public API as before:

- build_figure_3d(params=None): run iterations() and return a Plotly-compatible 3D figure dict
- plot(): convenience entry that uses default SimulationParams

Parameters:
- Accepts either the local SimulationParams (components.simulation.SimulationParams)
  or the centralized plot_3d SimulationParams (components.plot_3d.simulation_params.SimulationParams).

All returns are plain Python dicts/lists compatible with Dash/Plotly.
"""

from __future__ import annotations

from typing import Any, Dict

from .plot_3d.figure import assemble_figure_3d
from .plot_3d.iterations import iterations
from .plot_3d.simulation_params import SimulationParams as Plot3DSimulationParams


def build_figure_3d(
    params: Plot3DSimulationParams | None = None,
) -> Dict[str, Any]:
    """
    Run the simulation (iterations) and return a Plotly-compatible 3D figure dict.

    Args:
        params: Optional SimulationParams. If None, a default instance is used.

    Returns:
        dict: A figure with keys "data" (list of traces) and "layout" (figure layout).
    """
    # If no params provided, use centralized plot_3d SimulationParams
    if params is None:
        params = Plot3DSimulationParams()

    # Use centralized SimulationParams directly with iterations
    result = iterations(params)
    return assemble_figure_3d(
        params=params,
        result=result,
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        showlegend=False,
        title_prefix="3D Simulation",
    )


def plot() -> Dict[str, Any]:
    """
    Convenience entry point returning a 3D figure dict built from default parameters.
    """
    return build_figure_3d()


__all__ = ["build_figure_3d", "plot"]
