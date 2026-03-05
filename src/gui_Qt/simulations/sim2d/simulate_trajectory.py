"""2-D orbital trajectory integrator.

Simulates a particle under the gravitational pull of a central body
plus optional linear (atmospheric) drag, using the velocity-Verlet
integration scheme.

Physics model
-------------
The gravitational acceleration at position **r** is:

    a_grav = -μ / |r|² · r̂,   μ = G · M

A linear drag term opposes the velocity:

    a_drag = -γ · v

The total acceleration is therefore:

    a = a_grav + a_drag

Velocity-Verlet scheme (symplectic, second-order)
-------------------------------------------------
    r_{n+1} = r_n + v_n · dt + ½ a_n · dt²
    v_{n+1} = v_n + ½ (a_n + a_{n+1}) · dt

This conserves energy better than explicit Euler for orbit problems,
keeping elliptical trajectories stable over many revolutions.

Stopping conditions
-------------------
The integration loop halts when **either**:

1. The particle reaches the surface of the central body:
       |r| ≤ center_radius + particle_radius
2. The step counter reaches ``max_steps`` (default ``MAX_STEPS = 4 000``).

The second condition guards against stable or weakly-decaying orbits
that never collide.  With the default ``dt = 0.02 s`` and
``MAX_STEPS = 4 000`` this caps simulated time at 80 s — long enough
to show several complete orbits while keeping the frame count in a
range that animates in a few seconds at ``frame_ms = 5``.

Without this guard the default parameters (near-circular orbit with a
very small drag coefficient) produced ≈ 19 000 frames and an animation
lasting over a minute.
"""

import logging
from math import hypot
from typing import List

import numpy as np
from utils.params import Simulation2dParams

log = logging.getLogger(__name__)

# Hard ceiling on integration steps.
# 4 000 steps × dt=0.02 s = 80 s of simulated time.
MAX_STEPS: int = 4_000


def _accel(
    r_vec: np.ndarray,
    v_vec: np.ndarray,
    mu: float,
    gamma: float,
) -> np.ndarray:
    """Compute the total acceleration at a given state (r, v).

    Combines gravitational and drag accelerations. Defined at module
    level (not as a closure) so it can be called without capturing any
    outer scope — this also makes it straightforward to unit-test
    independently.

    Args:
        r_vec: Position vector [x, y] in metres.
        v_vec: Velocity vector [vx, vy] in m/s.
        mu: Gravitational parameter G·M [m³/s²].
        gamma: Linear drag coefficient [s⁻¹]. Pass 0 for no drag.

    Returns:
        Acceleration vector [ax, ay] in m/s².
    """
    # ``hypot`` is faster than ``np.linalg.norm`` for exactly two components
    # because it avoids NumPy dispatch overhead.
    r_norm = hypot(float(r_vec[0]), float(r_vec[1]))

    # Clamp to avoid division by zero if the particle somehow reaches
    # the exact origin (should be caught by the stopping condition first).
    r_norm = max(r_norm, 1e-12)

    r_hat = r_vec / r_norm  # unit vector pointing away from centre
    a_grav = -(mu / (r_norm**2)) * r_hat  # inverse-square attraction
    a_drag = -gamma * v_vec  # linear drag opposing motion

    return a_grav + a_drag


def simulate_trajectory(
    sim_params: Simulation2dParams,
    max_steps: int = MAX_STEPS,
) -> dict:
    """Integrate the 2-D orbital trajectory and return all frame positions.

    Uses the velocity-Verlet method to advance the particle from its
    initial position until it collides with the central body **or**
    ``max_steps`` integration steps have been performed, whichever
    comes first.

    Args:
        sim_params: Dataclass holding all physical and numerical
            parameters for this simulation run. Key fields used:

            - ``G``, ``M``            — gravitational constant and
                                        central body mass (μ = G·M).
            - ``r0``                  — initial orbital radius [m].
            - ``v0``                  — initial speed [m/s].
            - ``theta_deg``           — launch angle relative to the
                                        positive x-axis [°].
            - ``gamma``               — linear drag coefficient [s⁻¹].
            - ``dt``                  — integration time step [s].
            - ``center_radius``       — radius of the central body [m].
            - ``particle_radius``     — radius of the particle [m].
        max_steps: Maximum number of integration steps before the loop
            is forced to stop. Defaults to ``MAX_STEPS`` (4 000).
            Pass a larger value when you deliberately want a longer
            simulation (e.g. to study slow orbital decay).

    Returns:
        A dict with the following keys:

        - ``"xs"``       : ``list[float]`` — x-coordinate at each frame [m].
        - ``"ys"``       : ``list[float]`` — y-coordinate at each frame [m].
        - ``"n_frames"`` : ``int``          — total number of frames
                           (equal to ``len(xs)``).
    """
    # Precompute the gravitational parameter to avoid repeating G*M each step.
    mu = sim_params.G * sim_params.M
    dt = sim_params.dt
    gamma = sim_params.gamma

    log.debug(
        "simulate_trajectory (2D) — μ=%.4g dt=%.4g γ=%.4g max_steps=%d",
        mu,
        dt,
        gamma,
        max_steps,
    )

    # -----------------------------------------------------------------------
    # Initial conditions
    # -----------------------------------------------------------------------

    # Particle starts on the positive x-axis at distance r0 from the origin.
    r = np.array([sim_params.r0, 0.0], dtype=float)

    # Launch angle relative to the positive x-axis.
    theta = np.deg2rad(sim_params.theta_deg)
    v = np.array(
        [sim_params.v0 * np.cos(theta), sim_params.v0 * np.sin(theta)],
        dtype=float,
    )

    # Collision occurs when the particle surface touches the central body.
    stop_radius = sim_params.center_radius + sim_params.particle_radius

    # -----------------------------------------------------------------------
    # Velocity-Verlet integration
    # -----------------------------------------------------------------------

    # Bootstrap: compute acceleration at the initial position before the loop
    # so the first half-step update is correct.
    a = _accel(r, v, mu, gamma)

    trajectory_xs: List[float] = []
    trajectory_ys: List[float] = []
    step = 0

    while step < max_steps:
        # Record the current position as one animation frame.
        trajectory_xs.append(float(r[0]))
        trajectory_ys.append(float(r[1]))

        # Check stopping condition *after* recording so the final position
        # (on or inside the central body) is included in the output.
        if hypot(float(r[0]), float(r[1])) <= stop_radius:
            log.debug(
                "simulate_trajectory (2D) — collision at step %d / %d",
                step,
                max_steps,
            )
            break

        # --- Velocity-Verlet step ---

        # 1. Advance position using current velocity and acceleration.
        r_next = r + v * dt + 0.5 * a * dt**2

        # 2. Compute a provisional "half-step" velocity for the force evaluation.
        v_half = v + 0.5 * a * dt

        # 3. Evaluate acceleration at the new position with the half-step velocity
        #    (drag term uses v_half; gravitational term depends only on r_next).
        a_next = _accel(r_next, v_half, mu, gamma)

        # 4. Complete the velocity update using the average of old and new accelerations.
        v_next = v_half + 0.5 * a_next * dt

        # Advance state for the next iteration.
        r, v, a = r_next, v_next, a_next
        step += 1

    else:
        # The while condition (step < max_steps) became False — the loop
        # exhausted its budget without a collision.  This is the normal
        # outcome for stable or slowly-decaying orbits.
        log.info(
            "simulate_trajectory (2D) — max_steps=%d reached without collision "
            "(stable orbit or slow decay); trajectory truncated at %d frames.",
            max_steps,
            len(trajectory_xs),
        )

    log.debug(
        "simulate_trajectory (2D) — finished: %d frames, last r=%.4g",
        len(trajectory_xs),
        hypot(float(r[0]), float(r[1])),
    )

    return {
        "xs": trajectory_xs,
        "ys": trajectory_ys,
        "n_frames": len(trajectory_xs),
    }
