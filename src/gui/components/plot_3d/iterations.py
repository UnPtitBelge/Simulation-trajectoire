# Euler explicite pour une particule sur une surface axisymétrique.
# Modèle analytique partagé: z(r) et (dz/dx, dz/dy) via `model.gradient_xy`.
# Forces: gravité projetée (a = -g * grad(z)) + frottement linéaire.

from __future__ import annotations

from math import sqrt
from typing import Any, Dict, List, Tuple

from .model import gradient_xy
from .simulation_params import SimulationParams


def iterations(params: SimulationParams) -> Dict[str, Any]:
    g = float(params.g)
    dt = float(params.time_step)
    steps = int(params.num_steps)

    R = float(params.surface_radius)
    T = float(params.surface_tension)
    F = float(params.center_weight)
    center_radius = float(params.center_radius)

    # Masse estimée à partir du poids: F = m*g
    m = F / g if g != 0.0 else 1.0

    x = float(params.x0)
    y = float(params.y0)

    # Si l'initialisation est hors membrane, on rabat légèrement à l'intérieur
    r0 = sqrt(x * x + y * y)
    if r0 >= R:
        if r0 > 1e-12:
            scale = (R - 1e-6) / r0
            x *= scale
            y *= scale
        else:
            x = min(R - 1e-6, R)
            y = 0.0

    vx = float(params.vx0)
    vy = float(params.vy0)

    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []

    def surface_height_and_gradient(
        xy: Tuple[float, float],
    ) -> Tuple[float, float, float]:
        x_, y_ = xy
        z, dz_dx, dz_dy = gradient_xy(
            x_,
            y_,
            R=R,
            T=T,
            F=F,
            center_radius=center_radius,
        )
        return z, dz_dx, dz_dy

    steps_run = 0
    z = 0.0

    while True:
        z, dz_dx, dz_dy = surface_height_and_gradient((x, y))

        ax_g = -g * dz_dx
        ay_g = -g * dz_dy
        ax = ax_g - (params.friction_coef / m) * vx
        ay = ay_g - (params.friction_coef / m) * vy

        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        xs.append(x)
        ys.append(y)
        zs.append(float(z))

        steps_run += 1

        r = sqrt(x * x + y * y)
        if r >= R:
            break
        if r <= center_radius:
            break
        if steps_run >= steps:
            break

    final_state = {"x": x, "y": y, "vx": vx, "vy": vy, "z": float(z)}
    return {
        "xs": xs,
        "ys": ys,
        "zs": zs,
        "steps_run": steps_run,
        "final_state": final_state,
    }
