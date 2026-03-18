"""Conditions initiales scriptées pour le mode --presentation.

Source de vérité unique pour tous les paramètres utilisés lors d'une
présentation scriptée.  Importer les constantes nommées ci-dessous ;
ne jamais dupliquer ces valeurs ailleurs dans le code.

Utilisation
-----------
Dans main.py (mode présentation uniquement) ::

    from dataclasses import replace
    from utils.presentation_config import CONE, MEMBRANE, MCU, ML

    params = replace(CONE)   # copie fraîche pour chaque onglet

Choix des conditions initiales
-------------------------------
Cône et Membrane utilisent le même ratio r/R ≈ 0.75 et la même vitesse
initiale (0.60 m/s, légèrement sous la vitesse d'orbite circulaire stable),
avec un angle quasi-tangentiel (88°).  Cela garantit que les deux simulations
partent dans des conditions comparables et que la différence de précession
est directement visible.

Notation des angles : 0° = radial vers le centre, 90° = tangentiel CCW.
"""
from __future__ import annotations

from dataclasses import replace as _replace

from utils.params import (
    SimulationConeParams,
    SimulationMembraneParams,
    SimulationMCUParams,
    SimulationMLParams,
)


# ---------------------------------------------------------------------------
# 2D MCU — 3 orbites complètes, lancement clair du mouvement circulaire
# ---------------------------------------------------------------------------

MCU = SimulationMCUParams(
    R             = 50.0,   # rayon orbital [m (unités écran)]
    omega         = 0.50,   # vitesse angulaire [rad/s]
    n_orbits      = 3.0,    # nombre d'orbites à simuler
    initial_angle = 0.0,    # angle de départ [°]
    center_radius = 6.0,    # rayon du corps central (visuel) [m]
    particle_radius = 2.0,  # rayon de la particule (visuel) [m]
)


# ---------------------------------------------------------------------------
# 3D Cône (Newton) — ~4-5 boucles de précession visibles avant d'atteindre
#                    le centre ; sert de référence pour la comparaison.
#
# Surface : z(r) = -cone_slope · (R - r)
# Force radiale : constante = g · sin(α)
# r/R initial ≈ 0.75
# ---------------------------------------------------------------------------

CONE = SimulationConeParams(
    cone_slope     = 0.10,    # pente radiale constante [sans unité]
    surface_radius = 0.80,    # rayon du bord [m]
    center_radius  = 0.035,   # rayon de la sphère centrale [m]
    time_step      = 0.010,   # pas d'intégration [s]
    num_steps      = 20_000,  # nombre maximum de pas
    g              = 9.810,   # accélération gravitationnelle [m/s²]
    particle_radius = 0.010,  # rayon de la bille [m]
    particle_mass   = 0.010,  # masse de la bille [kg]
    x0            = 0.60,     # position initiale x [m]
    y0            = 0.00,     # position initiale y [m]
    v_i           = 0.60,     # vitesse initiale [m/s]
    theta         = 88.0,     # angle de lancement [°] (quasi-tangentiel)
    friction_coef = 0.012,    # coefficient de frottement cinétique μ
)


# ---------------------------------------------------------------------------
# 3D Membrane (Laplace) — mêmes conditions relatives que le cône (r/R ≈ 0.75,
#                         même vitesse, même angle) pour une comparaison
#                         directe ; précession et spirale différentes.
#
# Surface : z(r) = -(F / 2πT) · ln(R / r)
# Force radiale : ∝ 1/r  (diverge vers le centre)
# r/R initial = 0.30 / 0.40 = 0.75
# ---------------------------------------------------------------------------

MEMBRANE = SimulationMembraneParams(
    surface_tension = 10.0,   # tension de la membrane T [N/m]
    center_weight   = 4.905,  # charge centrale F = 0.5 kg × g [N]
    surface_radius  = 0.40,   # rayon du bord [m]
    center_radius   = 0.035,  # rayon de la sphère centrale [m]
    time_step       = 0.010,  # pas d'intégration [s]
    num_steps       = 20_000, # nombre maximum de pas
    g               = 9.810,  # accélération gravitationnelle [m/s²]
    particle_radius = 0.010,  # rayon de la bille [m]
    particle_mass   = 0.010,  # masse de la bille [kg]
    x0            = 0.30,     # position initiale x [m]  (r/R = 0.75)
    y0            = 0.00,     # position initiale y [m]
    v_i           = 0.60,     # vitesse initiale [m/s]   (identique au cône)
    theta         = 88.0,     # angle de lancement [°]   (identique au cône)
    friction_coef = 0.012,    # coefficient de frottement cinétique μ
)


# ---------------------------------------------------------------------------
# Machine Learning — trajectoire propre, vraie trajectoire affichée
# ---------------------------------------------------------------------------

ML = SimulationMLParams(
    test_initial_idx     = 0,     # indice de l'exemple de test
    noise_level          = 0.0,   # bruit ajouté à la prédiction [m]
    marker_size          = 10,    # taille du marqueur animé [px]
    show_true_trajectory = True,  # afficher la trajectoire réelle
)


# ---------------------------------------------------------------------------
# Utilitaire — copie fraîche d'un paramètre de présentation
# ---------------------------------------------------------------------------

def fresh(params: object) -> object:
    """Retourne une copie indépendante d'un paramètre de présentation.

    Utiliser cette fonction dans les factories de main.py pour que chaque
    onglet dispose de sa propre instance mutable, sans modifier la constante
    du module.

    Exemple ::

        from utils.presentation_config import CONE, fresh
        plot = PlotCone(fresh(CONE))
    """
    return _replace(params)
