from math import hypot
from typing import List

import numpy as np
from utils.params import Simulation2dParams


def _accel(r_vec: np.ndarray, v_vec: np.ndarray, mu: float, gamma: float) -> np.ndarray:
    """Pure function — no closure, no capture, defined once at module level."""
    r_norm = hypot(float(r_vec[0]), float(r_vec[1]))  # hypot >> np.linalg.norm for 2D
    r_norm = max(r_norm, 1e-12)
    r_hat = r_vec / r_norm
    a_grav = -(mu / (r_norm**2)) * r_hat
    a_drag = -gamma * v_vec
    return a_grav + a_drag


def simulate_trajectory(sim_params: Simulation2dParams):
    """Run the physics simulation to generate the trajectory."""
    mu = sim_params.G * sim_params.M
    dt = sim_params.dt
    gamma = sim_params.gamma

    # Initial conditions
    r = np.array([sim_params.r0, 0.0], dtype=float)
    theta = np.deg2rad(sim_params.theta_deg)
    v = np.array(
        [sim_params.v0 * np.cos(theta), sim_params.v0 * np.sin(theta)],
        dtype=float,
    )

    stop_radius = sim_params.center_radius + sim_params.particle_radius

    # Velocity-Verlet integration
    a = _accel(r, v, mu, gamma)
    trajectory_xs: List[float] = []
    trajectory_ys: List[float] = []

    while True:
        trajectory_xs.append(float(r[0]))
        trajectory_ys.append(float(r[1]))

        # hypot instead of np.linalg.norm: no NumPy overhead for a 2-element check
        if hypot(float(r[0]), float(r[1])) <= stop_radius:
            break

        r_next = r + v * dt + 0.5 * a * dt**2
        v_half = v + 0.5 * a * dt
        a_next = _accel(r_next, v_half, mu, gamma)
        v_next = v_half + 0.5 * a_next * dt

        r, v, a = r_next, v_next, a_next

    return {
        "xs": trajectory_xs,
        "ys": trajectory_ys,
        "n_frames": len(trajectory_xs),
    }
