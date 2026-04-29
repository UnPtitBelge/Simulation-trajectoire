"""Équations du mouvement d'une bille sur membrane élastique."""

from typing import Any, Callable
import numpy as np


def cone_velocity(
    r: float | np.ndarray, alpha_const: float, g: float = 9.81
) -> float | np.ndarray:
    """v(r) = sqrt(g tan(alpha_const) r)."""
    return np.sqrt(g * np.tan(alpha_const) * np.asarray(r, dtype=float))


def laplace_velocity(r: float | np.ndarray, K: float, m: float) -> float | np.ndarray:
    """v(r) = sqrt(K / (m r))."""
    return np.sqrt(K / (m * np.asarray(r, dtype=float)))


def cone_orbital_period(
    r: float | np.ndarray, alpha_const: float, g: float = 9.81
) -> float | np.ndarray:
    """T = 2π r / v(r). Can be used for analysis"""
    return 2 * np.pi * np.asarray(r, dtype=float) / cone_velocity(r, alpha_const, g)


def laplace_orbital_period(
    r: float | np.ndarray, K: float, m: float
) -> float | np.ndarray:
    """T = 2π r / v(r)."""
    return 2 * np.pi * np.asarray(r, dtype=float) / laplace_velocity(r, K, m)


def cone_surface_height(
    r: np.floating[Any], alpha_const: float, r_min: float
) -> float | np.ndarray:
    """z(r) = tan(alpha_const) (r - r_min)."""
    return np.tan(alpha_const) * (np.asarray(r, dtype=float) - r_min)


def laplace_surface_height(
    r: np.floating[Any],
    K: np.floating[Any],
    m: float,
    g: float = 9.81,
    r_min: float | None = None,
) -> float | np.ndarray:
    """z(r) = K/(m g) (1/r_min - 1/r)."""
    if r_min is None:
        raise ValueError("r_min requis.")
    return (K / (m * g)) * (1 / r_min - 1 / np.asarray(r, dtype=float))


def laplace_regularized_surface_height(
    r: np.floating[Any],
    K: np.floating[Any],
    m: float,
    r_c: float,
    g: float = 9.81,
    r_min: float | None = None,
) -> float | np.ndarray:
    """Hauteur Laplace avec raccord C¹ par cône tangent pour r < r_c.

    Construction — On intègre la pente régularisée (cf.
    ``surfaces.laplace_regularized_slope``) :

        Pour r ≥ r_c :   z(r) = K/(m g) · (1/r_min − 1/r)        (Laplace)
        Pour r <  r_c :  z(r) = z(r_c) + K/(m g r_c²) · (r − r_c)  (cône)

    La convention de référence z(r_min) = 0 est conservée pour la branche
    Laplace. Dans la branche conique, z décroît linéairement depuis z(r_c)
    avec la pente Laplace gelée à r = r_c. La continuité de la valeur et
    de la dérivée en r_c est garantie par construction.

    Utilisée comme potentiel : Ep(r) = m g z(r). Le terme dominant
    K/r_min (très grand pour r_min petit) ne disparaît pas mais la zone
    r < r_c n'introduit plus de stiffness dans l'intégration.
    """
    if r_min is None:
        raise ValueError("r_min requis.")
    r_arr = np.asarray(r, dtype=float)
    z_laplace = (K / (m * g)) * (1 / r_min - 1 / r_arr)
    z_at_rc = (K / (m * g)) * (1 / r_min - 1 / r_c)
    slope_c = K / (m * g * r_c**2)
    z_cone = z_at_rc + slope_c * (r_arr - r_c)
    return np.where(r_arr >= r_c, z_laplace, z_cone)


def cone_potential_energy(
    r: np.floating[Any],
    alpha_const: float,
    m: float,
    g: float = 9.81,
    r_min: float | None = None,
) -> float | np.ndarray:
    """Ep = m g z(r)."""
    if r_min is None:
        raise ValueError("r_min requis.")
    return m * g * cone_surface_height(r, alpha_const, r_min)


def laplace_potential_energy(
    r: np.floating[Any],
    K: np.floating[Any],
    m: float,
    g: float = 9.81,
    r_min: float | None = None,
) -> float | np.ndarray:
    """Ep = m g z(r)."""
    if r_min is None:
        raise ValueError("r_min requis.")
    return m * g * laplace_surface_height(r, K, m, g, r_min)


def kinetic_energy_rolling(
    m: float, v: np.floating[Any], factor: float = 7 / 10
) -> float | np.ndarray:
    """Ec = factor m v². factor = 7/10 (sphère pleine), 5/6 (creuse), 3/4 (cylindre)."""
    return factor * m * np.asarray(v, dtype=float) ** 2


def cone_mechanical_energy(
    m: float,
    v: np.floating[Any],
    r: np.floating[Any],
    alpha_const: float,
    g: float = 9.81,
    r_min: float | None = None,
    factor: float = 7 / 10,
) -> float | np.ndarray:
    """Em = Ec + Ep."""
    return cone_potential_energy(r, alpha_const, m, g, r_min) + kinetic_energy_rolling(
        m, v, factor
    )


def laplace_mechanical_energy(
    m: float,
    v: np.floating[Any],
    r: np.floating[Any],
    K: np.floating[Any],
    g: float = 9.81,
    r_min: float | None = None,
    factor: float = 7 / 10,
) -> float | np.ndarray:
    """Em = Ec + Ep."""
    return laplace_potential_energy(r, K, m, g, r_min) + kinetic_energy_rolling(
        m, v, factor
    )


def laplace_regularized_potential_energy(
    r: np.floating[Any],
    K: np.floating[Any],
    m: float,
    r_c: float,
    g: float = 9.81,
    r_min: float | None = None,
) -> float | np.ndarray:
    """Ep = m g z(r), avec z régularisé par un cône pour r < r_c."""
    if r_min is None:
        raise ValueError("r_min requis.")
    return m * g * laplace_regularized_surface_height(r, K, m, r_c, g, r_min)


def laplace_regularized_mechanical_energy(
    m: float,
    v: np.floating[Any],
    r: np.floating[Any],
    K: np.floating[Any],
    r_c: float,
    g: float = 9.81,
    r_min: float | None = None,
    factor: float = 7 / 10,
) -> float | np.ndarray:
    """Em = Ec + Ep pour le modèle Laplace régularisé (cône tangent r < r_c)."""
    return laplace_regularized_potential_energy(
        r, K, m, r_c, g, r_min
    ) + kinetic_energy_rolling(m, v, factor)


def centripetal_acceleration(
    r: np.floating[Any], slope_func: Callable, g: float = 9.81
) -> float | np.ndarray:
    """a_c = g |dz/dr|."""
    return g * np.abs(slope_func(np.asarray(r, dtype=float)))
