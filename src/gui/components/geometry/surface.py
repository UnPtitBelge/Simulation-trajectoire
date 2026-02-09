# Simulation-systeme-solaire/src/gui/components/geometry/surface.py
"""
Minimal Surface geometry utilities.

This module defines a simplified `Surface` class that:
- Builds a rectilinear (x, y) grid over a specified domain and resolution.
- Provides helpers to generate a flat Z heightfield (e.g., a plane at z=0 or any constant).
- Exposes plotting helpers to produce a Plotly-compatible "surface" trace and a 3D layout.
- Avoids any curvature/potential logic and any concept of "Source".
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple


class Surface:
    """
    Rectilinear surface grid and minimal plotting helpers.

    Parameters:
        x_range: (xmin, xmax) of the domain.
        y_range: (ymin, ymax) of the domain.
        resolution: (nx, ny) number of grid points along x and y.

    Notes:
        - The grid is defined by linearly spaced coordinates over x_range and y_range.
        - Z-values are plain Python lists so they are compatible with Dash props.
        - This class does NOT compute curvature or potentials.
    """

    def __init__(
        self,
        x_range: Tuple[float, float] = (-5.0, 5.0),
        y_range: Tuple[float, float] = (-5.0, 5.0),
        resolution: Tuple[int, int] = (60, 60),
    ) -> None:
        self.xmin, self.xmax = float(x_range[0]), float(x_range[1])
        self.ymin, self.ymax = float(y_range[0]), float(y_range[1])
        self.nx, self.ny = int(resolution[0]), int(resolution[1])
        if self.nx < 2 or self.ny < 2:
            raise ValueError("resolution must be at least (2, 2)")

        # Precompute 1D axes
        self._xs: List[float] = self._linspace(self.xmin, self.xmax, self.nx)
        self._ys: List[float] = self._linspace(self.ymin, self.ymax, self.ny)

    @staticmethod
    def _linspace(a: float, b: float, n: int) -> List[float]:
        if n == 1:
            return [a]
        step = (b - a) / float(n - 1)
        return [a + i * step for i in range(n)]

    @property
    def xs(self) -> List[float]:
        """Return the x-axis coordinates as a 1D list of length nx."""
        return self._xs

    @property
    def ys(self) -> List[float]:
        """Return the y-axis coordinates as a 1D list of length ny."""
        return self._ys

    # -----------------------------
    # Plotly helpers
    # -----------------------------
    def as_plotly_surface(
        self,
        colorscale: str = "Viridis",
        showscale: bool = True,
        opacity: Optional[float] = None,
        name: str = "Surface",
    ) -> Dict[str, object]:
        """



        Args:
            Z: 2D list of shape (ny, nx) from `flat_z` or any custom generator.
            colorscale: Plotly colorscale name.
            showscale: Whether to show the color bar.
            opacity: Optional opacity for the surface (0..1).
            name: Trace name.

        Returns:
            dict representing a Plotly surface trace compatible with Dash.
        """
        trace: Dict[str, object] = {
            "type": "surface",
            "name": name,
            "x": self._xs,
            "y": self._ys,
            "z": Z,
            "colorscale": colorscale,
            "showscale": showscale,
        }
        if opacity is not None:
            trace["opacity"] = float(opacity)
        return trace

    def default_layout_3d(
        self,
        title: str = "Surface",
        width: Optional[int] = None,
        height: int = 500,
        template: str = "plotly_white",
        aspectmode: str = "cube",
        margin: Tuple[int, int, int, int] = (0, 0, 0, 0),
        x_title: str = "x",
        y_title: str = "y",
        z_title: str = "z",
    ) -> Dict[str, object]:
        """
        Provide a simple 3D layout dict for Plotly figures.
        """
        ml, mr, mt, mb = margin
        layout: Dict[str, object] = {
            "title": {"text": title},
            "scene": {
                "xaxis": {"title": {"text": x_title}},
                "yaxis": {"title": {"text": y_title}},
                "zaxis": {"title": {"text": z_title}},
                "aspectmode": aspectmode,
            },
            "template": template,
            "margin": {"l": ml, "r": mr, "t": mt, "b": mb},
        }
        if width is not None:
            layout["width"] = int(width)
        if height is not None:
            layout["height"] = int(height)
        return layout
