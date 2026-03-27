"""Simulation physique de la membrane — intégrateur semi-implicite Euler.

Surface : z(r) = k · ln(r/R),  k = F/(2πT)
La surface est concave (bord le plus haut, centre le plus bas).
Bille glissante (pas de roulement).
Coordonnées polaires : état = (r, θ, vr, vθ) où vθ = r * dθ/dt.

Équations du mouvement (Newton en coordonnées polaires, bille glissante) :
  dvr/dt = +vθ²/r  -  g·(k/r)/√(1+(k/r)²)  -  μ·g/√(1+(k/r)²)·vr/|v|
  dvθ/dt = -vr·vθ/r  -  μ·g/√(1+(k/r)²)·vθ/|v|
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
    ball_radius: float = 0.01,
    ball_mass: float = 0.005,
    center_mass: float = 1.0,
    center_radius: float = 0.05,
) -> np.ndarray:
    """Retourne array (n_steps, 4) : colonnes = r, θ, vr, vθ.

    Bille glissante — la masse se simplifie, les accélérations sont :
    1. Centrifuge         : +vθ²/r
    2. Gravité radiale    : -g·(k/r)/√(1+(k/r)²)       (vers le centre)
    3. Frottement Coulomb : -μ·g/√(1+(k/r)²)·v/|v|     (normal variable avec r)
    4. Coriolis (net)     : -vr·vθ/r                    (en dvθ/dt)

    r_min doit être ≥ center_radius pour éviter la collision avec la bille centrale.
    """
    traj = np.empty((n_steps, 4))
    r, theta, vr, vtheta = r0, theta0, vr0, vtheta0
    r_min = max(r_min, center_radius)

    for i in range(n_steps):
        traj[i] = (r, theta, vr, vtheta)

        current_r   = max(r, r_min)
        local_slope = k / current_r
        inv_norm    = 1.0 / np.sqrt(1.0 + local_slope ** 2)  # cos(β) = 1/√(1+(k/r)²)

        # Gravité radiale : -g·sin(β) = -g·(k/r)/√(1+(k/r)²)
        a_gravity = -g * local_slope * inv_norm

        # Frottement de Coulomb : μ·N/m = μ·g·cos(β) = μ·g/√(1+(k/r)²)
        g_friction = friction * g * inv_norm
        speed = np.sqrt(vr ** 2 + vtheta ** 2)

        if speed > 0:
            friction_r     = -g_friction * vr     / speed
            friction_theta = -g_friction * vtheta / speed
            ar = vtheta ** 2 / current_r + a_gravity + friction_r
            at = -vr * vtheta / current_r + friction_theta
        elif abs(a_gravity) > g_friction:
            # Frottement statique dépassé : la bille glisse (gravité > friction max)
            ar = a_gravity + g_friction   # friction s'oppose au mouvement inward
            at = 0.0
        else:
            # Frottement statique tient : tan(β) ≤ μ, la bille reste immobile
            ar = at = 0.0

        vr     += dt * ar
        vtheta += dt * at

        # Snap-to-zero : si la vitesse est inférieure à ce que le frottement
        # peut produire en un pas ET que le frottement statique tient, bloquer.
        if np.sqrt(vr ** 2 + vtheta ** 2) < g_friction * dt and abs(a_gravity) <= g_friction:
            vr = vtheta = 0.0

        r     += dt * vr
        theta += dt * vtheta / current_r

        if r >= R:
            return traj[:i + 1]
        elif r < r_min:
            r = r_min
            vr = max(vr, 0.0)

        speed_after = np.sqrt(vr ** 2 + vtheta ** 2)
        if speed_after == 0.0 or (speed_after < g_friction * dt and (abs(a_gravity) <= g_friction or r <= r_min)):
            return traj[:i + 1]

    return traj
