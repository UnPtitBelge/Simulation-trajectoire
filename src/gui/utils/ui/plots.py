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
