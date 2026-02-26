import numpy as np
from surface_field import SurfaceField


class CentralBody:
    """
    Generic central body representation for mesh rendering on a curved surface.

    This class provides a parametric sphere (X, Y, Z) centered at the origin,
    with its Z coordinates offset by the surface height at (0, 0). It keeps
    backward-compatibility properties used elsewhere in the codebase.

    Parameters:
        radius (float): Radius of the central body (≥ 0).
        mass (float): Mass of the central body (arbitrary units).
    """

    def __init__(self, radius: float, mass: float):
        self._radius = float(radius)
        self._mass = float(mass)
        self._u = np.linspace(0.0, 2.0 * np.pi, 40)
        self._v = np.linspace(0.0, np.pi, 20)

        # Parametric sphere centered at origin; z lifted by surface height at (0, 0)
        r = self._radius
        self._X = r * np.outer(np.cos(self._u), np.sin(self._v))
        self._Y = r * np.outer(np.sin(self._u), np.sin(self._v))
        self._Z = r * np.outer(np.ones_like(self._u), np.cos(self._v)) + SurfaceField.h(
            0.0, 0.0
        )

    # --- Generic properties -------------------------------------------------
    @property
    def radius(self) -> float:
        return self._radius

    @property
    def mass(self) -> float:
        return self._mass

    @property
    def X(self):
        return self._X

    @property
    def Y(self):
        return self._Y

    @property
    def Z(self):
        return self._Z
