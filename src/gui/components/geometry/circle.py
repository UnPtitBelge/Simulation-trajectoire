# Simulation-trajectoire/src/gui/components/geometry/circle.py
"""
2D circle geometry primitives for visualization and simple motion.

This module defines:
- Circle: a basic geometric circle with helpers to generate 2D points for plotting and geometry utils.
- DynamicCircle(Circle): adds simple 2D motion integration utilities.

Typical usage:
    from .circle import Circle, DynamicCircle

    # Build a 2D circle
    c = Circle(x=0.0, y=0.0, radius=1.0)

    # Get geometry helpers
    area = c.area()
    length = c.circumference()
    bbox = c.bbox()
    inside = c.contains_point(0.5, 0.0)

    # Get a polygonal approximation for plotting
    pts = c.polygon_points(n=128, include_close=True)

    # Plotly 2D helpers
    shape = c.as_plotly_shape(line_color="red", fillcolor="rgba(255,0,0,0.2)")
    scatter = c.as_plotly_scatter(n=256, name="circle_outline")

    # Optional: animate a DynamicCircle with naive integration
    dyn = DynamicCircle(x=2.0, y=0.0, vx=0.0, vy=0.8, radius=0.5, mass=1.0)
    dyn.step(dt=0.05, acceleration=lambda s: (0.0, 0.0))

Notes:
- Motion integration is intentionally simple (symplectic Euler) for qualitative demos.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class Circle:
    """
    Simple geometric circle with minimal parameters.

    Attributes:
        x, y (float): Center coordinates in 2D.
        radius (float): Radius (≥ 0).
        mass (float): Optional mass parameter for the object (arbitrary units).

    Core geometry helpers:
        - center() -> (x, y)
        - area() -> float
        - circumference() -> float
        - bbox() -> (xmin, ymin, xmax, ymax)
        - contains_point(px, py, inclusive=True) -> bool
        - distance_to_center(px, py) -> float
        - polygon_points(n=64, include_close=False) -> List[(x, y)]
        - circle_points(n=64) -> List[(x, y)]  (alias to polygon_points without closing)
        - as_plotly_shape(...) -> Dict[str, Any]
        - as_plotly_scatter(...) -> Dict[str, Any]
    """

    x: float = 0.0
    y: float = 0.0
    radius: float = 1.0
    mass: float = 1.0

    # --- Basic getters -----------------------------------------------------

    def center(self) -> Tuple[float, float]:
        """Return the center of the circle as (x, y)."""
        return (float(self.x), float(self.y))

    # --- Geometry ----------------------------------------------------------

    def area(self) -> float:
        """Return the area of the circle (π r^2)."""
        r = max(0.0, float(self.radius))
        return pi * r * r

    def circumference(self) -> float:
        """Return the circumference (perimeter) of the circle (2 π r)."""
        r = max(0.0, float(self.radius))
        return 2.0 * pi * r

    def bbox(self) -> Tuple[float, float, float, float]:
        """
        Axis-aligned bounding box that encloses the circle.

        Returns:
            (xmin, ymin, xmax, ymax)
        """
        cx, cy = self.center()
        r = max(0.0, float(self.radius))
        return (cx - r, cy - r, cx + r, cy + r)

    def distance_to_center(self, px: float, py: float) -> float:
        """Euclidean distance from point (px, py) to circle center."""
        cx, cy = self.center()
        dx, dy = float(px) - cx, float(py) - cy
        return sqrt(dx * dx + dy * dy)

    def contains_point(self, px: float, py: float, inclusive: bool = True) -> bool:
        """
        Test whether point (px, py) lies inside the circle.

        Args:
            px, py: Point coordinates.
            inclusive: If True, points on the boundary are considered inside.

        Returns:
            True if inside (or on boundary when inclusive=True).
        """
        d = self.distance_to_center(px, py)
        r = max(0.0, float(self.radius))
        return d <= r if inclusive else d < r

    # --- Sampling ----------------------------------------------------------

    def polygon_points(
        self, n: int = 64, include_close: bool = False
    ) -> List[Tuple[float, float]]:
        """
        Generate 2D points approximating the circle as a regular polygon.

        Args:
            n: Number of samples around the circle (≥ 3 recommended).
            include_close: If True, repeat the first point at the end to close the polygon.

        Returns:
            List of (x, y) points on the polygon approximating the circle, suitable for 2D plotting.
        """
        n = max(3, int(n))
        cx, cy = self.center()
        r = max(0.0, float(self.radius))
        step = 2.0 * pi / float(n)
        pts = [(cx + r * cos(i * step), cy + r * sin(i * step)) for i in range(n)]
        if include_close:
            pts.append(pts[0])
        return pts

    def circle_points(self, n: int = 64) -> List[Tuple[float, float]]:
        """
        Alias for polygon_points(n, include_close=False).

        Returns:
            List of (x, y) points on the circle perimeter.
        """
        return self.polygon_points(n=n, include_close=False)

    # --- Plotly helpers (2D) ----------------------------------------------

    def as_plotly_shape(
        self,
        line_color: str = "rgba(200, 0, 0, 1.0)",
        line_width: float = 2.0,
        fillcolor: Optional[str] = None,
        opacity: Optional[float] = None,
        name: Optional[str] = None,
        editable: Optional[bool] = None,
        layer: Optional[str] = None,
        xref: str = "x",
        yref: str = "y",
    ) -> Dict[str, Any]:
        """
        Create a Plotly layout shape dict to render this circle on a 2D Cartesian axis.

        This uses the "circle" shape with center (x, y) and size via bbox.

        Args:
            line_color: Stroke color.
            line_width: Stroke width.
            fillcolor: Fill color (None to omit).
            opacity: Shape opacity (0..1, None to omit).
            name: Optional name (supported in newer Plotly versions via `label` plugin; kept here for completeness).
            editable: Whether the shape is editable (if supported).
            layer: Rendering layer ("above" or "below"), if supported.
            xref, yref: Axis references.

        Returns:
            dict suitable for inclusion in a Plotly figure layout "shapes" list.
        """
        xmin, ymin, xmax, ymax = self.bbox()
        shape: Dict[str, Any] = {
            "type": "circle",
            "xref": xref,
            "yref": yref,
            "x0": xmin,
            "y0": ymin,
            "x1": xmax,
            "y1": ymax,
            "line": {"color": line_color, "width": float(line_width)},
        }
        if fillcolor is not None:
            shape["fillcolor"] = fillcolor
        if opacity is not None:
            shape["opacity"] = float(opacity)
        if editable is not None:
            shape["editable"] = bool(editable)
        if layer is not None:
            shape["layer"] = str(layer)
        if name is not None:
            # Plotly shapes do not have a native "name" field for legends;
            # include as a customdata-style tag for downstream usage.
            shape["name"] = str(name)
        return shape

    def as_plotly_scatter(
        self,
        n: int = 128,
        name: str = "Circle",
        mode: str = "lines",
        line_color: str = "rgba(200, 0, 0, 1.0)",
        line_width: float = 2.0,
        fill: Optional[str] = None,
        fillcolor: Optional[str] = None,
        showlegend: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Plotly scatter trace dict rendering the circle outline (polygon approximation).

        Args:
            n: Number of points along the perimeter.
            name: Trace name.
            mode: Plotly scatter mode; typically "lines".
            line_color: Stroke color.
            line_width: Stroke width.
            fill: Plotly fill mode (e.g. "toself") or None to omit.
            fillcolor: Fill color when using fill.
            showlegend: Whether to show legend.

        Returns:
            dict suitable for inclusion in a Plotly figure "data" list.
        """
        pts = self.polygon_points(n=n, include_close=True)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        trace: Dict[str, Any] = {
            "type": "scatter",
            "name": name,
            "x": xs,
            "y": ys,
            "mode": mode,
            "line": {"color": line_color, "width": float(line_width)},
            "showlegend": bool(showlegend),
        }
        if fill is not None:
            trace["fill"] = str(fill)
        if fillcolor is not None:
            trace["fillcolor"] = str(fillcolor)
        return trace

    # --- Serialization -----------------------------------------------------

    def to_dict(self) -> Dict[str, float]:
        """Return a minimal dict representation of the circle."""
        return {
            "x": float(self.x),
            "y": float(self.y),
            "radius": float(self.radius),
            "mass": float(self.mass),
        }


@dataclass
class DynamicCircle(Circle):
    """
    Circle with simple motion integration in 2D.

    Attributes:
        vx, vy (float): Velocity components.

    Methods:
        - state() -> Dict[str, float]
        - step(dt, acceleration, method="symplectic-euler")
        - step_with_sources(sources, dt, method="symplectic-euler")
          Note: sources-based acceleration is deprecated and returns zero.
    """

    vx: float = 0.0
    vy: float = 0.0

    def state(self) -> Dict[str, float]:
        """Return a dictionary with position and velocity."""
        return {
            "x": float(self.x),
            "y": float(self.y),
            "vx": float(self.vx),
            "vy": float(self.vy),
            "radius": float(self.radius),
            "mass": float(self.mass),
        }

    def step(
        self,
        dt: float,
        acceleration: Optional[Callable[[DynamicCircle], Tuple[float, float]]] = None,
        method: str = "symplectic-euler",
    ) -> None:
        """
        Advance the circle's position/velocity by dt.

        Args:
            dt: Time step (seconds or arbitrary time units).
            acceleration: Function that returns (ax, ay) given the current circle.
                          If None, uses zero acceleration.
            method: Integration method. Currently only "symplectic-euler" is provided.

        Notes:
            Symplectic Euler:
                v_{t+dt} = v_t + a(x_t) * dt
                x_{t+dt} = x_t + v_{t+dt} * dt
        """
        ax, ay = (0.0, 0.0)
        if acceleration is not None:
            ax, ay = acceleration(self)

        if method != "symplectic-euler":
            # Fallback to symplectic-euler for unknown methods
            method = "symplectic-euler"

        # Update velocity first, then position
        self.vx += float(ax) * dt
        self.vy += float(ay) * dt

        self.x += self.vx * dt
        self.y += self.vy * dt


__all__ = ["Circle", "DynamicCircle"]
