"""
plot_3d.model

Shared analytical deformation model for the axisymmetric membrane surface.

This module centralizes the surface height function z(r) and a helper to compute
the projected gradient components (dz/dx, dz/dy) using only scalar parameters,
so that rendering and simulation can use the same model without depending on
any geometry classes.

Model:
    z(r) = -F / (2π T) * ln(R / r_clamped)
where:
    - F: central sphere weight (N), related to its mass m via F = m * g
    - T: membrane tension (N/m or arbitrary units)
    - R: membrane radius (m)
    - r_clamped = max(r, center_radius) prevents the log singularity at r -> 0
    - center_radius: central sphere radius (m)

Projected gradient:
    For (x, y) with r = sqrt(x^2 + y^2),
        coeff = F / (2π T)
        dz/dx = coeff * (x / r^2)
        dz/dy = coeff * (y / r^2)
    with dz/dx = dz/dy = 0 when r is sufficiently small (to avoid division by zero).

All functions return plain Python types (floats, tuples) to remain compatible
with Dash/Plotly and internal computation routines.
"""

from __future__ import annotations

from math import log, pi, sqrt
from typing import Tuple


def deformation(r: float, R: float, T: float, F: float, center_radius: float) -> float:
    """
    Return axisymmetric surface height z(r) for the membrane model.

    Args:
        r: Radial position from the center (m).
        R: Membrane radius (m).
        T: Membrane tension.
        F: Central sphere weight (N).
        center_radius: Central sphere radius (m), used to clamp r at contact.

    Returns:
        z(r) as a float (arbitrary units consistent with inputs).
    """
    r_use = max(float(r), float(center_radius))
    return -float(F) / (2.0 * pi * float(T)) * log(float(R) / r_use)


def gradient_xy(
    x: float, y: float, R: float, T: float, F: float, center_radius: float
) -> Tuple[float, float, float]:
    """
    Compute z and its projected gradient components (dz/dx, dz/dy) at (x, y).

    Args:
        x, y: Cartesian coordinates (m).
        R: Membrane radius (m).
        T: Membrane tension.
        F: Central sphere weight (N).
        center_radius: Central sphere radius (m).

    Returns:
        (z, dz_dx, dz_dy) where:
            - z is the surface height at r = sqrt(x^2 + y^2)
            - dz_dx, dz_dy are projected gradient components for use in dynamics

    Notes:
        The gradient direction follows the negative radial slope:
            dz/dx = -coeff * (x / r), dz/dy = -coeff * (y / r)
        with coeff = F / (2π T) and dz/dx = dz/dy = 0 when r is very small.
    """
    r = sqrt(float(x) * float(x) + float(y) * float(y))
    z = deformation(r, R=R, T=T, F=F, center_radius=center_radius)

    if r > 1e-12:
        coeff = float(F) / (2.0 * pi * float(T))
        dz_dx = coeff * (float(x) / (r * r))
        dz_dy = coeff * (float(y) / (r * r))
    else:
        dz_dx = 0.0
        dz_dy = 0.0

    return z, dz_dx, dz_dy
