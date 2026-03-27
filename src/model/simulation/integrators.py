"""Numerical integration step functions for physics simulations.

Each function advances (x, y, vx, vy) by one time step dt given an
acceleration function accel(x, y, vx, vy) -> (ax, ay).

All functions share the same signature:
    step_*(x, y, vx, vy, accel, dt) -> (x_new, y_new, vx_new, vy_new)
"""

from typing import Callable

AccelFn = Callable[[float, float, float, float], tuple[float, float]]


def step_euler_semi_implicit(
    x: float,
    y: float,
    vx: float,
    vy: float,
    accel: AccelFn,
    dt: float,
) -> tuple[float, float, float, float]:
    """Semi-implicit Euler (symplectic Euler) — order O(dt).

    Update velocity first with current acceleration, then position with
    the *new* velocity. This preserves energy better than explicit Euler.

    v(t+dt) = v(t) + a(x(t), v(t)) * dt
    x(t+dt) = x(t) + v(t+dt) * dt
    """
    ax, ay = accel(x, y, vx, vy)
    vx_new = vx + ax * dt
    vy_new = vy + ay * dt
    x_new = x + vx_new * dt
    y_new = y + vy_new * dt
    return x_new, y_new, vx_new, vy_new


def step_verlet(
    x: float,
    y: float,
    vx: float,
    vy: float,
    accel: AccelFn,
    dt: float,
) -> tuple[float, float, float, float]:
    """Velocity-Verlet (Störmer-Verlet) — order O(dt²), symplectic.

    x(t+dt) = x(t) + v(t)*dt + ½*a(t)*dt²
    a(t+dt) = accel(x(t+dt), v(t))          [approx: friction uses v(t)]
    v(t+dt) = v(t) + ½*(a(t) + a(t+dt))*dt
    """
    ax, ay = accel(x, y, vx, vy)
    dt2 = dt * dt
    x_new = x + vx * dt + 0.5 * ax * dt2
    y_new = y + vy * dt + 0.5 * ay * dt2
    ax2, ay2 = accel(x_new, y_new, vx, vy)
    vx_new = vx + 0.5 * (ax + ax2) * dt
    vy_new = vy + 0.5 * (ay + ay2) * dt
    return x_new, y_new, vx_new, vy_new


def step_rk4(
    x: float,
    y: float,
    vx: float,
    vy: float,
    accel: AccelFn,
    dt: float,
) -> tuple[float, float, float, float]:
    """Classic 4th-order Runge-Kutta — order O(dt⁴).

    4 evaluations per step. Very precise but 4× more expensive than Euler.
    Not symplectic: energy may drift on very long simulations.

    State vector: [x, y, vx, vy]
    Derivative:   [vx, vy, ax, ay]
    """
    # k1
    ax1, ay1 = accel(x, y, vx, vy)
    k1x, k1y, k1vx, k1vy = vx, vy, ax1, ay1

    # k2 — half step with k1
    hdt = 0.5 * dt
    x2 = x + k1x * hdt
    y2 = y + k1y * hdt
    vx2 = vx + k1vx * hdt
    vy2 = vy + k1vy * hdt
    ax2, ay2 = accel(x2, y2, vx2, vy2)
    k2x, k2y, k2vx, k2vy = vx2, vy2, ax2, ay2

    # k3 — half step with k2
    x3 = x + k2x * hdt
    y3 = y + k2y * hdt
    vx3 = vx + k2vx * hdt
    vy3 = vy + k2vy * hdt
    ax3, ay3 = accel(x3, y3, vx3, vy3)
    k3x, k3y, k3vx, k3vy = vx3, vy3, ax3, ay3

    # k4 — full step with k3
    x4 = x + k3x * dt
    y4 = y + k3y * dt
    vx4 = vx + k3vx * dt
    vy4 = vy + k3vy * dt
    ax4, ay4 = accel(x4, y4, vx4, vy4)
    k4x, k4y, k4vx, k4vy = vx4, vy4, ax4, ay4

    # Weighted average
    sixth = dt / 6.0
    x_new = x + sixth * (k1x + 2 * k2x + 2 * k3x + k4x)
    y_new = y + sixth * (k1y + 2 * k2y + 2 * k3y + k4y)
    vx_new = vx + sixth * (k1vx + 2 * k2vx + 2 * k3vx + k4vx)
    vy_new = vy + sixth * (k1vy + 2 * k2vy + 2 * k3vy + k4vy)

    return x_new, y_new, vx_new, vy_new
