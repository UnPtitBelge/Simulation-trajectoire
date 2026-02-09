"""
2D plot utilities: build a scatter figure containing a round surface (filled disc)
with a filled circle in the center.

- Returns native Python dicts/lists (no Plotly objects) for Dash compatibility.
- Uses `Circle.polygon_points()` / `Circle.circle_points()` to generate 2D points on circles.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .geometry.circle import Circle
from .geometry.surface import RoundSurface

# Default constants for easy tuning of plot parameters
DEFAULT: Dict[str, Any] = {
    "center_radius": 5,
    "center_mass": 1.0,
    "surface_radius": 50,  # multiplier or absolute, used as absolute by default
    "samples": 256,
    "outer_line_color": "rgba(100, 100, 255, 1.0)",
    "outer_line_width": 1.5,
    "outer_fillcolor": "rgba(100, 100, 255, 1.0)",
    "center_line_color": "rgba(255, 80, 80, 1.0)",
    "center_line_width": 2.0,
    "center_fillcolor": "rgba(255, 80, 80, 1.0)",
    "showlegend": False,
    "width": None,
    "height": 480,
}


class Plot2D:
    """
    Minimal 2D plot builder:
    - Generates a circle as a scatter trace from a `Circle` (x, y, radius).
    """

    def __init__(self) -> None:
        # No state required for 2D scatter plots.
        pass

    @staticmethod
    def circle_trace(
        points: List[Tuple[float, float]], name: str = "Circle"
    ) -> Dict[str, Any]:
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
        circle: Circle,
        samples: int = 128,
        title: str = "2D Circle",
        width: int | None = None,
        height: int | None = 420,
    ) -> Dict[str, Any]:
        """
        Build a 2D figure with a single circle trace.

        Args:
            circle: Circle with (x, y, radius) used to generate circle points.
            samples: Number of sample points to approximate the circle.
            title: Figure title.
            width: Optional figure width.
            height: Optional figure height.

        Returns:
            dict: Plotly-compatible figure (data/layout) as native dicts/lists.
        """
        pts = circle.circle_points(n=samples)
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

    def figure_with_surface_and_center(
        self,
        circle: Circle | None = None,
        samples: int | None = None,
        title: str = "Round Surface with Center Circle",
        # Independent tuning of surface (outer disc)
        surface_radius: float | None = None,
        outer_fillcolor: str | None = None,
        outer_line_color: str | None = None,
        outer_line_width: float | None = None,
        # Independent tuning of center "sphere" (circle)
        center_radius: float | None = None,
        center_mass: float | None = None,
        center_fillcolor: str | None = None,
        center_line_color: str | None = None,
        center_line_width: float | None = None,
        showlegend: bool | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> Dict[str, Any]:
        """
        Build a 2D figure with:
          - An outer filled disc ("round surface") centered at the circle's center.
          - A filled inner circle using the provided circle radius.

        Args:
            circle: Center circle (x, y, radius) for the inner filled circle.
            samples: Number of points to approximate both circles.
            title: Figure title.
            outer_radius: Optional radius for the outer disc; defaults to 3x the inner radius.
            outer_fillcolor, outer_line_color, outer_line_width: Styling for the outer disc.
            center_fillcolor, center_line_color, center_line_width: Styling for the inner circle.
            showlegend: Whether to show legend.
            width, height: Optional figure size.

        Returns:
            dict: Plotly-compatible figure (data/layout) as native dicts/lists.
        """
        # Resolve defaults
        samples = int(samples if samples is not None else DEFAULT["samples"])
        showlegend = bool(
            showlegend if showlegend is not None else DEFAULT["showlegend"]
        )
        width = width if width is not None else DEFAULT["width"]
        height = height if height is not None else DEFAULT["height"]

        # Build or update center circle with easy tuning for radius and mass
        if circle is None:
            circle = Circle(
                x=0.0,
                y=0.0,
                radius=float(
                    center_radius
                    if center_radius is not None
                    else DEFAULT["center_radius"]
                ),
                mass=float(
                    center_mass if center_mass is not None else DEFAULT["center_mass"]
                ),
            )
        else:
            if center_radius is not None:
                circle.radius = float(center_radius)
            if center_mass is not None:
                circle.mass = float(center_mass)

        # Surface radius is independent from the center circle
        R_outer = (
            float(surface_radius)
            if surface_radius is not None
            else float(DEFAULT["surface_radius"])
        )

        # Build outer disc using RoundSurface helper
        surf = RoundSurface(x=circle.x, y=circle.y, radius=R_outer, mass=circle.mass)
        outer_trace = surf.as_plotly_scatter(
            n=samples,
            name="Surface",
            mode="lines",
            line_color=(
                outer_line_color
                if outer_line_color is not None
                else DEFAULT["outer_line_color"]
            ),
            line_width=float(
                outer_line_width
                if outer_line_width is not None
                else DEFAULT["outer_line_width"]
            ),
            fill="toself",
            fillcolor=(
                outer_fillcolor
                if outer_fillcolor is not None
                else DEFAULT["outer_fillcolor"]
            ),
            showlegend=showlegend,
        )

        # Build inner filled circle points
        inner_pts = circle.polygon_points(n=samples, include_close=True)
        inner_xs = [p[0] for p in inner_pts]
        inner_ys = [p[1] for p in inner_pts]

        inner_trace: Dict[str, Any] = {
            "type": "scatter",
            "mode": "lines",
            "name": "Center Circle",
            "x": inner_xs,
            "y": inner_ys,
            "fill": "toself",
            "fillcolor": (
                center_fillcolor
                if center_fillcolor is not None
                else DEFAULT["center_fillcolor"]
            ),
            "line": {
                "color": (
                    center_line_color
                    if center_line_color is not None
                    else DEFAULT["center_line_color"]
                ),
                "width": float(
                    center_line_width
                    if center_line_width is not None
                    else DEFAULT["center_line_width"]
                ),
            },
            "showlegend": showlegend,
        }

        layout: Dict[str, Any] = {
            "title": {"text": title},
            "xaxis": {"title": {"text": "x"}, "scaleanchor": "y", "scaleratio": 1},
            "yaxis": {"title": {"text": "y"}},
            "template": "plotly_white",
            "showlegend": showlegend,
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        }
        if width is not None:
            layout["width"] = int(width)
        if height is not None:
            layout["height"] = int(height)

        return {"data": [outer_trace, inner_trace], "layout": layout}

    def default_figure(self) -> Dict[str, Any]:
        """
        Convenience: return a default figure with a round surface and a center circle.
        """
        s = Circle(
            x=0.0,
            y=0.0,
            radius=float(DEFAULT["center_radius"]),
            mass=float(DEFAULT["center_mass"]),
        )
        return self.figure_with_surface_and_center(
            circle=s,
            samples=int(DEFAULT["samples"]),
            title="Round Surface + Center Circle",
            surface_radius=float(DEFAULT["surface_radius"]),
        )


def plot() -> Dict[str, Any]:
    """
    Return a default 2D circle figure as a plain dict.
    """
    return Plot2D().default_figure()


__all__ = ["Plot2D", "plot"]
