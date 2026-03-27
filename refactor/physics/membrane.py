"""Simulation physique de la membrane — intégrateur semi-implicite Euler.

Surface : z(r) = k · ln(r/R),  k = F/(2πT)
La surface est concave (bord le plus haut, centre le plus bas).
Coordonnées polaires : état = (r, θ, vr, vθ) où vθ = r * dθ/dt.

Équations du mouvement (Lagrangien avec métrique variable) :
  ar   = [vθ²/r − g·k/r + 2·k²·vr²/r³] / (1+(k/r)²) − friction·vr
  v̇θ  = −(vr·vθ)/r − friction·vθ
  ṙ   = vr    (semi-implicite)
  θ̇   = vθ/r  (semi-implicite)
"""

import numpy as np


def compute_membrane(
    r0: float,
    theta0: float,
    vr0: float,
    vtheta0: float,
    R: float,
    k: float,
    r_min: float,
    friction: float,
    g: float,
    dt: float,
    n_steps: int,
) -> np.ndarray:
    """Retourne array (n_steps, 4) : colonnes = r, θ, vr, vθ."""
    traj = np.empty((n_steps, 4))
    r, theta, vr, vtheta = r0, theta0, vr0, vtheta0

    for i in range(n_steps):
        traj[i] = (r, theta, vr, vtheta)

        kr = k / max(r, r_min)
        metric = 1.0 + kr ** 2

        ar = (vtheta ** 2 / r - g * k / r + 2 * k ** 2 * vr ** 2 / r ** 3) / metric - friction * vr
        at = -(vr * vtheta) / r - friction * vtheta

        vr     += dt * ar
        vtheta += dt * at
        r      += dt * vr
        theta  += dt * vtheta / max(r, r_min)

        if r >= R:
            r = R
            vr = min(vr, 0.0)
        elif r < r_min:
            r = r_min
            vr = max(vr, 0.0)

    return traj
