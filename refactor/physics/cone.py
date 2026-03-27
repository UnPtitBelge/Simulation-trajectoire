"""Simulation physique du cône — intégrateur semi-implicite Euler.

Surface : z(r) = -slope * (R - r),  slope = depth / R
Coordonnées polaires : état = (r, θ, vr, vθ) où vθ = r * dθ/dt.

Équations du mouvement (Lagrangien sur la surface conique) :
  v̇r  = [vθ²/r − g·s] / (1+s²) − friction·vr
  v̇θ  = −(vr·vθ)/r   − friction·vθ
  ṙ   = vr    (semi-implicite : r mis à jour après vr)
  θ̇   = vθ/r  (semi-implicite : θ mis à jour après vθ et r)
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
) -> np.ndarray:
    """Retourne array (n_steps, 4) : colonnes = r, θ, vr, vθ."""
    slope = depth / R
    s2 = 1.0 + slope ** 2
    r_min = 0.005  # évite division par zéro

    traj = np.empty((n_steps, 4))
    r, theta, vr, vtheta = r0, theta0, vr0, vtheta0

    for i in range(n_steps):
        traj[i] = (r, theta, vr, vtheta)

        ar = (vtheta ** 2 / r - g * slope) / s2 - friction * vr
        at = -(vr * vtheta) / r - friction * vtheta

        vr     += dt * ar
        vtheta += dt * at
        r      += dt * vr
        theta  += dt * vtheta / max(r, r_min)

        # Conditions limites : la bille reste sur le cône
        if r >= R:
            r = R
            vr = min(vr, 0.0)   # pas de sortie vers l'extérieur
        elif r < r_min:
            r = r_min
            vr = max(vr, 0.0)

    return traj
