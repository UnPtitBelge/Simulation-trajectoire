from math import pi, sqrt

import numpy as np


def deformation(r, R: float, T: float, F: float, center_radius: float) -> np.ndarray:
    """Compute deformation for a NumPy array of radii, clamped at the sphere's bottom."""
    # Clamp near r=0 to avoid log singularity / contact region
    # r_use = np.maximum(r, center_radius)

    # Vectorized computation of deformation
    z = -F / (2.0 * pi * T) * np.log(R / r)

    # Calculate the Z value at r = center_radius (bottom of the sphere)
    z_sphere_bottom = -F / (2.0 * pi * T) * np.log(R / center_radius)

    # Clamp the deformation so it never goes below the sphere's bottom
    z = np.maximum(z, z_sphere_bottom)

    return z


def gradient_xy(x: float, y: float, R: float, T: float, F: float, center_radius: float):
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


def disk_xy(
    cx: float, cy: float, radius: float, n: int = 60
) -> tuple[np.ndarray, np.ndarray]:
    """
    Get the (x, y) coordinates of points forming a circle (disk) centered at (cx, cy) with the given radius.
    """
    ang = np.linspace(0, 2 * np.pi, n, endpoint=True)
    x = cx + radius * np.cos(ang)
    y = cy + radius * np.sin(ang)
    # Append the first point to the end to close the loop
    x = np.append(x, x[0])
    y = np.append(y, y[0])
    return x, y
