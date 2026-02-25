import numpy as np
from utils.params import Simulation2dParams


def simulate_trajectory(sim_params: Simulation2dParams):
    """Run the physics simulation to generate the trajectory."""
    mu = sim_params.G * sim_params.M
    dt = sim_params.dt

    # Initial conditions
    r = np.array([sim_params.r0, 0.0], dtype=float)

    # Initial velocity with angle
    theta = np.deg2rad(sim_params.theta_deg)
    v = np.array(
        [sim_params.v0 * np.cos(theta), sim_params.v0 * np.sin(theta)],
        dtype=float,
    )

    def accel(r_vec: np.ndarray, v_vec: np.ndarray) -> np.ndarray:
        r_norm = np.linalg.norm(r_vec)
        r_norm = max(float(r_norm), 1e-12)
        r_hat = r_vec / r_norm
        a_mag = mu / (r_norm**2)  # Gravitationnal acceleration
        a_grav = -a_mag * r_hat
        a_drag = -sim_params.gamma * v_vec
        return a_grav + a_drag

    # Velocity-Verlet integration
    a = accel(r, v)
    trajectory_xs = []
    trajectory_ys = []
    frame_count = 0

    while True:
        trajectory_xs.append(float(r[0]))
        trajectory_ys.append(float(r[1]))
        frame_count += 1

        if np.linalg.norm(r) <= (sim_params.center_radius + sim_params.particle_radius):
            break

        r_next = r + v * dt + 0.5 * a * dt**2
        v_half = v + 0.5 * a * dt
        a_next = accel(r_next, v_half)
        v_next = v_half + 0.5 * a_next * dt

        r, v, a = r_next, v_next, a_next

    return {
        "xs": trajectory_xs,
        "ys": trajectory_ys,
        "n_frames": frame_count,
    }
