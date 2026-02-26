import numpy as np
from config import surface_depth, surface_sigma


class SurfaceField:
    """
    Generic surface deformation field used to curve a 2D plane around a central mass.

    This class models a simple radial height function:
        h(x, y) = -D * exp(-(x^2 + y^2) / (2 * S^2))

    Where:
        - D (depth) controls how deep the surface curves.
        - S (sigma) controls the spread (width) of the deformation.

    Parameters:
        k_depth (float): Scale factor applied to the central mass to compute depth.
        k_sigma (float): Scale factor applied to the central radius to compute sigma.
        central_mass (float): Mass of the central body.
        central_radius (float): Radius of the central body.
        friction (float): Linear friction/damping coefficient used by the motion model.

    Notes:
        - The static height function `h(x, y)` uses global constants `surface_depth` and
          `surface_sigma` for compatibility with legacy code expecting module-level values.
        - Instance properties expose the configured depth/sigma/friction for consumers that
          rely on object state rather than global constants.
    """

    def __init__(
        self,
        k_depth: float,
        k_sigma: float,
        central_mass: float,
        central_radius: float,
        friction: float,
    ):
        self._depth = float(k_depth) * float(central_mass)
        self._sigma = float(k_sigma) * float(central_radius)
        self._friction = float(friction)

    @staticmethod
    def h(x, y):
        """
        Compute the surface height at (x, y). Accepts scalars or numpy arrays.
        """
        x_arr = np.asarray(x)
        y_arr = np.asarray(y)
        r2 = x_arr**2 + y_arr**2
        return -surface_depth * np.exp(-r2 / (2.0 * surface_sigma**2))

    @property
    def depth(self) -> float:
        return self._depth

    @property
    def sigma(self) -> float:
        return self._sigma

    @property
    def friction(self) -> float:
        return self._friction
