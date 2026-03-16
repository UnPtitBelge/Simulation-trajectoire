from math import atan, cos, hypot, sin, sqrt

from utils.math_helpers import _deformation_scalar
from utils.params import Simulation3dParams


def simulate_trajectory(
    sim_params: Simulation3dParams | None = None,
) -> dict:
    """Integrate the 3-D conical surface trajectory and return all frame positions.

    Because the cone has a constant radial slope (``cone_slope = dz/dr``),
    all surface-dependent quantities are constant and pre-computed once
    before the integration loop.

    Surface geometry
    ----------------
        α = arctan(cone_slope)              — cone half-angle

    Forces (projected onto the surface plane)
    -----------------------------------------
    1. Gravity tangential component (constant everywhere on the cone):

           a_grav = g · sin(α)

       Cartesian projection (radially inward):

           a_x = -a_grav · (x / r)
           a_y = -a_grav · (y / r)

    2. Coulomb (dry) friction — opposes the velocity direction:

           N     = m · g · cos(α)           — normal force
           F_f   = -μ_c · N · v̂            — friction force
           a_f   = -(μ_c · g · cos(α)) · v̂ — friction acceleration

       where v̂ = (vx, vy) / ‖v‖ is the unit velocity vector.
       The friction magnitude is constant (independent of speed) and
       drops to zero only when the particle is at rest (‖v‖ = 0).

    Uses semi-implicit (symplectic) Euler integration.  Returns a dict with keys
    ``"xs"``, ``"ys"``, ``"zs"`` — lists of per-frame particle positions.
    """

    if sim_params is None:
        sim_params = Simulation3dParams()

    g = sim_params.g
    dt = sim_params.time_step
    steps = sim_params.num_steps
    friction_coef = sim_params.friction_coef
    # particle_mass is read explicitly so it appears in the UI controls and
    # remains available for future forces independent of mass (wind, magnetic…).
    # In the current model it cancels out — see the derivation comment below.
    particle_mass: float = sim_params.particle_mass
    assert particle_mass > 0, f"particle_mass must be positive, got {particle_mass}"

    R = sim_params.surface_radius
    cone_slope = sim_params.cone_slope
    center_radius = sim_params.center_radius
    particle_radius = sim_params.particle_radius

    # ------------------------------------------------------------------
    # Pre-compute all constant surface quantities.
    #
    #   α = arctan(cone_slope)              — cone half-angle
    #
    # Full Newton second law (F = m·a) for each force:
    #
    #   1. Gravity tangential component:
    #        F_grav = m · g · sin(α)
    #        a_grav = F_grav / m = g · sin(α)           ← m cancels
    #
    #   2. Coulomb kinetic friction  (normal force N = m · g · cos(α)):
    #        F_fric = μ_c · N = μ_c · m · g · cos(α)
    #        a_fric = F_fric / m = μ_c · g · cos(α)     ← m cancels
    #
    # In the current model (gravity + Coulomb only), particle_mass
    # cancels in both accelerations — the trajectory is mass-independent,
    # exactly as in free fall (Galileo's equivalence principle).
    #
    # particle_mass is still read from sim_params and kept in scope so
    # that any future force independent of mass (e.g. wind, magnetic
    # field) can be added here as  a_extra = F_extra / particle_mass
    # without restructuring the model.
    # ------------------------------------------------------------------
    alpha = atan(cone_slope)
    a_grav = g * sin(alpha)  # = (m·g·sin α) / m
    a_fric = friction_coef * g * cos(alpha)  # = (μ_c·m·g·cos α) / m

    # ------------------------------------------------------------------
    # Z-centre of the central sphere mesh (matches Plot3d._draw_center_sphere).
    # The mesh is placed with z_offset = z(center_radius) + center_radius,
    # so the equator of the sphere sits at the surface level at r = center_radius
    # (centre = surface + radius → equator is flush with the surface).
    # ------------------------------------------------------------------
    _z_center_sphere = (
        _deformation_scalar(
            center_radius, R=R, cone_slope=cone_slope, center_radius=center_radius
        )
        + center_radius  # centre = surface + rayon → équateur au niveau de la surface
    )

    # Sum of radii — stop when the 3-D distance between sphere centres
    # equals this value.
    _contact_dist = center_radius + particle_radius

    # ------------------------------------------------------------------
    # Initial conditions — clamp inside the rim if necessary.
    # ------------------------------------------------------------------
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

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    vxs: list[float] = []
    vys: list[float] = []

    steps_run = 0

    # ------------------------------------------------------------------
    # Integration loop (semi-implicit (symplectic) Euler).
    #
    # Equations of motion projected on the surface plane:
    #
    #   a_x = -a_grav · (x/r)  -  a_fric · (vx / ‖v‖)
    #   a_y = -a_grav · (y/r)  -  a_fric · (vy / ‖v‖)
    #
    # where:
    #   -a_grav · (x/r)       gravity pull, constant magnitude, radially inward
    #   -a_fric · v̂           Coulomb friction, constant magnitude, opposing v⃗
    # ------------------------------------------------------------------
    while True:
        r = hypot(x, y)

        # -- Radial unit vector (gravity direction) ----------------------
        if r > 1e-12:
            ux = x / r
            uy = y / r
        else:
            ux = uy = 0.0

        # -- Velocity unit vector (friction direction) -------------------
        v = hypot(vx, vy)
        if v > 1e-12:
            wx = vx / v
            wy = vy / v
        else:
            wx = wy = 0.0

        ax = -a_grav * ux - a_fric * wx
        ay = -a_grav * uy - a_fric * wy

        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        # Re-project particle onto the cone surface at the new (x, y).
        r = hypot(x, y)
        z = _deformation_scalar(
            r, R=R, cone_slope=cone_slope, center_radius=center_radius
        )

        xs.append(x)
        ys.append(y)
        zs.append(float(z))
        vxs.append(vx)
        vys.append(vy)

        steps_run += 1

        # ---- Stopping conditions ----------------------------------------

        if r >= R:
            break

        # 3-D distance between particle centre and central-sphere centre.
        # Particle centre is at (x, y, z + particle_radius) on the surface.
        # Central sphere centre is at (0, 0, _z_center_sphere).
        dz_to_center = (z + particle_radius) - _z_center_sphere
        dist3d = sqrt(r * r + dz_to_center * dz_to_center)
        if dist3d <= _contact_dist:
            break

        if steps_run >= steps:
            break

    return {"xs": xs, "ys": ys, "zs": zs, "vxs": vxs, "vys": vys}
