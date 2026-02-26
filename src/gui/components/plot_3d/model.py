from __future__ import annotations

from math import log, pi, sqrt
from typing import Tuple


def deformation(r: float, R: float, T: float, F: float, center_radius: float) -> float:
    # Clamp near r=0 to avoid the log singularity / contact region.
    r_use = max(float(r), float(center_radius))
    return -float(F) / (2.0 * pi * float(T)) * log(float(R) / r_use)


def gradient_xy(
    x: float, y: float, R: float, T: float, F: float, center_radius: float
) -> Tuple[float, float, float]:
    r = sqrt(float(x) * float(x) + float(y) * float(y))
    z = deformation(r, R=R, T=T, F=F, center_radius=center_radius)

    # Avoid division by zero in x/r^2, y/r^2 near the center.
    if r > 1e-12:
        coeff = float(F) / (2.0 * pi * float(T))
        dz_dx = coeff * (float(x) / (r * r))
        dz_dy = coeff * (float(y) / (r * r))
    else:
        dz_dx = 0.0
        dz_dy = 0.0

    return z, dz_dx, dz_dy
