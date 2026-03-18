"""3-D Laplace membrane trajectory integrator.

Models a particle sliding on an elastic membrane deformed by a central
point load, using velocity-Verlet (predictor-corrector) integration.

Surface geometry (Laplace equation solution)
--------------------------------------------
A circular elastic membrane under a central point load F [N] with
surface tension T [N/m], clamped at rim radius R::

    z(r)  = -(F / 2πT) · ln(R / r)
    ∂z/∂x =  (F / 2πT) · x / r²
    ∂z/∂y =  (F / 2πT) · y / r²

Forces
------
Gravity projected onto the exact tangent plane::

    ‖∇z‖² = (∂z/∂x)² + (∂z/∂y)²
    norm_sq = 1 + ‖∇z‖²

    ax = -g · (∂z/∂x) / norm_sq
    ay = -g · (∂z/∂y) / norm_sq

Coulomb kinetic friction with slope-corrected normal force::

    N/m     = g / √norm_sq
    vz      = (∂z/∂x)·vx + (∂z/∂y)·vy   (surface-constraint velocity)
    |v₃D|   = √(vx² + vy² + vz²)
    ax     -= μ · (g/√norm_sq) · vx / |v₃D|
    ay     -= μ · (g/√norm_sq) · vy / |v₃D|

Integration
-----------
Velocity-Verlet (predictor-corrector, second-order symplectic)::

    x_{n+1}  = x_n + vx_n·dt + ½·ax_n·dt²
    vx_pred  = vx_n + ax_n·dt
    ax_{n+1} = accel(x_{n+1}, vx_pred)
    vx_{n+1} = vx_n + ½·(ax_n + ax_{n+1})·dt

Stopping conditions
-------------------
1. ``r ≥ R``              particle exits through the rim
2. ``r ≤ center_radius``  particle reaches the central sphere
3. ``steps_run ≥ num_steps``
"""
from __future__ import annotations

from math import log, pi, sqrt

from utils.params import SimulationMembraneParams


def _accel(
    x: float,
    y: float,
    vx: float,
    vy: float,
    *,
    g: float,
    friction_coef: float,
    R: float,
    coeff: float,          # pre-computed F / (2πT)
    center_radius: float,
) -> tuple[float, float, float]:
    """Return ``(z, ax, ay)`` at state (x, y, vx, vy).

    Uses *coeff* = F / (2πT) — pre-computed once before the integration
    loop to avoid repeating the division inside the hot path.
    """
    r = sqrt(x * x + y * y)
    r_use = r if r > center_radius else center_radius

    z = -coeff * log(R / r_use)

    if r > 1e-12:
        inv_r2 = 1.0 / (r * r)
        dz_dx = coeff * x * inv_r2
        dz_dy = coeff * y * inv_r2
    else:
        dz_dx = dz_dy = 0.0

    norm_sq = 1.0 + dz_dx * dz_dx + dz_dy * dz_dy

    # Gravity projected onto the tangent plane
    ax = -g * dz_dx / norm_sq
    ay = -g * dz_dy / norm_sq

    # Coulomb kinetic friction (slope-corrected normal force)
    vz  = dz_dx * vx + dz_dy * vy
    v3d = sqrt(vx * vx + vy * vy + vz * vz)
    if v3d > 1e-12:
        normal_acc = g / sqrt(norm_sq)
        ax -= friction_coef * normal_acc * vx / v3d
        ay -= friction_coef * normal_acc * vy / v3d

    return z, ax, ay


def simulate_membrane(sim_params: SimulationMembraneParams | None = None) -> dict:
    """Integrate the membrane trajectory and return per-frame positions.

    Args:
        sim_params: Simulation parameters.  Uses defaults if ``None``.

    Returns:
        Dict with keys ``"xs"``, ``"ys"``, ``"zs"``, ``"vxs"``, ``"vys"``
        — lists of floats, one entry per recorded frame.
    """
    if sim_params is None:
        sim_params = SimulationMembraneParams()

    g             = float(sim_params.g)
    dt            = float(sim_params.time_step)
    steps         = int(sim_params.num_steps)
    R             = float(sim_params.surface_radius)
    T             = float(sim_params.surface_tension)
    F             = float(sim_params.center_weight)
    center_radius = float(sim_params.center_radius)
    friction_coef = float(sim_params.friction_coef)

    # Pre-compute F/(2πT) — appears in every gradient evaluation
    coeff = F / (2.0 * pi * T)

    kw = dict(g=g, friction_coef=friction_coef,
              R=R, coeff=coeff, center_radius=center_radius)

    # Initial position — clamp inside the rim
    x = float(sim_params.x0)
    y = float(sim_params.y0)
    r0 = sqrt(x * x + y * y)
    if r0 >= R:
        scale = (R - 1e-6) / r0 if r0 > 1e-12 else 1.0
        x *= scale
        y *= scale

    vx = float(sim_params.vx0)
    vy = float(sim_params.vy0)

    # Bootstrap: initial acceleration
    z, ax, ay = _accel(x, y, vx, vy, **kw)

    xs:  list[float] = []
    ys:  list[float] = []
    zs:  list[float] = []
    vxs: list[float] = []
    vys: list[float] = []
    steps_run = 0

    while True:
        # Velocity-Verlet predictor-corrector
        x_next  = x  + vx * dt + 0.5 * ax * dt * dt
        y_next  = y  + vy * dt + 0.5 * ay * dt * dt
        vx_pred = vx + ax * dt
        vy_pred = vy + ay * dt

        z_next, ax_next, ay_next = _accel(x_next, y_next, vx_pred, vy_pred, **kw)

        vx_next = vx + 0.5 * (ax + ax_next) * dt
        vy_next = vy + 0.5 * (ay + ay_next) * dt

        x,  y,  z  = x_next,  y_next,  z_next
        vx, vy     = vx_next, vy_next
        ax, ay     = ax_next,  ay_next

        xs.append(x)
        ys.append(y)
        zs.append(z)
        vxs.append(vx)
        vys.append(vy)

        steps_run += 1

        r = sqrt(x * x + y * y)
        if r >= R or r <= center_radius or steps_run >= steps:
            break

    return {"xs": xs, "ys": ys, "zs": zs, "vxs": vxs, "vys": vys}
