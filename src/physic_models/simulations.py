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


def simulate_adaptive(
    r0: np.ndarray,
    v0: np.ndarray,
    acc_func: Callable,
    integrator: Callable,
    dt_func: Callable,
    stop_condition: Callable,
    max_steps: int = 1_000_000,
) -> Results:
    """Intègre avec un pas dt variable, retourné par dt_func(r, v) -> float.

    Utilisé quand la stiffness varie beaucoup selon la position (modèle
    Laplace pur, potentiel en 1/r) : un dt fixe calibré sur le périgée
    serait inutilement petit à l'apogée. Un dt local ajusté à l'échelle
    de temps orbital local garde une précision uniforme le long de la
    trajectoire.
    """
    t_list = [0.0]
    r_list = [r0.copy()]
    v_list = [v0.copy()]
    a_list = [acc_func(r0, v0)]
    t_current = 0.0

    r, v = r0.copy(), v0.copy()
    for _ in range(max_steps):
        if stop_condition(r, v):
            break
        dt = dt_func(r, v)
        r, v, a = integrator(r, v, acc_func, dt)
        t_current += dt
        t_list.append(t_current)
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
