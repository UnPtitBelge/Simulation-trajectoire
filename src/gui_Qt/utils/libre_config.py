"""Configuration pour le mode --libre (dashboard interactif public).

Source de vérité unique pour :
- Les conditions initiales du mode libre (orbites visuellement frappantes)
- Le contenu textuel du dashboard à 3 niveaux
- Les équations clés et anecdotes par simulation

Utilisation
-----------
    from utils import libre_config

    params = libre_config.fresh(libre_config.CONE)
    content = libre_config.CONTENT["3d_cone"]
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
# Conditions initiales — optimisées pour montrer de belles orbites d'emblée
# ---------------------------------------------------------------------------

MCU = SimulationMCUParams(
    R             = 50.0,
    omega         = 0.80,   # plus rapide qu'en présentation → dynamique
    n_orbits      = 6.0,    # tourne longtemps, le public peut observer
    initial_angle = 0.0,
    center_radius = 6.0,
    particle_radius = 2.0,
)

CONE = SimulationConeParams(
    cone_slope     = 0.10,
    surface_radius = 0.80,
    center_radius  = 0.035,
    time_step      = 0.010,
    num_steps      = 20_000,
    g              = 9.810,
    particle_radius = 0.010,
    particle_mass   = 0.010,
    x0            = 0.65,   # r/R ≈ 0.81 → belle orbite ample
    y0            = 0.00,
    v_i           = 0.65,
    theta         = 88.0,
    friction_coef = 0.015,
)

MEMBRANE = SimulationMembraneParams(
    surface_tension = 10.0,
    center_weight   = 4.905,
    surface_radius  = 0.40,
    center_radius   = 0.035,
    time_step       = 0.010,
    num_steps       = 20_000,
    g               = 9.810,
    particle_radius = 0.010,
    particle_mass   = 0.010,
    x0            = 0.32,   # r/R ≈ 0.80
    y0            = 0.00,
    v_i           = 0.65,
    theta         = 88.0,
    friction_coef = 0.015,
)

ML = SimulationMLParams(
    test_initial_idx     = 0,
    noise_level          = 0.0,
    marker_size          = 10,
    show_true_trajectory = True,
)


def fresh(params: object) -> object:
    """Retourne une copie indépendante d'un paramètre libre."""
    return _replace(params)


# ---------------------------------------------------------------------------
# Contenu textuel du dashboard
# ---------------------------------------------------------------------------
# Chaque entrée contient :
#   title          Titre affiché dans l'en-tête (peut contenir \n)
#   subtitle       Sous-titre discret
#   color          Couleur accentuée (#rrggbb)
#   key_equation   Formule(s) clé(s) en police monospace
#   levels         Dict avec 3 niveaux : "decouverte", "lycee", "avance"
#   fun_fact       Anecdote affichée en bas du dashboard

CONTENT: dict[str, dict] = {

    "2d_mcu": {
        "title":    "Mouvement Circulaire\nUniforme",
        "subtitle": "Le cas idéal — solution exacte",
        "color":    "#06d6a0",
        "key_equation": (
            "x(t) = R · cos(ωt + φ₀)\n"
            "y(t) = R · sin(ωt + φ₀)\n"
            "|v|  = ω · R  (constante)"
        ),
        "levels": {
            "decouverte": (
                "La bille tourne en cercle parfait à vitesse constante. "
                "Elle ne ralentit jamais, ne s'écarte jamais de son chemin.\n\n"
                "C'est le mouvement le plus simple qui soit — et pourtant, "
                "il décrit l'orbite des satellites autour de la Terre !"
            ),
            "lycee": (
                "Le MCU est décrit exactement par x(t) = R·cos(ωt) et y(t) = R·sin(ωt). "
                "La vitesse est constante |v| = ωR, et l'accélération centripète "
                "ac = ω²R pointe toujours vers le centre.\n\n"
                "Il n'y a pas d'intégration numérique ici : la formule donne la position "
                "exacte à tout instant. C'est ce qu'on appelle une solution analytique."
            ),
            "avance": (
                "Le MCU est le seul cas présenté ayant une solution analytique exacte. "
                "La trajectoire x(t) = R·cos(ωt + φ₀) est intégrable en fermé — "
                "aucune erreur numérique, énergie conservée à la machine.\n\n"
                "Les simulations 3D nécessitent, elles, une intégration numérique "
                "(Euler semi-implicite O(dt) pour le cône, Velocity-Verlet O(dt²) pour "
                "la membrane). La simplicité du MCU vient de l'absence de degré "
                "de liberté radial : r est contraint constant par construction."
            ),
        },
        "fun_fact": (
            "La Station Spatiale Internationale orbite à ~28 800 km/h. "
            "C'est la vitesse tangentielle qui l'empêche de tomber : "
            "elle \"tombe\" en permanence, mais la Terre se courbe sous elle aussi vite."
        ),
    },

    "3d_cone": {
        "title":    "Surface Conique",
        "subtitle": "Modèle de Newton — pente constante",
        "color":    "#ff6b35",
        "key_equation": (
            "z(r) = −pente · (R − r)\n"
            "a_r  = g · sin(α)  [N/kg, constant]"
        ),
        "levels": {
            "decouverte": (
                "La bille glisse sur un cône et tourne en spirale de plus en plus serrée. "
                "Comme une pièce de monnaie dans un wishing well !\n\n"
                "La pente est identique partout sur le cône : la bille est attirée vers "
                "le centre avec la même force, quelle que soit sa position."
            ),
            "lycee": (
                "Sur un cône de demi-angle α, la composante gravitationnelle le long "
                "de la surface est constante : a = g·sin(α). "
                "Le frottement de Coulomb dissipe l'énergie, causant la spirale.\n\n"
                "L'orbite est une rosette qui précesse d'environ 151° à chaque révolution "
                "— elle ne se referme jamais. Ce n'est pas une ellipse !"
            ),
            "avance": (
                "Force centrale constante F(r) = −g·sin(α). "
                "Potentiel effectif : V_eff(r) = L²/2r² + g·sin(α)·r. "
                "Orbite circulaire stable : r_eq = (L²/g·sin(α))^(1/3).\n\n"
                "ω_r = √3·ω_θ → précession de 2π(1−1/√3) ≈ 151°/orbite. "
                "Intégrateur : Euler semi-implicite (symplectique, O(dt)) — "
                "v += a·dt, puis x += v·dt."
            ),
        },
        "fun_fact": (
            "Malgré sa simplicité mathématique, ce modèle décrit mieux la membrane "
            "en caoutchouc réelle que l'équation de Laplace. "
            "Parfois, moins d'équations = plus de précision."
        ),
    },

    "3d_membrane": {
        "title":    "Membrane de Laplace",
        "subtitle": "Solution exacte de ∇²z = 0",
        "color":    "#118ab2",
        "key_equation": (
            "z(r) = −(F/2πT) · ln(R/r)\n"
            "dz/dr = F / (2πT · r)  [∝ 1/r]"
        ),
        "levels": {
            "decouverte": (
                "La bille glisse sur une membrane tendue comme un tissu élastique. "
                "Plus elle s'approche du centre, plus elle est attirée fort — "
                "la spirale s'accélère vers la fin !\n\n"
                "Comparez la trajectoire avec le modèle conique : "
                "même départ, orbites différentes."
            ),
            "lycee": (
                "La surface suit z(r) = −(F/2πT)·ln(R/r), solution de l'équation de Laplace "
                "pour une membrane sous tension T avec une charge F au centre. "
                "La pente varie en 1/r : la force augmente vers le centre.\n\n"
                "L'orbite précesse d'environ 105° par tour — différent du cône (151°). "
                "Même conditions initiales, dynamique radicalement différente."
            ),
            "avance": (
                "Potentiel logarithmique V_eff(r) = L²/2r² + g·(F/2πT)·ln(r). "
                "Orbite circulaire : r_eq = L/√(g·F/2πT). "
                "ω_r = √2·ω_θ → précession de 2π(1−1/√2) ≈ 105°/orbite.\n\n"
                "Intégrateur Velocity-Verlet (O(dt²)) — nécessaire car la force dépend "
                "de la vitesse (frottement). Note : ce modèle suppose une membrane idéale "
                "à charge ponctuelle ; la membrane réelle est mieux approchée par le cône."
            ),
        },
        "fun_fact": (
            "L'équation ∇²z = 0 gouverne aussi les champs électriques, "
            "la conduction thermique et le potentiel gravitationnel dans le vide. "
            "Une seule équation, des dizaines de phénomènes différents."
        ),
    },

    "ml": {
        "title":    "Machine Learning",
        "subtitle": "Apprendre sans équations",
        "color":    "#ef476f",
        "key_equation": (
            "θ = (XᵀX)⁻¹ Xᵀy\n"
            "(régression linéaire)"
        ),
        "levels": {
            "decouverte": (
                "L'ordinateur a regardé des centaines de trajectoires et a appris à prédire "
                "la suivante — sans jamais voir les équations de la physique !\n\n"
                "Comparez la courbe prédite avec la vraie trajectoire. "
                "La machine fait de son mieux... mais elle ne comprend pas pourquoi "
                "la bille tourne comme ça."
            ),
            "lycee": (
                "Un modèle de régression linéaire est entraîné sur des positions mesurées. "
                "Il apprend des corrélations dans les données, sans aucun modèle physique.\n\n"
                "Résultat : il prédit bien les cas proches de l'entraînement, "
                "mais échoue en dehors. Il ne peut pas vous dire quelle force agit "
                "sur la bille, ni pourquoi l'orbite précesse."
            ),
            "avance": (
                "Régression linéaire : θ = (XᵀX)⁻¹Xᵀy minimise ||Xθ − y||². "
                "Le modèle interpole dans la distribution d'entraînement "
                "mais extrapole mal (pas d'inductive bias physique).\n\n"
                "Il ne respecte pas la conservation d'énergie ni les contraintes "
                "géométriques. Un réseau de neurones ferait mieux en interpolation, "
                "mais le problème de généralisation hors distribution reste ouvert."
            ),
        },
        "fun_fact": (
            "Les grands modèles de langage comme GPT utilisent le même principe fondamental "
            "— apprendre des patterns dans des données — avec des milliards de paramètres. "
            "Le problème de généralisation hors distribution reste un défi central de l'IA."
        ),
    },
}
