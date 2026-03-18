"""Mathematical helpers for surface geometry.

Provides deformation models for two 3-D surface types used by the
particle integrators and the OpenGL surface renderers.

Cone surface (Newton model)
---------------------------
Constant-slope cone::

    z(r) = -cone_slope · (R - r)

The gravitational acceleration tangential to the surface is constant::

    a_grav = g · sin(α),   α = arctan(cone_slope)

Laplace membrane (Laplace model)
---------------------------------
A circular elastic membrane under a central point load F [N] with
surface tension T [N/m], clamped at rim radius R::

    z(r) = -(F / 2πT) · ln(R / r)

Gravity must be projected onto the (curved) tangent plane; the normal
force is slope-corrected.

Naming convention
-----------------
Functions whose names begin with an underscore are scalar variants
intended for use inside tight ODE integrator loops.  The plain-name
variants are vectorised and operate on NumPy arrays.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Cone surface
# ---------------------------------------------------------------------------


def cone_z(
    r: np.ndarray,
    R: float,
    cone_slope: float,
    center_radius: float,
) -> np.ndarray:
    """Vectorised vertical deflection of the cone surface at radii *r*.

    Computes ``z(r) = -cone_slope · (R - r)`` and clamps the result so
    no point drops below the floor set by the central sphere contact.

    Args:
        r:             Radial distances [m].  Any shape; output matches.
        R:             Cone rim radius [m].  z = 0 at r = R.
        cone_slope:    Constant radial slope dz/dr [dimensionless].
        center_radius: Central sphere radius [m].  Sets the z floor.

    Returns:
        Vertical deflection array, same shape as *r* [m].
    """
    z = -cone_slope * (R - r)
    z_floor = -cone_slope * (R - center_radius)
    return np.maximum(z, z_floor)


def _cone_z_scalar(
    r: float,
    R: float,
    cone_slope: float,
    center_radius: float,
) -> float:
    """Scalar cone deflection — no NumPy overhead for integrator loops.

    Identical physics to :func:`cone_z` but operates on a single float.
    """
    r = max(r, 1e-9)
    z = -cone_slope * (R - r)
    z_floor = -cone_slope * (R - center_radius)
    return z if z > z_floor else z_floor


# ---------------------------------------------------------------------------
# Laplace membrane surface
# ---------------------------------------------------------------------------


def membrane_z(
    r: np.ndarray,
    R: float,
    T: float,
    F: float,
    center_radius: float,
) -> np.ndarray:
    """Vectorised vertical deflection of the Laplace membrane at radii *r*.

    The membrane is an elastic disk under a central point load *F* [N] with
    surface tension *T* [N/m], clamped to zero at rim radius *R*.

    Laplace equation solution (axisymmetric)::

        z(r) = -(F / 2πT) · ln(R / r)

    The radii are clamped to *center_radius* to avoid the log singularity
    near the central sphere.

    Args:
        r:             Radial distances [m].
        R:             Membrane rim radius [m].
        T:             Surface tension [N/m].
        F:             Central point load [N].
        center_radius: Central sphere radius [m].  Clamps r from below.

    Returns:
        Vertical deflection array, same shape as *r* [m].
    """
    r_safe = np.maximum(r, float(center_radius))
    coeff = F / (2.0 * np.pi * T)
    return -coeff * np.log(R / r_safe)


def _membrane_z_scalar(
    r: float,
    R: float,
    T: float,
    F: float,
    center_radius: float,
) -> float:
    """Scalar membrane deflection — no NumPy overhead for integrator loops."""
    import math
    r_use = max(float(r), float(center_radius))
    coeff = F / (2.0 * math.pi * T)
    return -coeff * math.log(R / r_use)


def _membrane_gradient(
    x: float,
    y: float,
    R: float,
    T: float,
    F: float,
    center_radius: float,
) -> tuple[float, float, float]:
    """Return ``(z, dz_dx, dz_dy)`` for the membrane surface at point (x, y).

    Used inside the Laplace integrator to compute gravity projections and
    friction forces from the surface gradient.

    Args:
        x, y:          Position [m].
        R, T, F:       Membrane rim radius, tension, central load.
        center_radius: Central sphere radius [m].

    Returns:
        Tuple ``(z, dz_dx, dz_dy)`` — height and partial derivatives.
    """
    import math

    r = math.sqrt(x * x + y * y)
    r_use = r if r > center_radius else center_radius

    coeff = F / (2.0 * math.pi * T)
    z = -coeff * math.log(R / r_use)

    if r > 1e-12:
        inv_r2 = 1.0 / (r * r)
        dz_dx = coeff * x * inv_r2
        dz_dy = coeff * y * inv_r2
    else:
        dz_dx = dz_dy = 0.0

    return z, dz_dx, dz_dy


# ---------------------------------------------------------------------------
# 2-D geometry helper
# ---------------------------------------------------------------------------


def disk_xy(
    cx: float,
    cy: float,
    radius: float,
    n: int = 60,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (x, y) coordinates of a closed circle.

    Generates *n* evenly-spaced points using ``linspace(0, 2π, n,
    endpoint=True)``.  Because cos(2π) = cos(0), the last point
    coincides with the first, closing the loop visually.

    Args:
        cx, cy: Centre of the circle [plot units].
        radius: Circle radius [plot units].
        n:      Number of sample points.

    Returns:
        ``(x, y)`` tuple of 1-D NumPy arrays of length *n*.
    """
    ang = np.linspace(0, 2 * np.pi, n, endpoint=True)
    return cx + radius * np.cos(ang), cy + radius * np.sin(ang)


# ---------------------------------------------------------------------------
# Backward-compatible aliases  (old name → new name)
# ---------------------------------------------------------------------------

# The old names were used by existing code; keep aliases so nothing breaks
# during the refactor before old files are deleted.
deformation = cone_z
_deformation_scalar = _cone_z_scalar
