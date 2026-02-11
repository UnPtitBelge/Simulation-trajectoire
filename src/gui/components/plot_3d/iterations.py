# Simulation-trajectoire/src/gui/components/plot_3d/iterations.py
"""
plot_3d.iterations

Euler iterations for 2D motion on an axisymmetric membrane surface using
centralized SimulationParams (no geometry objects).

Physics:
- Surface height: z(r) = -F / (2πT) * ln(R / max(r, center_radius))
- Projected gradient (matching model.gradient_xy): ∂z/∂x = (F / (2πT)) * x / r², ∂z/∂y = (F / (2πT)) * y / r²
  Note: The acceleration uses a_g = -g ∇z, so motion is directed inward along the slope toward the center.
- Tangential acceleration due to gravity: a_g = -g ∇z
- Linear friction: a_f = -(coef/m) v
- Integration: explicit Euler

Returns a Plotly-friendly dict:
    {
        "xs": [float], "ys": [float], "zs": [float],
        "steps_run": int,
        "final_state": {"x": float, "y": float, "vx": float, "vy": float},
    }
"""

from __future__ import annotations

from math import sqrt
from typing import Any, Dict, List, Tuple

from .model import gradient_xy
from .simulation_params import SimulationParams


def iterations(params: SimulationParams) -> Dict[str, Any]:
    """
    Run Euler iterations with gravity projection and linear friction.

    Args:
        params: Centralized SimulationParams (theta in degrees; v_i scalar speed).
                Uses:
                  - g, time_step, num_steps
                  - surface_radius (R), surface_tension (T)
                  - center_weight (F), center_radius
                  - x0, y0, vx0, vy0 (derived from v_i and theta)
                  - friction_coef

    Returns:
        Dict[str, Any]: Plotly-friendly results with trajectory and final state.
    """
    # Shortcuts (centralized parameters)
    g = float(params.g)
    dt = float(params.time_step)
    steps = int(params.num_steps)
    print(g, " ", steps, " ", dt)

    R = float(params.surface_radius)
    T = float(params.surface_tension)
    F = float(params.center_weight)
    center_radius = float(params.center_radius)

    # Mass from weight: F = m g -> m = F / g
    m = F / g if g != 0.0 else 1.0

    # Initial state
    x = float(params.x0)
    y = float(params.y0)
    # Validate initial position within the surface radius; clamp if outside
    r0 = sqrt(x * x + y * y)
    if r0 >= R:
        print(
            "[WARNING] Initial position outside surface: clamping to boundary just inside R."
        )
        # Clamp to slightly inside boundary along the same angle
        if r0 > 1e-12:
            scale = (R - 1e-6) / r0
            x *= scale
            y *= scale
        else:
            # Degenerate case at origin; leave as is
            x = min(R - 1e-6, R)
            y = 0.0
    vx = float(params.vx0)  # derived from v_i and theta (degrees)
    vy = float(params.vy0)

    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []

    def surface_height_and_gradient(
        xy: Tuple[float, float],
    ) -> Tuple[float, float, float]:
        """Return (z, dz_dx, dz_dy) using centralized analytical model (shared)."""
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

    while True:
        # Height and gradient at current position
        z, dz_dx, dz_dy = surface_height_and_gradient((x, y))

        # Gravity projected along the slope (toward the well)
        ax_g = -g * dz_dx
        ay_g = -g * dz_dy

        # Linear friction (direction opposite to velocity)
        ax = ax_g - (params.friction_coef / m) * vx
        ay = ay_g - (params.friction_coef / m) * vy

        # Explicit Euler integration
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        # Record history
        xs.append(x)
        ys.append(y)
        zs.append(z)
        steps_run += 1

        # Stop conditions
        r = sqrt(x * x + y * y)
        if r >= R:
            print("[WARNING] Simulation stopped: exceeded surface radius (r >= R).")
            break
        if r <= center_radius:
            print(
                "[WARNING] Simulation stopped: collision with central sphere (r <= center_radius)."
            )
            break

    final_state = {"x": x, "y": y, "vx": vx, "vy": vy}
    return {
        "xs": xs,
        "ys": ys,
        "zs": zs,
        "steps_run": steps_run,
        "final_state": final_state,
    }
