"""Mathematical helpers for surface geometry.

Provides the deformation model of a circular rubber-sheet membrane
loaded by a central point force, and derived utilities used by both
the 3D surface renderer and the particle integrator.

Physical model
--------------
A circular membrane of radius ``R`` and tension ``T`` [N/m] is loaded
at its centre by a point force ``F`` [N] (the weight of the heavy
sphere). The vertical deflection at radius ``r`` from the centre is:

    z(r) = -F / (2 π T) · ln(R / r)

The surface is clamped at the rim (z = 0 at r = R) and is bounded
below by the sphere's surface at r = ``center_radius``.

Two implementations of the same formula are provided:

- ``deformation``        — vectorised (NumPy arrays), used for mesh
                           generation where all grid points are
                           evaluated at once.
- ``_deformation_scalar`` — pure-Python scalar, used inside the ODE
                           integrator where calling NumPy per step
                           would dominate runtime.
"""

from math import log, pi, sqrt

import numpy as np

# ---------------------------------------------------------------------------
# Surface deformation
# ---------------------------------------------------------------------------


def deformation(
    r: np.ndarray,
    R: float,
    T: float,
    F: float,
    center_radius: float,
) -> np.ndarray:
    """Vectorised vertical deflection of the membrane at radii ``r``.

    Computes z(r) = -F / (2 π T) · ln(R / r) for every element of
    ``r``, then clamps the result so no point dips below the bottom of
    the central sphere.

    Intended for NumPy array inputs (e.g. a 2-D grid of radii produced
    by ``np.meshgrid``). For a single scalar call ``_deformation_scalar``
    instead to avoid NumPy overhead.

    Args:
        r: Radial distances from the centre [m]. Must be > 0 and ≤ R.
            Shape is arbitrary; the output has the same shape.
        R: Membrane radius (clamping boundary) [m].
        T: Membrane tension [N/m].
        F: Central point force (weight of the sphere) [N].
        center_radius: Radius of the central sphere [m]. Defines the
            minimum z value: z_min = z(center_radius).

    Returns:
        Vertical deflection array with the same shape as ``r`` [m].
        Values are ≤ 0 (the membrane sags downward).
    """
    # Deflection at every grid point.
    z = -F / (2.0 * pi * T) * np.log(R / r)

    # The sphere's equator sets a hard floor — compute it once as a
    # scalar to avoid an extra array allocation.
    z_sphere_bottom = -F / (2.0 * pi * T) * log(R / center_radius)

    # Clamp: no part of the membrane can pass through the sphere.
    return np.maximum(z, z_sphere_bottom)


def _deformation_scalar(
    r: float,
    R: float,
    T: float,
    F: float,
    center_radius: float,
) -> float:
    """Scalar vertical deflection — zero NumPy overhead.

    Identical physics to ``deformation`` but operates on a single
    ``float``. Called from the inner loop of the 3D ODE integrator
    (once per time step) where array allocation would be wasteful.

    Args:
        r: Radial distance from the centre [m]. Must be > 0 and ≤ R.
        R: Membrane radius [m].
        T: Membrane tension [N/m].
        F: Central point force [N].
        center_radius: Radius of the central sphere [m].

    Returns:
        Vertical deflection at radius ``r`` [m], clamped to the bottom
        of the central sphere.
    """
    r = max(r, 1e-9)
    center_radius = max(center_radius, 1e-9)

    coeff = -F / (2.0 * pi * T)
    z = coeff * log(R / r)
    z_bottom = coeff * log(R / center_radius)

    # Return whichever is higher (less negative) — the membrane cannot
    # penetrate the central sphere.
    return z if z > z_bottom else z_bottom


# ---------------------------------------------------------------------------
# Gradient of the surface (used by the 3D integrator)
# ---------------------------------------------------------------------------


def gradient_xy(
    x: float,
    y: float,
    R: float,
    T: float,
    F: float,
    center_radius: float,
) -> tuple[float, float, float]:
    """Return the surface height and its gradient at Cartesian point (x, y).

    The gradient drives the gravitational acceleration of the particle:
        a_x = -g · ∂z/∂x,  a_y = -g · ∂z/∂y

    Analytically, for z(r) = -F/(2πT) · ln(R/r):
        ∂z/∂x = F/(2πT) · x/r²
        ∂z/∂y = F/(2πT) · y/r²

    Uses only ``math`` functions — no NumPy — so it is safe to call
    thousands of times per second from the integrator loop.

    Args:
        x: x-coordinate of the particle [m].
        y: y-coordinate of the particle [m].
        R: Membrane radius [m].
        T: Membrane tension [N/m].
        F: Central point force [N].
        center_radius: Radius of the central sphere [m].

    Returns:
        A ``(z, dz_dx, dz_dy)`` tuple where:
            - ``z``     is the surface height at (x, y) [m].
            - ``dz_dx`` is ∂z/∂x at (x, y) [dimensionless].
            - ``dz_dy`` is ∂z/∂y at (x, y) [dimensionless].
        Both gradient components are 0 at the origin (r ≤ 1e-12).
    """
    r = sqrt(x * x + y * y)

    # Height is computed by the scalar helper (handles the sphere floor).
    z = _deformation_scalar(r, R=R, T=T, F=F, center_radius=center_radius)

    if r > 1e-12:
        # Analytical partial derivatives of z(r) w.r.t. x and y.
        coeff = F / (2.0 * pi * T)
        dz_dx = coeff * (x / (r * r))
        dz_dy = coeff * (y / (r * r))
    else:
        # Surface is symmetric at the origin — gradient is undefined,
        # treat as zero to avoid division by zero.
        dz_dx = dz_dy = 0.0

    return z, dz_dx, dz_dy


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

    Generates ``n`` evenly-spaced points around the circle and
    appends the first point at the end so that a ``PlotCurveItem``
    draws a visually closed loop without a gap.

    Args:
        cx: x-coordinate of the circle's centre [plot units].
        cy: y-coordinate of the circle's centre [plot units].
        radius: Circle radius [plot units].
        n: Number of sample points around the circumference before
            the closing duplicate is appended. Defaults to 60.

    Returns:
        A ``(x, y)`` tuple of 1-D NumPy arrays each of length ``n + 1``.
    """
    ang = np.linspace(0, 2 * np.pi, n, endpoint=True)
    x = cx + radius * np.cos(ang)
    y = cy + radius * np.sin(ang)

    return x, y
