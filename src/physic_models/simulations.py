"""Génération de trajectoires par intégration numérique."""

from typing import Callable
import numpy as np

Results = tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]


def simulate(
    r0: np.ndarray,
    v0: np.ndarray,
    acc_func: Callable,
    integrator: Callable,
    dt: float,
    stop_condition: Callable,
    max_steps: int = 1_000_000,
) -> Results:
    """Intègre jusqu'à stop_condition(r, v) ou max_steps."""
    t_list = [0.0]
    r_list = [r0.copy()]
    v_list = [v0.copy()]
    a_list = [acc_func(r0, v0)]

    r, v = r0.copy(), v0.copy()
    for i in range(max_steps):
        if stop_condition(r, v):
            break
        r, v, a = integrator(r, v, acc_func, dt)
        t_list.append((i + 1) * dt)
        r_list.append(r.copy())
        v_list.append(v.copy())
        a_list.append(a)

    return (np.array(t_list), np.array(r_list), np.array(v_list), np.array(a_list))


def stop_after(n_steps: int) -> Callable:
    """Condition d'arrêt après n_steps pas."""
    counter = {"i": 0}

    def condition(r, v):
        counter["i"] += 1
        return counter["i"] > n_steps

    return condition


def stop_at_radius(r_min: float, r_max: float) -> Callable:
    """Condition d'arrêt quand |r| <= r_min (centre atteint) ou |r| >= r_max (sortie)."""

    def condition(r, v):
        rn = np.linalg.norm(r)
        return rn <= r_min or rn >= r_max

    return condition
