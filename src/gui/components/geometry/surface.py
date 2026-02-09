# Simulation-trajectoire/src/gui/components/geometry/surface.py
"""
Geometry surfaces: a generic 2D `Surface` base class and a concrete `RoundSurface`
subclass representing a filled disc (round surface).

This module is 2D-focused and returns native Python dicts/lists that are directly
compatible with Plotly/Dash without requiring Plotly objects.

Classes:
- Surface: Abstract/generic 2D surface interface (center, bbox, sampling, Plotly helpers).
- RoundSurface(Surface): Concrete 2D circular surface (disc) with geometry and plotting utilities.

Typical usage:
    from .surface import RoundSurface

    surf = RoundSurface(x=0.0, y=0.0, radius=3.0)
    area = surf.area()
    bbox = surf.bbox()
    inside = surf.contains_point(1.0, 1.0)

    # Plot helpers
    shape = surf.as_plotly_shape(fillcolor="rgba(100,100,255,0.25)")
    trace = surf.as_plotly_scatter(n=512, name="Surface", fillcolor="rgba(100,100,255,0.25)")
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Surface:
    """
    Generic 2D surface interface.

    This base class provides common attributes and a consistent API for 2D surfaces.
    Concrete subclasses must implement geometry-specific methods.

    Attributes:
        x, y (float): Center coordinates of the surface in 2D.
        mass (float): Optional mass parameter (kept for consistency with other geometry classes).

    Subclasses should implement:
        - bbox() -> (xmin, ymin, xmax, ymax)
        - contains_point(px, py, inclusive=True) -> bool
        - polygon_points(n=256, include_close=True) -> List[(x, y)]
        - area() -> float
        - circumference() -> float

    Plotly helpers provided here rely on `bbox()` and `polygon_points(...)`.
    """

    x: float = 0.0
    y: float = 0.0
    mass: float = 1.0

    # --- Basic getters -----------------------------------------------------

    def center(self) -> Tuple[float, float]:
        """Return the center as (x, y)."""
        return (float(self.x), float(self.y))

    # --- Geometry (to be implemented by subclasses) -----------------------

    def bbox(self) -> Tuple[float, float, float, float]:
        """
        Axis-aligned bounding box that encloses the surface.

        Subclasses must implement this.
        """
        raise NotImplementedError("Surface.bbox must be implemented by subclasses")

    def contains_point(self, px: float, py: float, inclusive: bool = True) -> bool:
        """
        Test whether point (px, py) lies inside the surface.

        Subclasses must implement this.
        """
        raise NotImplementedError(
            "Surface.contains_point must be implemented by subclasses"
        )

    def polygon_points(
        self, n: int = 256, include_close: bool = True
    ) -> List[Tuple[float, float]]:
        """
        Return points approximating the surface boundary as a polygon.

        Subclasses must implement this.
        """
        raise NotImplementedError(
            "Surface.polygon_points must be implemented by subclasses"
        )

    def area(self) -> float:
        """Return the area of the surface."""
        raise NotImplementedError("Surface.area must be implemented by subclasses")

    def circumference(self) -> float:
        """Return the perimeter/length of the surface boundary."""
        raise NotImplementedError(
            "Surface.circumference must be implemented by subclasses"
        )

    # --- Plotly helpers (generic) -----------------------------------------

    def as_plotly_shape(
        self,
        line_color: str = "rgba(80, 80, 80, 0.9)",
        line_width: float = 1.5,
        fillcolor: Optional[str] = None,
        opacity: Optional[float] = None,
        name: Optional[str] = None,
        editable: Optional[bool] = None,
        layer: Optional[str] = None,
        xref: str = "x",
        yref: str = "y",
    ) -> Dict[str, Any]:
        """
        Create a Plotly layout shape dict to render this surface on a 2D Cartesian axis.

        By default, uses the bounding box as an ellipse shape, which works for circular
        and elliptical surfaces. Subclasses can override for specialized rendering.

        Args:
            line_color: Stroke color.
            line_width: Stroke width.
            fillcolor: Fill color (None to omit).
            opacity: Shape opacity (0..1, None to omit).
            name: Optional name (not part of legends; kept for downstream usage).
            editable: Whether the shape is editable (if supported).
            layer: Rendering layer ("above" or "below"), if supported.
            xref, yref: Axis references.

        Returns:
            dict suitable for inclusion in a Plotly figure layout "shapes" list.
        """
        xmin, ymin, xmax, ymax = self.bbox()
        shape: Dict[str, Any] = {
            "type": "circle",  # Works for circles; for generic surfaces this is a best-effort ellipse
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
            shape["name"] = str(name)
        return shape

    def as_plotly_scatter(
        self,
        n: int = 512,
        name: str = "Surface",
        mode: str = "lines",
        line_color: str = "rgba(80, 80, 80, 0.9)",
        line_width: float = 1.5,
        fill: Optional[str] = "toself",
        fillcolor: Optional[str] = None,
        showlegend: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Plotly scatter trace dict rendering the surface boundary (polygon approximation)
        with optional fill for a solid appearance.

        Args:
            n: Number of points along the boundary.
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
        """Return a minimal dict representation of the surface."""
        return {"x": float(self.x), "y": float(self.y), "mass": float(self.mass)}


# ---------------------------------------------------------------------------


@dataclass
class RoundSurface(Surface):
    """
    2D round surface (disc) centered at (x, y) with radius `radius`.

    Attributes:
        x, y (float): Center coordinates.
        radius (float): Disc radius (≥ 0).
        mass (float): Optional mass parameter.

    Geometry utilities provided:
        - center() -> (x, y)
        - area() -> float
        - circumference() -> float
        - bbox() -> (xmin, ymin, xmax, ymax)
        - contains_point(px, py, inclusive=True) -> bool
        - distance_to_center(px, py) -> float
        - polygon_points(n=256, include_close=True) -> List[(x, y)]

    Plotly helpers specialize the base class for circular rendering:
        - as_plotly_shape(...) uses type="circle" with the disc bbox.
        - as_plotly_scatter(...) renders a filled perimeter polygon.

    Notes:
        - Designed for 2D plotting and geometry utilities.
        - Returns plain dicts/lists suitable for Dash/Plotly JSON props.
    """

    radius: float = 1.0

    # --- Geometry ----------------------------------------------------------

    def area(self) -> float:
        """Return the area of the disc (π r^2)."""
        r = max(0.0, float(self.radius))
        return pi * r * r

    def circumference(self) -> float:
        """Return the circumference (perimeter) of the disc boundary (2 π r)."""
        r = max(0.0, float(self.radius))
        return 2.0 * pi * r

    def bbox(self) -> Tuple[float, float, float, float]:
        """
        Axis-aligned bounding box that encloses the disc.

        Returns:
            (xmin, ymin, xmax, ymax)
        """
        cx, cy = self.center()
        r = max(0.0, float(self.radius))
        return (cx - r, cy - r, cx + r, cy + r)

    def distance_to_center(self, px: float, py: float) -> float:
        """Euclidean distance from point (px, py) to disc center."""
        cx, cy = self.center()
        dx, dy = float(px) - cx, float(py) - cy
        return sqrt(dx * dx + dy * dy)

    def contains_point(self, px: float, py: float, inclusive: bool = True) -> bool:
        """
        Test whether point (px, py) lies inside the disc.

        Args:
            px, py: Point coordinates.
            inclusive: If True, points on the boundary are considered inside.

        Returns:
            True if inside (or on boundary when inclusive=True).
        """
        d = self.distance_to_center(px, py)
        r = max(0.0, float(self.radius))
        return d <= r if inclusive else d < r

    def polygon_points(
        self, n: int = 256, include_close: bool = True
    ) -> List[Tuple[float, float]]:
        """
        Generate 2D points approximating the disc boundary as a regular polygon.

        Args:
            n: Number of samples around the disc boundary (≥ 3 recommended).
            include_close: If True, repeat the first point at the end to close the polygon.

        Returns:
            List of (x, y) points on the polygon approximating the circle boundary.
        """
        n = max(3, int(n))
        cx, cy = self.center()
        r = max(0.0, float(self.radius))
        step = 2.0 * pi / float(n)
        pts = [(cx + r * cos(i * step), cy + r * sin(i * step)) for i in range(n)]
        if include_close:
            pts.append(pts[0])
        return pts

    # --- Plotly helpers (override for clarity) -----------------------------

    def as_plotly_shape(
        self,
        line_color: str = "rgba(100, 100, 255, 0.6)",
        line_width: float = 1.5,
        fillcolor: Optional[str] = "rgba(100, 100, 255, 0.25)",
        opacity: Optional[float] = None,
        name: Optional[str] = None,
        editable: Optional[bool] = None,
        layer: Optional[str] = None,
        xref: str = "x",
        yref: str = "y",
    ) -> Dict[str, Any]:
        """
        Create a Plotly layout shape dict to render this disc on a 2D Cartesian axis.
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
            shape["name"] = str(name)
        return shape

    def as_plotly_scatter(
        self,
        n: int = 512,
        name: str = "Surface",
        mode: str = "lines",
        line_color: str = "rgba(100, 100, 255, 1.0)",
        line_width: float = 1.5,
        fill: Optional[str] = "toself",
        fillcolor: Optional[str] = "rgba(100, 100, 255, 1.0)",
        showlegend: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Plotly scatter trace dict rendering the disc boundary (polygon approximation)
        with optional fill for a solid appearance.
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
        """Return a minimal dict representation of the round surface."""
        base = super().to_dict()
        base["radius"] = float(self.radius)
        return base


__all__ = ["Surface", "RoundSurface"]
