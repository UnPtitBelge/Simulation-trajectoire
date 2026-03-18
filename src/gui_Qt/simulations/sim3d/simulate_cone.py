"""3-D conical surface trajectory integrator (Newton model).

Models a particle sliding on a cone of constant slope under gravity and
Coulomb kinetic friction, using semi-implicit (symplectic) Euler integration.

Surface geometry
----------------
The cone has a constant radial slope ``cone_slope = dz/dr``::

    z(r) = -cone_slope · (R - r)

    α = arctan(cone_slope)   — cone half-angle

Forces projected onto the surface plane
----------------------------------------
1. Gravity (constant everywhere on the cone)::

       a_grav = g · sin(α)
       ax = -a_grav · x/r,   ay = -a_grav · y/r

2. Coulomb kinetic friction (opposing velocity)::

       a_fric = μ_c · g · cos(α)
       ax -= a_fric · vx/|v|,   ay -= a_fric · vy/|v|

Both accelerations are mass-independent (m cancels).

Integration
-----------
Semi-implicit (symplectic) Euler::

    v_{n+1} = v_n + a_n · dt
    x_{n+1} = x_n + v_{n+1} · dt     ← uses the *updated* velocity

Stopping conditions
-------------------
1. ``r ≥ R``                    particle exits through the rim
2. 3-D distance to central sphere ≤ contact distance
3. ``steps_run ≥ num_steps``    step budget exhausted
"""
from __future__ import annotations

from math import atan, cos, hypot, sin, sqrt

from utils.math_helpers import _cone_z_scalar
from utils.params import SimulationConeParams


def simulate_cone(sim_params: SimulationConeParams | None = None) -> dict:
    """Integrate the cone trajectory and return per-frame positions.

    Args:
        sim_params: Simulation parameters.  Uses defaults if ``None``.

    Returns:
        Dict with keys ``"xs"``, ``"ys"``, ``"zs"``, ``"vxs"``, ``"vys"``
        — lists of floats, one entry per recorded frame.
    """
    if sim_params is None:
        sim_params = SimulationConeParams()

    g             = sim_params.g
    dt            = sim_params.time_step
    steps         = sim_params.num_steps
    friction_coef = sim_params.friction_coef
    R             = sim_params.surface_radius
    cone_slope    = sim_params.cone_slope
    center_radius = sim_params.center_radius
    particle_radius = sim_params.particle_radius

    # Pre-compute constant surface quantities
    alpha  = atan(cone_slope)
    a_grav = g * sin(alpha)             # tangential gravity magnitude [m/s²]
    a_fric = friction_coef * g * cos(alpha)  # friction magnitude [m/s²]

    # Z-centre of the central sphere (equator flush with the cone surface)
    z_center = (
        _cone_z_scalar(center_radius, R=R, cone_slope=cone_slope,
                       center_radius=center_radius)
        + center_radius
    )
    contact_dist = center_radius + particle_radius

    # Initial conditions — clamp inside the rim
    x = float(sim_params.x0)
    y = float(sim_params.y0)
    r0 = hypot(x, y)
    if r0 >= R:
        scale = (R - 1e-6) / r0 if r0 > 1e-12 else 1.0
        x *= scale
        y *= scale

    vx = float(sim_params.vx0)
    vy = float(sim_params.vy0)

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    vxs: list[float] = []
    vys: list[float] = []

    steps_run = 0

    while True:
        r = hypot(x, y)

        # Radial unit vector (gravity direction, inward)
        if r > 1e-12:
            ux, uy = x / r, y / r
        else:
            ux = uy = 0.0

        # Velocity unit vector (friction direction)
        v = hypot(vx, vy)
        if v > 1e-12:
            wx, wy = vx / v, vy / v
        else:
            wx = wy = 0.0

        ax = -a_grav * ux - a_fric * wx
        ay = -a_grav * uy - a_fric * wy

        # Semi-implicit Euler: update velocity first, then position
        vx += ax * dt
        vy += ay * dt
        x  += vx * dt
        y  += vy * dt

        r = hypot(x, y)
        z = _cone_z_scalar(r, R=R, cone_slope=cone_slope,
                           center_radius=center_radius)

        xs.append(x)
        ys.append(y)
        zs.append(float(z))
        vxs.append(vx)
        vys.append(vy)

        steps_run += 1

        if r >= R:
            break

        dz = (z + particle_radius) - z_center
        if sqrt(r * r + dz * dz) <= contact_dist:
            break

        if steps_run >= steps:
            break

    return {"xs": xs, "ys": ys, "zs": zs, "vxs": vxs, "vys": vys}
