"""Intégrateurs numériques pour r'' = a(r, v).

Convention commune :
    acc_func : (r, v) -> a, où r, v, a sont des np.ndarray de même forme.
    Chaque pas retourne (r_next, v_next, a_next).
"""

from typing import Callable
import numpy as np

State = tuple[np.ndarray, np.ndarray, np.ndarray]


def explicit_euler(
    r: np.ndarray, v: np.ndarray, acc_func: Callable, dt: float
) -> State:
    """Ordre 1, non symplectique. Énergie dérive."""
    a = acc_func(r, v)
    r_next = r + v * dt
    v_next = v + a * dt
    a_next = acc_func(r_next, v_next)
    return r_next, v_next, a_next


def semi_implicit_euler(
    r: np.ndarray, v: np.ndarray, acc_func: Callable, dt: float
) -> State:
    """Ordre 1, symplectique. Énergie bornée."""
    a = acc_func(r, v)
    v_next = v + a * dt
    r_next = r + v_next * dt
    a_next = acc_func(r_next, v_next)
    return r_next, v_next, a_next


def velocity_verlet(
    r: np.ndarray, v: np.ndarray, acc_func: Callable, dt: float
) -> State:
    """Ordre 2, symplectique pour a(r). Avec a(r, v), précision dégradée."""
    a = acc_func(r, v)
    r_next = r + v * dt + 0.5 * a * dt**2
    v_half = v + 0.5 * a * dt
    a_next = acc_func(r_next, v_half)
    v_next = v + 0.5 * (a + a_next) * dt
    return r_next, v_next, a_next


def rk4(r: np.ndarray, v: np.ndarray, acc_func: Callable, dt: float) -> State:
    """Ordre 4, non symplectique. Dérive énergétique lente."""
    k1r, k1v = v, acc_func(r, v)
    k2r, k2v = v + 0.5 * dt * k1v, acc_func(r + 0.5 * dt * k1r, v + 0.5 * dt * k1v)
    k3r, k3v = v + 0.5 * dt * k2v, acc_func(r + 0.5 * dt * k2r, v + 0.5 * dt * k2v)
    k4r, k4v = v + dt * k3v, acc_func(r + dt * k3r, v + dt * k3v)
    r_next = r + (dt / 6) * (k1r + 2 * k2r + 2 * k3r + k4r)
    v_next = v + (dt / 6) * (k1v + 2 * k2v + 2 * k3v + k4v)
    a_next = acc_func(r_next, v_next)
    return r_next, v_next, a_next
