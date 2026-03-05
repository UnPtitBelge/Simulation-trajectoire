from math import log, pi, sqrt

import numpy as np


def deformation(
    r: np.ndarray, R: float, T: float, F: float, center_radius: float
) -> np.ndarray:
    """Vectorised deformation — used for surface mesh generation (NumPy arrays)."""
    z = -F / (2.0 * pi * T) * np.log(R / r)
    z_sphere_bottom = -F / (2.0 * pi * T) * log(R / center_radius)  # scalar, no alloc
    return np.maximum(z, z_sphere_bottom)


def _deformation_scalar(
    r: float, R: float, T: float, F: float, center_radius: float
) -> float:
    """Scalar version of deformation — no NumPy overhead, used inside the 3D loop."""
    coeff = -F / (2.0 * pi * T)
    z = coeff * log(R / r)
    z_bottom = coeff * log(R / center_radius)
    return z if z > z_bottom else z_bottom


def gradient_xy(x: float, y: float, R: float, T: float, F: float, center_radius: float):
    """Return (z, dz/dx, dz/dy) at scalar (x, y). Uses pure-math, no NumPy."""
    r = sqrt(x * x + y * y)  # no cast needed — already floats from the 3D loop
    z = _deformation_scalar(r, R=R, T=T, F=F, center_radius=center_radius)

    if r > 1e-12:
        coeff = F / (2.0 * pi * T)
        dz_dx = coeff * (x / (r * r))
        dz_dy = coeff * (y / (r * r))
    else:
        dz_dx = dz_dy = 0.0

    return z, dz_dx, dz_dy


def disk_xy(
    cx: float, cy: float, radius: float, n: int = 60
) -> tuple[np.ndarray, np.ndarray]:
    """(x, y) coordinates of a closed circle centred at (cx, cy)."""
    ang = np.linspace(0, 2 * np.pi, n, endpoint=True)
    x = cx + radius * np.cos(ang)
    y = cy + radius * np.sin(ang)
    x = np.append(x, x[0])
    y = np.append(y, y[0])
    return x, y
