"""Mathematical helpers for surface geometry.

Provides the deformation model of a conical surface and derived utilities
used by both the 3D surface renderer and the particle integrator.

Physical model
--------------
The surface is a **cone of constant slope**:

    z(r) = -cone_slope · (R - r)

where:
    - ``cone_slope = dz/dr``  [dimensionless] is the constant radial slope.
    - ``R``                   is the rim radius [m]   (z = 0 at r = R).
    - z is most negative at the centre (r = 0): z(0) = -cone_slope · R.

Because the slope is constant, the gravitational acceleration tangential
to the surface is also constant everywhere:

    a_grav = g · sin(α)    with  α = arctan(cone_slope)

Functions provided
------------------
- ``deformation``         — vectorised (NumPy arrays), used for mesh
                            generation where all grid points are
                            evaluated at once.
- ``_deformation_scalar`` — pure-Python scalar, used inside the ODE
                            integrator where calling NumPy per step
                            would dominate runtime.
- ``disk_xy``             — returns (x, y) coordinates of a closed
                            circle for 2D plot overlays.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Surface deformation
# ---------------------------------------------------------------------------


def deformation(
    r: np.ndarray,
    R: float,
    cone_slope: float,
    center_radius: float,
) -> np.ndarray:
    """Vectorised vertical deflection of the cone surface at radii ``r``.

    Computes z(r) = -cone_slope · (R - r) for every element of ``r``,
    then clamps the result so no point dips below the floor set by the
    central sphere contact radius.

    Args:
        r:             Radial distances from the centre [m]. Shape is arbitrary;
                       the output has the same shape.
        R:             Cone rim radius [m]. z = 0 at r = R.
        cone_slope:    Constant radial slope dz/dr [dimensionless].
        center_radius: Radius of the central sphere [m]. Sets the minimum
                       allowed z value: z_floor = z(center_radius).

    Returns:
        Vertical deflection array with the same shape as ``r`` [m].
        Values are ≤ 0 when ``cone_slope ≥ 0`` and ``r ≤ R``
        (the surface descends toward the centre).
    """
    z = -cone_slope * (R - r)

    # Hard floor at the central sphere contact circle.
    z_floor = -cone_slope * (R - center_radius)

    return np.maximum(z, z_floor)


def _deformation_scalar(
    r: float,
    R: float,
    cone_slope: float,
    center_radius: float,
) -> float:
    """Scalar vertical deflection of the cone — zero NumPy overhead.

    Identical physics to ``deformation`` but operates on a single
    ``float``. Called from the inner loop of the 3D ODE integrator
    (once per time step) where array allocation would be wasteful.

    Args:
        r:             Radial distance from the centre [m].
        R:             Cone rim radius [m].
        cone_slope:    Constant radial slope dz/dr [dimensionless].
        center_radius: Radius of the central sphere [m].

    Returns:
        Vertical deflection at radius ``r`` [m], clamped to the floor
        defined by the central sphere contact radius.
    """
    r = max(r, 1e-9)
    center_radius = max(center_radius, 1e-9)

    z = -cone_slope * (R - r)
    z_floor = -cone_slope * (R - center_radius)

    # The membrane cannot penetrate the central sphere.
    return z if z > z_floor else z_floor


# ---------------------------------------------------------------------------
# 2D geometry helper
# ---------------------------------------------------------------------------


def disk_xy(
    cx: float,
    cy: float,
    radius: float,
    n: int = 60,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (x, y) coordinates of a closed circle.

    Generates ``n`` evenly-spaced points around the circle using
    ``np.linspace(0, 2π, n, endpoint=True)``.  Because ``cos(2π) = cos(0)``
    and ``sin(2π) = sin(0)``, the last point coincides with the first,
    closing the loop visually without appending an extra duplicate.

    Args:
        cx:     x-coordinate of the circle's centre [plot units].
        cy:     y-coordinate of the circle's centre [plot units].
        radius: Circle radius [plot units].
        n:      Number of sample points (including the closing point at 2π).
                Defaults to 60.

    Returns:
        A ``(x, y)`` tuple of 1-D NumPy arrays each of length ``n``.
    """
    ang = np.linspace(0, 2 * np.pi, n, endpoint=True)
    x = cx + radius * np.cos(ang)
    y = cy + radius * np.sin(ang)
    return x, y
