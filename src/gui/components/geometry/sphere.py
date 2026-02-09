# Simulation-systeme-solaire/src/gui/components/geometry/sphere.py
"""
Circle geometry primitives for simple 2D visualization and motion.

This module defines:
- Circle: a basic geometric circle with helpers to generate 2D points for plotting.
- DynamicCircle(Circle): adds simple 2D motion integration utilities for demonstration purposes.

Design choices:
- Plain Python only (no NumPy) to keep dependencies minimal and Dash-prop friendly (native lists/dicts).
- 2D-only: no dependence on z-coordinates.

Typical usage:
    from .sphere import Circle, DynamicCircle

    # Build a 2D circle
    c = Circle(x=0.0, y=0.0, radius=1.0)

    # Optional: get 2D points to display the circle
    pts = c.circle_points(n=128)

    # Optional: animate a DynamicCircle with naive integration
    dyn = DynamicCircle(x=2.0, y=0.0, vx=0.0, vy=0.8, radius=0.5, mass=1.0)
    dyn.step(dt=0.05, acceleration=lambda s: (0.0, 0.0))

Note:
- The motion integration here is intentionally simple (symplectic Euler).
  It’s meant for a qualitative demo, not high-precision physics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

# Local import; `Surface` defines a `Source` dataclass that we reuse here
try:
    from .surface import Source
except Exception:  # pragma: no cover - fallback type for static checkers
    @dataclass
    class Source:  # type: ignore
        x: float
        y: float
        mass: float
        softening: float = 0.0


@dataclass
class Circle:
    """
    Simple geometric circle with minimal parameters.

    Attributes:
        x, y (float): Center coordinates in 2D (z optional for legacy compatibility).
        radius (float): Radius (≥ 0).
        mass (float): Mass parameter for the object (arbitrary units).

    Methods:
        center() -> Tuple[float, float, float]: Return (x, y, z).
        circle_points(n=64) -> List[Tuple[float,float]]:
            Generate 2D circle points (x, y) around the center for plotting in 2D.
        mesh(n_phi=24, n_theta=36) -> Tuple[List[List[float]], ...]:
            3D mesh generator retained for compatibility; can be ignored in 2D contexts.
        as_plotly_surface(...) -> Dict[str, Any]:
            3D visualization helper retained for compatibility; can be ignored in 2D contexts.
    """
    x: float = 0.0
    y: float = 0.0
    radius: float = 1.0
    mass: float = 1.0

    def center(self) -> Tuple[float, float]:
        return (float(self.x), float(self.y))

    def circle_points(self, n: int = 64) -> List[Tuple[float, float]]:
        """
        Generate 2D circle points centered at (x, y) with radius `radius`.

        Args:
            n: Number of samples around the circle (≥ 3 recommended).

        Returns:
            List of (x, y) points on the circle, suitable for 2D plotting.
        """
        n = max(3, int(n))
        cx, cy = float(self.x), float(self.y)
        r = max(0.0, float(self.radius))
        step = 2.0 * pi / float(n)
        return [(cx + r * cos(i * step), cy + r * sin(i * step)) for i in range(n)]

    def mesh(
        self,
        n_phi: int = 24,
        n_theta: int = 36,
    ) -> Tuple[List[List[float]], List[List[float]], List[List[float]]]:
        """
        Generate a parametric sphere mesh centered at (x, y).

        Args:
            n_phi: Number of samples in polar angle φ ∈ [0, π] (vertical).
            n_theta: Number of samples in azimuth θ ∈ [0, 2π] (horizontal).

        Returns:
            (X, Y, Z): Each a 2D list with shape (n_phi, n_theta).
                       Suitable for a Plotly "surface" trace.
        """
        n_phi = max(2, int(n_phi))
        n_theta = max(3, int(n_theta))
        r = max(0.0, float(self.radius))
        cx, cy, cz = self.center()

        def linspace(a: float, b: float, n: int) -> List[float]:
            if n == 1:
                return [a]
            step = (b - a) / float(n - 1)
            return [a + i * step for i in range(n)]

        # Open interval variant: excludes the end point (useful to avoid duplicate
        # seam columns for theta in [0, 2π] when building a surface mesh).
        def linspace_open(a: float, b: float, n: int) -> List[float]:
            n = max(1, int(n))
            step = (b - a) / float(n)
            return [a + i * step for i in range(n)]

        phis = linspace(0.0, pi, n_phi)
        thetas = linspace_open(0.0, 2.0 * pi, n_theta)

        X: List[List[float]] = []
        Y: List[List[float]] = []
        Z: List[List[float]] = []
        for ip, phi in enumerate(phis):
            row_x: List[float] = []
            row_y: List[float] = []
            row_z: List[float] = []
            sp, cp = sin(phi), cos(phi)
            for it, th in enumerate(thetas):
                sth, cth = sin(th), cos(th)
                row_x.append(cx + r * sp * cth)
                row_y.append(cy + r * sp * sth)
                row_z.append(cz + r * cp)
            X.append(row_x)
            Y.append(row_y)
            Z.append(row_z)
        return X, Y, Z

    def as_plotly_surface(
        self,
        n_phi: int = 24,
        n_theta: int = 36,
        colorscale: str = "Reds",
        showscale: bool = False,
        opacity: Optional[float] = 1.0,
        name: str = "Sphere",
    ) -> Dict[str, Any]:
        """
        Create a Plotly "surface" trace dict to render this sphere.

        Note: This is a geometric mesh, not the potential surface.

        Args:
            n_phi, n_theta: Mesh resolution (see `mesh`).
            colorscale: Plotly colorscale for the surface.
            showscale: Whether to display the colorbar.
            opacity: Surface opacity (0..1). Use None to omit the key.
            name: Trace name.

        Returns:
            dict suitable for inclusion in a Plotly figure "data" list.
        """
        X, Y, Z = self.mesh(n_phi=n_phi, n_theta=n_theta)
        trace: Dict[str, Any] = {
            "type": "surface",
            "name": name,
            "x": X,
            "y": Y,
            "z": Z,
            "colorscale": colorscale,
            "showscale": showscale,
        }
        if opacity is not None:
            trace["opacity"] = float(opacity)
        return trace


@dataclass
class DynamicCircle(Circle):
    """
    Circle with simple motion integration in 2D.

    Attributes:
        vx, vy, vz (float): Velocity components.

    Methods:
        step(dt, acceleration): Advance state by dt using a provided acceleration
                                function a = f(self) -> (ax, ay, az).
        acceleration_from_sources(sources, G=1.0, z0=0.0) -> Tuple[float, float, float]:
            Deprecated placeholder returning zero acceleration.
        step_with_sources(sources, dt, G=1.0, z0=0.0, method="symplectic-euler"):
            Advance state using acceleration computed from sources.
    """
    vx: float = 0.0
    vy: float = 0.0

    def state(self) -> Dict[str, float]:
        return {
            "x": float(self.x),
            "y": float(self.y),
            "vx": float(self.vx),
            "vy": float(self.vy),
        }

    def step(
        self,
        dt: float,
        acceleration: Optional[Callable[[DynamicCircle], Tuple[float, float]]] = None,
        method: str = "symplectic-euler",
    ) -> None:
        """
        Advance the sphere's position/velocity by dt.

        Args:
            dt: Time step (seconds or arbitrary time units).
            acceleration: Function that returns (ax, ay, az) given the current sphere.
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
            # Fallback to symplectic-euler for unknown methods for simplicity
            method = "symplectic-euler"

        # Update velocity first, then position
        self.vx += float(ax) * dt
        self.vy += float(ay) * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

    def acceleration_from_sources(
        self,
        sources: Iterable[object],
        G: float = 1.0,
    ) -> Tuple[float, float]:
        """
        Deprecated: potential-based acceleration has been removed.
        This method returns zero acceleration to keep the API minimally compatible.
        """
        return (0.0, 0.0)

    def step_with_sources(
        self,
        sources: Iterable[object],
        dt: float,
        G: float = 1.0,
        method: str = "symplectic-euler",
    ) -> None:
        """
        Integrate motion for dt using acceleration derived from `sources`.

        Args:
            sources: Iterable of potential sources.
            dt: Time step.
            G: Gravitational constant scale.

            method: Integration method (only "symplectic-euler" supported).

        Behavior:
            Uses `acceleration_from_sources` to compute a single-step acceleration
            and then calls `step(...)`.
        """
        a = self.acceleration_from_sources(sources, G=G)

        def a_fn(_self: DynamicCircle) -> Tuple[float, float]:  # noqa: ANN001
            return a

        self.step(dt=dt, acceleration=a_fn, method=method)


__all__ = ["Circle", "DynamicCircle"]
