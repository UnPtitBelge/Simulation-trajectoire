"""
2D plot utilities: build a scatter figure containing a circle.

- Returns native Python dicts/lists (no Plotly objects) for Dash compatibility.
- Uses `Sphere.circle_points()` to generate 2D points on a circle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from .geometry.sphere import Circle


class Plot2D:
    """
    Minimal 2D plot builder:
    - Generates a circle as a scatter trace from a `Sphere` (x, y, radius).
    """

    def __init__(self) -> None:
        # No state required for 2D scatter plots.
        pass

    @staticmethod
    def circle_trace(points: List[Tuple[float, float]], name: str = "Circle") -> Dict[str, Any]:
        """
        Build a Plotly scatter trace dict from 2D points.

        Args:
            points: List of (x, y) tuples.
            name: Trace name.

        Returns:
            dict: Plotly-compatible scatter trace for a Dash `dcc.Graph`.
        """
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        # Close the loop by appending the first point at the end
        if points:
            xs.append(points[0][0])
            ys.append(points[0][1])

        return {
            "type": "scatter",
            "mode": "lines",
            "name": name,
            "x": xs,
            "y": ys,
            "line": {"width": 2},
        }

    def figure_with_circle(
        self,
        sphere: Circle,
        samples: int = 128,
        title: str = "2D Circle",
        width: int | None = None,
        height: int | None = 420,
    ) -> Dict[str, Any]:
        """
        Build a 2D figure with a single circle trace.

        Args:
            sphere: Sphere with (x, y, radius) used to generate circle points.
            samples: Number of sample points to approximate the circle.
            title: Figure title.
            width: Optional figure width.
            height: Optional figure height.

        Returns:
            dict: Plotly-compatible figure (data/layout) as native dicts/lists.
        """
        pts = sphere.circle_points(n=samples)
        trace = self.circle_trace(pts, name="Circle")

        layout: Dict[str, Any] = {
            "title": {"text": title},
            "xaxis": {"title": {"text": "x"}, "scaleanchor": "y", "scaleratio": 1},
            "yaxis": {"title": {"text": "y"}},
            "template": "plotly_white",
            "showlegend": False,
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        }
        if width is not None:
            layout["width"] = int(width)
        if height is not None:
            layout["height"] = int(height)

        return {"data": [trace], "layout": layout}

    def default_figure(self) -> Dict[str, Any]:
        """
        Convenience: return a default circle centered at the origin with radius 1.0.
        """
        s = Circle(x=0.0, y=0.0, radius=1.0, mass=1.0)
        return self.figure_with_circle(sphere=s, samples=128, title="2D Circle")


def plot() -> Dict[str, Any]:
    """
    Return a default 2D circle figure as a plain dict.
    """
    return Plot2D().default_figure()


__all__ = ["Plot2D", "plot"]
