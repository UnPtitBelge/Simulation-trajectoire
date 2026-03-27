"""Mouvement Circulaire Uniforme — solution analytique.

État retourné : (x, y) en coordonnées cartésiennes.
x(t) = r · cos(θ₀ + ω·t)
y(t) = r · sin(θ₀ + ω·t)
"""

import numpy as np


def compute_mcu(
    r: float,
    theta0: float,
    omega: float,
    n_steps: int,
    dt: float,
) -> np.ndarray:
    """Retourne array (n_steps, 2) : colonnes = x, y."""
    t = np.arange(n_steps) * dt
    angles = theta0 + omega * t
    traj = np.column_stack([r * np.cos(angles), r * np.sin(angles)])
    return traj
