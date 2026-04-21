"""Pente locale dz/dr de la membrane pour trois modèles de surface."""

from typing import Any

import numpy as np


def cone_slope(r: float | np.ndarray, alpha_const: float) -> float | np.ndarray:
    """dz/dr = tan(alpha_const)."""
    return np.tan(alpha_const) * np.ones_like(np.asarray(r, dtype=float))


def laplace_slope(
    r: float | np.ndarray, K: np.floating[Any], m: float, g: float = 9.81
) -> float | np.ndarray:
    """dz/dr = K / (m g r²)."""
    return K / (m * g * np.asarray(r, dtype=float) ** 2)


def laplace_regularized_slope(
    r: float | np.ndarray,
    K: np.floating[Any],
    m: float,
    r_c: float,
    g: float = 9.81,
) -> float | np.ndarray:
    """Pente du modèle Laplace régularisée par un raccord C¹ avec un cône.

    Pour r ≥ r_c : dz/dr = K/(m g r²) (modèle Laplace analytique).
    Pour r <  r_c : dz/dr = K/(m g r_c²) (pente constante = cône tangent).

    Motivation — Le modèle Laplace idéalisé dérive d'une masse ponctuelle
    centrale, ce qui rend la pente divergente en 1/r² au voisinage du
    centre. Physiquement, la bille centrale a un rayon fini et sa présence
    aplatit la membrane sous elle : cette zone ressemble davantage à un
    plateau (ou à un cône peu pentu) qu'à un puits hyperbolique. On
    modélise donc la région r < r_c par un cône dont la pente est choisie
    pour raccorder exactement la pente Laplace en r = r_c.

    Conséquence : a_c = g·|dz/dr| est bornée par K/(m·r_c²) au lieu de
    diverger, ce qui supprime la stiffness numérique au périgée et rend
    l'énergie mécanique simulée stable pour un pas dt fixe.

    Le raccord est C¹ par construction mais pas C². La dérivée seconde
    (courbure) présente un saut en r_c — acceptable puisque les
    équations du mouvement ne font intervenir que la pente.
    """
    r_arr = np.asarray(r, dtype=float)
    slope_laplace = K / (m * g * r_arr**2)
    slope_cone = K / (m * g * r_c**2)
    return np.where(r_arr >= r_c, slope_laplace, slope_cone)
