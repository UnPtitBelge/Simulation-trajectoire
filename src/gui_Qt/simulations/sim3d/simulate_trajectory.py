from math import hypot
from typing import List

from utils.math_helpers import gradient_xy
from utils.params import PlotParams, Simulation3dParams


def simulate_trajectory(
    sim_params: Simulation3dParams = Simulation3dParams(),
    plot_params: PlotParams = PlotParams(),
):
    """Simulate a point moving on a deformable surface."""
    g = sim_params.g
    dt = sim_params.time_step
    steps = sim_params.num_steps
    friction_coef = sim_params.friction_coef

    R = plot_params.surface_radius
    T = plot_params.surface_tension
    F = plot_params.center_weight
    center_radius = plot_params.center_radius

    m = F / g if g != 0.0 else 1.0
    friction_over_m = friction_coef / m  # precompute constant

    # Initial position
    x = float(sim_params.x0)
    y = float(sim_params.y0)
    r0 = hypot(x, y)
    if r0 >= R:
        if r0 > 1e-12:
            scale = (R - 1e-6) / r0
            x *= scale
            y *= scale
        else:
            x, y = R - 1e-6, 0.0

    vx = float(sim_params.vx0)
    vy = float(sim_params.vy0)

    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []

    steps_run = 0
    z = 0.0

    while True:
        z, dz_dx, dz_dy = gradient_xy(x, y, R=R, T=T, F=F, center_radius=center_radius)

        ax = -g * dz_dx - friction_over_m * vx
        ay = -g * dz_dy - friction_over_m * vy

        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        # Recompute z at the NEW position so the stored z matches (x, y)
        z, _, _ = gradient_xy(x, y, R=R, T=T, F=F, center_radius=center_radius)

        xs.append(x)
        ys.append(y)
        zs.append(float(z))

        steps_run += 1
        r = hypot(x, y)
        if r >= R or r <= center_radius or steps_run >= steps:
            break

    return {
        "xs": xs,
        "ys": ys,
        "zs": zs,
        "steps_run": steps_run,
        "final_state": {"x": x, "y": y, "vx": vx, "vy": vy, "z": float(z)},
    }
