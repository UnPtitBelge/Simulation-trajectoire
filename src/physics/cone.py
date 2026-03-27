"""Simulation physique du cône — intégrateur semi-implicite Euler.

Surface : z(r) = slope * (r - R_centre),  slope = depth / R
Bille glissante (pas de roulement).
Coordonnées polaires : état = (r, θ, vr, vθ) où vθ = r * dθ/dt.

Équations du mouvement (Newton en coordonnées polaires, bille glissante) :
  dvr/dt = +vθ²/r  -  g·sin(α)  -  μ·g·cos(α)·vr/|v|
  dvθ/dt = -vr·vθ/r  -  μ·g·cos(α)·vθ/|v|
"""

import numpy as np


def compute_cone(
    r0: float,
    theta0: float,
    vr0: float,
    vtheta0: float,
    R: float,
    depth: float,
    friction: float,
    g: float,
    dt: float,
    n_steps: int,
    ball_radius: float = 0.01,
    ball_mass: float = 0.005,
    center_mass: float = 1.0,
    center_radius: float = 0.05,
) -> np.ndarray:
    """Retourne array (n_steps, 4) : colonnes = r, θ, vr, vθ.

    Bille glissante — la masse se simplifie, les accélérations sont :
    1. Centrifuge         : +vθ²/r
    2. Gravité radiale    : -g·sin(α)           (constant sur le cône)
    3. Frottement Coulomb : -μ·g·cos(α)·v/|v|  (opposé à la vitesse totale)
    4. Coriolis (net)     : -vr·vθ/r            (en dvθ/dt)
    """
    slope = depth / R
    slope_angle = np.arctan(slope)
    g_radial  = -g * np.sin(slope_angle)   # gravité le long du cône (constante)
    g_friction = friction * g * np.cos(slope_angle)  # amplitude frottement Coulomb

    r_min = center_radius

    traj = np.empty((n_steps, 4))
    r, theta, vr, vtheta = r0, theta0, vr0, vtheta0

    for i in range(n_steps):
        traj[i] = (r, theta, vr, vtheta)

        current_r = max(r, r_min)
        speed = np.sqrt(vr ** 2 + vtheta ** 2)

        if speed > 0:
            friction_r     = -g_friction * vr     / speed
            friction_theta = -g_friction * vtheta / speed
            ar = vtheta ** 2 / current_r + g_radial + friction_r
            at = -vr * vtheta / current_r + friction_theta
        elif abs(g_radial) > g_friction:
            # Frottement statique dépassé : la bille glisse (gravité > friction max)
            ar = g_radial + g_friction   # friction s'oppose au mouvement inward
            at = 0.0
        else:
            # Frottement statique tient : la bille reste immobile
            ar = at = 0.0

        vr     += dt * ar
        vtheta += dt * at

        # Snap-to-zero : si la vitesse est inférieure à ce que le frottement
        # peut produire en un pas ET que le frottement statique tient, bloquer.
        if np.sqrt(vr ** 2 + vtheta ** 2) < g_friction * dt and abs(g_radial) <= g_friction:
            vr = vtheta = 0.0

        r     += dt * vr
        theta += dt * vtheta / current_r

        if r >= R:
            return traj[:i + 1]
        elif r < r_min:
            r = r_min
            vr = max(vr, 0.0)

        speed_after = np.sqrt(vr ** 2 + vtheta ** 2)
        if speed_after == 0.0 or (speed_after < g_friction * dt and (abs(g_radial) <= g_friction or r <= r_min)):
            return traj[:i + 1]

    return traj
