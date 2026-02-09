"""
utils.ui.plots

Plot-related defaults and layout builder for the Dash app.

Exports:
- PLOT_DEFAULTS: Shared defaults used by figure builders.
- build_layout: Helper to produce a Plotly-compatible layout dict with sensible defaults.

Notes:
- Returns plain Python dicts/lists for easy Dash JSON prop compatibility.
- Centralizing defaults here allows consistent styling across all figures.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# Plot defaults (dict-based, Plotly-compatible) used by graph figure builders
PLOT_DEFAULTS: Dict[str, Any] = {
    "samples": 256,
    "width": None,  # If None, do not set width in layout (let the container size prevail)
    "height": 480,  # A sensible default height for most figures
    "template": "plotly_white",
    "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
    "xaxis": {"title": {"text": "x"}, "scaleanchor": "y", "scaleratio": 1},
    "yaxis": {"title": {"text": "y"}},
    "showlegend": False,
}


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
    """
    Build a standardized Plotly layout dict with sensible defaults.

    Args:
        title: Title text.
        width, height: Optional size; falls back to PLOT_DEFAULTS when None.
        showlegend: Toggle legend visibility; falls back to PLOT_DEFAULTS.
        xaxis, yaxis: Axis config; falls back to PLOT_DEFAULTS when None.
        template: Plotly template name; falls back to PLOT_DEFAULTS.
        margin: Dict with "l","r","t","b" (ints); falls back to PLOT_DEFAULTS.

    Returns:
        A dict ready to assign to figure["layout"].
    """
    layout: Dict[str, Any] = {
        "title": {"text": title},
        "xaxis": xaxis if xaxis is not None else PLOT_DEFAULTS["xaxis"],
        "yaxis": yaxis if yaxis is not None else PLOT_DEFAULTS["yaxis"],
        "template": template if template is not None else PLOT_DEFAULTS["template"],
        "showlegend": showlegend
        if showlegend is not None
        else PLOT_DEFAULTS["showlegend"],
        "margin": margin if margin is not None else PLOT_DEFAULTS["margin"],
    }

    # Apply explicit width/height if provided, otherwise use defaults (when not None)
    if width is not None:
        layout["width"] = int(width)
    elif PLOT_DEFAULTS["width"] is not None:
        layout["width"] = int(PLOT_DEFAULTS["width"])  # type: ignore[arg-type]

    if height is not None:
        layout["height"] = int(height)
    elif PLOT_DEFAULTS["height"] is not None:
        layout["height"] = int(PLOT_DEFAULTS["height"])  # type: ignore[arg-type]

    return layout


__all__ = ["PLOT_DEFAULTS", "build_layout"]
