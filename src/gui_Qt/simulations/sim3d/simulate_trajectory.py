from math import hypot, log, pi, sqrt
from typing import List

from utils.math_helpers import _deformation_scalar, gradient_xy
from utils.params import Simulation3dParams


def simulate_trajectory(
    sim_params: Simulation3dParams | None = None,
) -> dict:
    """Integrate the 3-D surface trajectory and return all frame positions.

    Uses explicit Euler integration. Returns a dict with keys
    "xs", "ys", "zs" — lists of per-frame particle positions.
    """

    if sim_params is None:
        sim_params = Simulation3dParams()

    g = sim_params.g
    dt = sim_params.time_step
    steps = sim_params.num_steps
    friction_coef = sim_params.friction_coef

    R = sim_params.surface_radius
    T = sim_params.surface_tension
    # F is the weight of the central sphere: it depends on BOTH mass and gravity.
    # Using F = center_mass * g means doubling g or doubling center_mass both
    # deepen the surface by the same factor, which is physically correct.
    center_mass = sim_params.center_mass
    F = center_mass * g
    center_radius = sim_params.center_radius
    particle_radius = sim_params.particle_radius

    # Z-centre of the central sphere mesh (matches Plot3d._draw_center_sphere).
    # The mesh is placed with z_offset = deformation(center_radius) + center_radius/2,
    # so the equator of the sphere sits at the surface level at r = center_radius.
    _z_center_sphere = (
        _deformation_scalar(center_radius, R=R, T=T, F=F, center_radius=center_radius)
        + center_radius / 2.0
    )
    # Sum of radii — stop when 3-D distance between sphere centres equals this.
    _contact_dist = center_radius + particle_radius

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

        ax = -g * dz_dx - friction_coef * vx
        ay = -g * dz_dy - friction_coef * vy

        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        z, _, _ = gradient_xy(x, y, R=R, T=T, F=F, center_radius=center_radius)

        xs.append(x)
        ys.append(y)
        zs.append(float(z))

        steps_run += 1

        r = hypot(x, y)

        if r >= R:
            break

        # 3-D distance between particle centre and central-sphere centre.
        # Particle centre is at (x, y, z + particle_radius) on the surface.
        # Central sphere centre is at (0, 0, _z_center_sphere).
        dz = (z + particle_radius) - _z_center_sphere
        dist3d = sqrt(r * r + dz * dz)
        if dist3d <= _contact_dist:
            break

        if steps_run >= steps:
            break

    return {"xs": xs, "ys": ys, "zs": zs}
