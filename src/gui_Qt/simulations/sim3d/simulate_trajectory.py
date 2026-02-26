from math import sqrt
from typing import List, Tuple

from utils.math_helpers import gradient_xy
from utils.params import PlotParams, Simulation3dParams


def simulate_trajectory(
    sim_params: Simulation3dParams = Simulation3dParams(),
    plot_params: PlotParams = PlotParams(),
):
    """
    Simulates the trajectory of a point moving on a deformable surface.

    Args:
        sim_params: Simulation parameters (e.g., gravity, friction, initial conditions).
        plot_params: Plot parameters (e.g., surface radius, tension, center weight).

    Returns:
        A dictionary containing:
        - xs: List of x-coordinates of the trajectory.
        - ys: List of y-coordinates of the trajectory.
        - zs: List of z-coordinates of the trajectory.
        - steps_run: Number of simulation steps executed.
        - final_state: Final state of the point (x, y, vx, vy, z).
    """
    # Extract simulation parameters
    g = sim_params.g
    dt = sim_params.time_step
    steps = sim_params.num_steps
    friction_coef = sim_params.friction_coef

    # Extract plot parameters
    R = plot_params.surface_radius
    T = plot_params.surface_tension
    F = plot_params.center_weight
    center_radius = plot_params.center_radius

    # Calculate mass from weight: F = m * g
    m = F / g if g != 0.0 else 1.0

    # Initial position
    x = float(sim_params.x0)
    y = float(sim_params.y0)

    # If the initial position is outside the membrane, move it slightly inside
    r0 = sqrt(x**2 + y**2)
    if r0 >= R:
        if r0 > 1e-12:
            scale = (R - 1e-6) / r0
            x *= scale
            y *= scale
        else:
            x = min(R - 1e-6, R)
            y = 0.0

    # Initial velocity
    vx = float(sim_params.vx0)
    vy = float(sim_params.vy0)

    # Initialize trajectory lists
    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []

    def get_surface_height_and_gradient(
        xy: Tuple[float, float],
    ):
        """
        Computes the surface height (z) and its gradient (dz/dx, dz/dy) at a given (x, y).

        Args:
            xy: Tuple of (x, y) coordinates.

        Returns:
            Tuple of (z, dz/dx, dz/dy).
        """
        x_, y_ = xy
        return gradient_xy(x_, y_, R=R, T=T, F=F, center_radius=center_radius)

    steps_run = 0
    z = 0.0

    while True:
        # Compute surface height and gradient at current position
        z, dz_dx, dz_dy = get_surface_height_and_gradient((x, y))

        # Compute accelerations due to gravity and friction
        ax_g = -g * dz_dx
        ay_g = -g * dz_dy
        ax = ax_g - (friction_coef / m) * vx
        ay = ay_g - (friction_coef / m) * vy

        # Update velocity and position
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        # Record trajectory
        xs.append(x)
        ys.append(y)
        zs.append(float(z))

        steps_run += 1

        # Stopping conditions
        r = sqrt(x**2 + y**2)
        if r >= R:  # Point is outside the surface
            break
        if r <= center_radius:  # Point is inside the center region
            break
        if steps_run >= steps:  # Maximum steps reached
            break

    # Final state of the point
    final_state = {"x": x, "y": y, "vx": vx, "vy": vy, "z": float(z)}

    return {
        "xs": xs,
        "ys": ys,
        "zs": zs,
        "steps_run": steps_run,
        "final_state": final_state,
    }
