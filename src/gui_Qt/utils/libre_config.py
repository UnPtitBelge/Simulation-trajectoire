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

from dataclasses import dataclass as _dataclass
from dataclasses import replace as _replace

from utils.params import (
    SimulationConeParams,
    SimulationMembraneParams,
    SimulationMCUParams,
    SimulationMLParams,
)
from utils.ui_constants import SIM_COLORS


@_dataclass(frozen=True)
class ScenarioConfig:
    """Preconfigured simulation scenario with display metadata and physics parameters.

    Attributes
    ----------
    id        Unique string identifier (never shown to users).
    sim_type  One of ``"2d_mcu"``, ``"3d_cone"``, ``"3d_membrane"``, ``"ml"``.
    title     Short display name shown on the scenario card.
    subtitle  One-line description shown below the title.
    params    Simulation parameter dataclass instance (immutable; copied before use).
    """

    id:       str
    sim_type: str
    title:    str
    subtitle: str
    params:   object


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
    surface_radius = 0.40,   # mesure réelle
    center_radius  = 0.030,  # mesure réelle
    time_step      = 0.010,
    num_steps      = 20_000,
    g              = 9.810,
    particle_radius = 0.005,  # mesure réelle
    particle_mass   = 0.010,
    x0            = 0.00,    # mesure réelle
    y0            = 0.38,    # mesure réelle (r = 0.38 m ≈ 95 % de R)
    v_i           = 1.00,    # mesure réelle
    theta         = 90.0,    # mesure réelle (tangentiel pur)
    friction_coef = 0.015,
)

MEMBRANE = SimulationMembraneParams(
    surface_tension = 10.0,
    center_weight   = 4.905,
    surface_radius  = 0.40,   # mesure réelle
    center_radius   = 0.030,  # mesure réelle
    time_step       = 0.010,
    num_steps       = 20_000,
    g               = 9.810,
    particle_radius = 0.005,  # mesure réelle
    particle_mass   = 0.010,
    x0            = 0.00,    # mesure réelle
    y0            = 0.38,    # mesure réelle (r = 0.38 m ≈ 95 % de R)
    v_i           = 1.00,    # mesure réelle
    theta         = 90.0,    # mesure réelle (tangentiel pur)
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
# Preconfigured scenarios — 3 per simulation type, ordered by sim type
# ---------------------------------------------------------------------------

SCENARIOS: list[ScenarioConfig] = [

    # ── 2D MCU ──────────────────────────────────────────────────────────

    ScenarioConfig(
        id       = "mcu_classique",
        sim_type = "2d_mcu",
        title    = "MCU Classique",
        subtitle = "Orbite circulaire à vitesse constante",
        params   = SimulationMCUParams(
            R=50.0, omega=0.60, n_orbits=3.0, initial_angle=0.0,
            center_radius=6.0, particle_radius=2.0,
        ),
    ),
    ScenarioConfig(
        id       = "mcu_rapide",
        sim_type = "2d_mcu",
        title    = "Orbiteur Rapide",
        subtitle = "Haute vitesse angulaire, cinq orbites",
        params   = SimulationMCUParams(
            R=30.0, omega=1.80, n_orbits=5.0, initial_angle=0.0,
            center_radius=5.0, particle_radius=2.0,
        ),
    ),
    ScenarioConfig(
        id       = "mcu_large",
        sim_type = "2d_mcu",
        title    = "Grande Orbite",
        subtitle = "Rayon large, mouvement lent et majestueux",
        params   = SimulationMCUParams(
            R=70.0, omega=0.25, n_orbits=2.0, initial_angle=0.0,
            center_radius=8.0, particle_radius=2.5,
        ),
    ),

    # ── 3D Cône ─────────────────────────────────────────────────────────

    ScenarioConfig(
        id       = "cone_elegant",
        sim_type = "3d_cone",
        title    = "Spirale Élégante",
        subtitle = "Faible frottement — précession visible",
        params   = SimulationConeParams(
            cone_slope=0.10, surface_radius=0.40, center_radius=0.030,
            time_step=0.010, num_steps=20_000, g=9.810,
            particle_radius=0.005, particle_mass=0.010,
            x0=0.00, y0=0.38, v_i=1.00, theta=90.0,
            friction_coef=0.006,
        ),
    ),
    ScenarioConfig(
        id       = "cone_chute",
        sim_type = "3d_cone",
        title    = "Chute Rapide",
        subtitle = "Frottement élevé — spirale serrée vers le centre",
        params   = SimulationConeParams(
            cone_slope=0.12, surface_radius=0.40, center_radius=0.030,
            time_step=0.010, num_steps=15_000, g=9.810,
            particle_radius=0.005, particle_mass=0.010,
            x0=0.00, y0=0.36, v_i=1.00, theta=85.0,
            friction_coef=0.045,
        ),
    ),
    ScenarioConfig(
        id       = "cone_stable",
        sim_type = "3d_cone",
        title    = "Orbite Quasi-Stable",
        subtitle = "Frottement minimal — orbite qui décroît très lentement",
        params   = SimulationConeParams(
            cone_slope=0.10, surface_radius=0.40, center_radius=0.030,
            time_step=0.010, num_steps=25_000, g=9.810,
            particle_radius=0.005, particle_mass=0.010,
            x0=0.00, y0=0.38, v_i=1.00, theta=90.0,
            friction_coef=0.002,
        ),
    ),

    # ── 3D Membrane ─────────────────────────────────────────────────────

    ScenarioConfig(
        id       = "membrane_classique",
        sim_type = "3d_membrane",
        title    = "Spirale Logarithmique",
        subtitle = "Trajectoire caractéristique de la membrane",
        params   = SimulationMembraneParams(
            surface_tension=10.0, center_weight=4.905,
            surface_radius=0.40, center_radius=0.030,
            time_step=0.010, num_steps=20_000, g=9.810,
            particle_radius=0.005, particle_mass=0.010,
            x0=0.00, y0=0.38, v_i=1.00, theta=90.0,
            friction_coef=0.015,
        ),
    ),
    ScenarioConfig(
        id       = "membrane_comparaison",
        sim_type = "3d_membrane",
        title    = "Comparaison avec le Cône",
        subtitle = "Mêmes conditions initiales que la Spirale Élégante",
        params   = SimulationMembraneParams(
            surface_tension=10.0, center_weight=4.905,
            surface_radius=0.40, center_radius=0.030,
            time_step=0.010, num_steps=20_000, g=9.810,
            particle_radius=0.005, particle_mass=0.010,
            x0=0.00, y0=0.38, v_i=1.00, theta=90.0,
            friction_coef=0.006,
        ),
    ),
    ScenarioConfig(
        id       = "membrane_forte",
        sim_type = "3d_membrane",
        title    = "Attraction Forte",
        subtitle = "Charge centrale élevée — accélération logarithmique",
        params   = SimulationMembraneParams(
            surface_tension=8.0, center_weight=9.810,
            surface_radius=0.40, center_radius=0.030,
            time_step=0.010, num_steps=18_000, g=9.810,
            particle_radius=0.005, particle_mass=0.010,
            x0=0.00, y0=0.36, v_i=1.00, theta=87.0,
            friction_coef=0.012,
        ),
    ),

    # ── Machine Learning ────────────────────────────────────────────────

    ScenarioConfig(
        id       = "ml_precis",
        sim_type = "ml",
        title    = "Prédiction Fidèle",
        subtitle = "Sans bruit — le modèle au mieux de ses capacités",
        params   = SimulationMLParams(
            test_initial_idx=0, noise_level=0.0,
            marker_size=10, show_true_trajectory=True,
        ),
    ),
    ScenarioConfig(
        id       = "ml_bruit",
        sim_type = "ml",
        title    = "Avec Bruit",
        subtitle = "Bruit σ = 0.04 — limites du ML visibles",
        params   = SimulationMLParams(
            test_initial_idx=0, noise_level=0.04,
            marker_size=10, show_true_trajectory=True,
        ),
    ),
    ScenarioConfig(
        id       = "ml_alternatif",
        sim_type = "ml",
        title    = "Trajectoire Alternative",
        subtitle = "Conditions initiales différentes — généralisation testée",
        params   = SimulationMLParams(
            test_initial_idx=1, noise_level=0.0,
            marker_size=10, show_true_trajectory=True,
        ),
    ),
]

# Order in which sim types appear in the landing page / nav bar
SIM_TYPE_ORDER: list[str] = ["2d_mcu", "3d_cone", "3d_membrane", "ml"]


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
        "color":    SIM_COLORS["2d_mcu"],
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
        "extreme": (
            "Que se passe-t-il aux extrêmes ?\n\n"
            "• ω → 0 : la bille se déplace infiniment lentement — elle semble immobile. "
            "La force centripète F = mω²R tend vers zéro.\n\n"
            "• ω → ∞ : à haute vitesse, la force centripète devient immense. "
            "En pratique, les systèmes réels se rompent (satellites, cordes tournantes).\n\n"
            "• R → 0 : orbite dégénérée — la bille reste au centre.\n\n"
            "• n_orbits → ∞ : sans frottement, le MCU tourne éternellement. "
            "C'est une idéalisation : aucun satellite ne reste en orbite parfaite indéfiniment."
        ),
        "compare": (
            "MCU vs simulations 3D\n\n"
            "Le MCU est le seul modèle à solution exacte : x(t) = R·cos(ωt). "
            "Aucune erreur numérique, énergie conservée parfaitement à la précision machine.\n\n"
            "Le cône et la membrane nécessitent une intégration numérique pas à pas. "
            "Ils accumulent des erreurs d'arrondi et dissipent de l'énergie via le frottement.\n\n"
            "Le MCU ne modélise ni gravité ni surface : c'est une orbite pure, impossible sans "
            "force centrale active (fusée, tension de corde). Les modèles 3D, eux, reproduisent "
            "un phénomène physique réel et observable."
        ),
        "formula_details": [
            {
                "formula": "x(t) = R · cos(ωt + φ₀)",
                "terms": [
                    ("x(t)", "Position horizontale [m]", "Coordonnée projetée sur l'axe x"),
                    ("R",    "Rayon orbital [m]",         "Distance constante au centre — contrainte imposée"),
                    ("ω",    "Vitesse angulaire [rad/s]", "ω = v/R ; constante car |v| est constant en MCU"),
                    ("t",    "Temps [s]",                 "Variable indépendante"),
                    ("φ₀",  "Phase initiale [rad]",      "Angle à t = 0"),
                ],
            },
            {
                "formula": "|v| = ω · R  (constante)",
                "terms": [
                    ("|v|", "Vitesse scalaire [m/s]", "Norme du vecteur vitesse — invariante en MCU"),
                    ("ω",   "Vitesse angulaire [rad/s]", "Pulsation angulaire"),
                    ("R",   "Rayon [m]",                "Rayon de la trajectoire circulaire"),
                ],
            },
        ],
        "fun_fact": (
            "La Station Spatiale Internationale orbite à ~28 800 km/h. "
            "C'est la vitesse tangentielle qui l'empêche de tomber : "
            "elle \"tombe\" en permanence, mais la Terre se courbe sous elle aussi vite."
        ),
    },

    "3d_cone": {
        "title":    "Surface Conique",
        "subtitle": "Modèle de Newton — pente constante",
        "color":    SIM_COLORS["3d_cone"],
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
        "extreme": (
            "Comportements extrêmes du cône\n\n"
            "• friction → 0 : sans frottement, la bille orbite indéfiniment. "
            "L'orbite est une rosette fermée — mais le frottement la transforme en spirale.\n\n"
            "• friction → 1 : frottement intense, la bille s'arrête en quelques tours. "
            "Au-delà d'un seuil critique, elle glisse radialement sans orbiter.\n\n"
            "• v_i très grande : la bille sort du cône immédiatement. "
            "L'orbite circulaire stable requiert v = √(g·sin(α)·r).\n\n"
            "• pente → 0 : surface plate, pas de force radiale — la bille part en ligne droite."
        ),
        "compare": (
            "Cône vs Membrane\n\n"
            "Force radiale — Cône : a_r = g·sin(α) = constante (indépendante de r). "
            "Membrane : a_r ∝ 1/r (diverge vers le centre).\n\n"
            "Précession — Cône : ~151°/orbite (ω_r = √3·ω_θ). "
            "Membrane : ~105°/orbite (ω_r = √2·ω_θ). "
            "Même conditions initiales, dynamiques clairement différentes.\n\n"
            "Intégrateurs — Cône : Euler semi-implicite (O(dt), symplectique). "
            "Membrane : Velocity-Verlet (O(dt²), plus précis mais plus coûteux).\n\n"
            "Le cône est plus simple mathématiquement mais moins réaliste physiquement "
            "que la membrane élastique sous charge."
        ),
        "formula_details": [
            {
                "formula": "z(r) = −pente · (R − r)",
                "terms": [
                    ("z(r)", "Hauteur de la surface [m]", "Profil du cône en fonction du rayon"),
                    ("pente","Pente radiale [sans unité]",  "tan(α) où α est le demi-angle du cône"),
                    ("R",    "Rayon du bord [m]",           "Bord extérieur de la surface"),
                    ("r",    "Rayon courant [m]",            "Distance radiale au centre"),
                ],
            },
            {
                "formula": "a_r = g · sin(α)  [constante]",
                "terms": [
                    ("a_r",    "Accélération radiale [m/s²]", "Composante vers le centre — constante sur tout le cône"),
                    ("g",      "Gravité [m/s²]",              "9.81 m/s² au sol"),
                    ("sin(α)", "Sinus de la pente",           "Fraction de g dirigée vers le centre"),
                ],
            },
        ],
        "fun_fact": (
            "Malgré sa simplicité mathématique, ce modèle décrit mieux la membrane "
            "en caoutchouc réelle que l'équation de Laplace. "
            "Parfois, moins d'équations = plus de précision."
        ),
    },

    "3d_membrane": {
        "title":    "Membrane de Laplace",
        "subtitle": "Solution exacte de ∇²z = 0",
        "color":    SIM_COLORS["3d_membrane"],
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
        "extreme": (
            "Comportements extrêmes de la membrane\n\n"
            "• F → 0 : sans charge centrale, la membrane reste plate. "
            "Pas de puit de potentiel, la bille s'éloigne en ligne droite.\n\n"
            "• F → ∞ : puit infiniment profond — la force en 1/r diverge au centre. "
            "La bille tombe inexorablement vers le centre quelle que soit sa vitesse initiale.\n\n"
            "• T → 0 : tension nulle — pente infinie partout. "
            "La membrane 'collapse' ; physiquement impossible sans déchirure.\n\n"
            "• r → 0 : force → ∞. La singularité logarithmique au centre est une idéalisation "
            "mathématique — une membrane réelle déchire avant d'atteindre r = 0."
        ),
        "compare": (
            "Membrane vs Cône\n\n"
            "Surface — Membrane : z(r) = -(F/2πT)·ln(R/r), profil logarithmique. "
            "Cône : z(r) = -pente·(R-r), profil linéaire.\n\n"
            "Force radiale — Membrane : F_r ∝ 1/r (augmente vers le centre). "
            "Cône : F_r = constante. La membrane 'aspire' de plus en plus fort.\n\n"
            "Précession — Membrane : 2π(1−1/√2) ≈ 105°/orbite. "
            "Cône : 2π(1−1/√3) ≈ 151°/orbite.\n\n"
            "La membrane est physiquement plus réaliste (wishing well réel), "
            "mais la singularité en r=0 est une limitation théorique absente du cône."
        ),
        "formula_details": [
            {
                "formula": "z(r) = −(F / 2πT) · ln(R / r)",
                "terms": [
                    ("z(r)", "Hauteur de la surface [m]",        "Profil logarithmique — solution de ∇²z = 0"),
                    ("F",    "Charge centrale [N]",              "Poids posé au centre : F = m·g"),
                    ("T",    "Tension de surface [N/m]",         "Tension de la membrane élastique"),
                    ("R",    "Rayon du bord [m]",                "Condition aux limites : z(R) = 0"),
                    ("r",    "Rayon courant [m]",                "Distance radiale — ln(R/r) > 0 pour r < R"),
                ],
            },
            {
                "formula": "dz/dr = F / (2πT · r)  [∝ 1/r]",
                "terms": [
                    ("dz/dr", "Pente locale de la surface [sans unité]", "Augmente vers le centre"),
                    ("F",     "Charge [N]",                              "Plus F est grand, plus la pente est forte"),
                    ("2πT",   "Tension × 2π",                           "Facteur géométrique — périmètre unitaire"),
                    ("r",     "Rayon [m]",                              "Singularité en r = 0 (membrane idéale)"),
                ],
            },
        ],
        "fun_fact": (
            "L'équation ∇²z = 0 gouverne aussi les champs électriques, "
            "la conduction thermique et le potentiel gravitationnel dans le vide. "
            "Une seule équation, des dizaines de phénomènes différents."
        ),
    },

    "ml": {
        "title":    "Machine Learning",
        "subtitle": "Apprendre sans équations",
        "color":    SIM_COLORS["ml"],
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
        "extreme": (
            "Limites et cas extrêmes du ML\n\n"
            "• noise_level → grand : le modèle 'hallucine' des trajectoires aléatoires. "
            "La régression linéaire n'a pas de robustesse au bruit.\n\n"
            "• Entraîné sur peu de données : le modèle sur-ajuste (overfitting). "
            "Il mémorise les exemples mais échoue sur de nouveaux cas.\n\n"
            "• Conditions hors distribution : si la bille part d'une position jamais vue "
            "à l'entraînement, la prédiction s'effondre. C'est le problème de généralisation.\n\n"
            "• Modèle parfait impossible : sans intégrer les équations de la physique, "
            "aucun modèle ML ne peut être exact — il manque d'inductive bias physique."
        ),
        "compare": (
            "ML vs Simulation physique\n\n"
            "Précision locale — Le ML prédit bien les trajectoires proches de l'entraînement. "
            "La simulation physique est exacte partout (dans la limite du modèle).\n\n"
            "Généralisation — Le ML échoue hors distribution. "
            "La simulation extrapole correctement vers des conditions jamais testées.\n\n"
            "Conservation d'énergie — La simulation conserve l'énergie (à l'erreur numérique près). "
            "Le ML peut prédire des trajectoires qui violent la physique.\n\n"
            "Interprétabilité — La simulation explique pourquoi la bille tourne (forces, lois). "
            "Le ML dit comment prédire, pas pourquoi. C'est la différence entre modèle et corrélation."
        ),
        "formula_details": [
            {
                "formula": "θ = (XᵀX)⁻¹ Xᵀy",
                "terms": [
                    ("θ",      "Paramètres du modèle",     "Vecteur de poids appris — minimise l'erreur quadratique"),
                    ("X",      "Matrice de features [N×d]","N exemples, d features (position+vitesse initiale)"),
                    ("y",      "Cibles [N×p]",             "Trajectoires complètes (p points × 2 coordonnées)"),
                    ("XᵀX",   "Matrice de Gram",           "Inversible si les features sont indépendantes"),
                    ("(XᵀX)⁻¹","Pseudo-inverse",           "Garantit la solution de moindres carrés"),
                ],
            },
            {
                "formula": "L(θ) = ||Xθ − y||²  (à minimiser)",
                "terms": [
                    ("L(θ)", "Perte quadratique",      "Erreur totale entre prédictions et vraies trajectoires"),
                    ("Xθ",   "Prédictions du modèle",  "Trajectoires prédites par régression linéaire"),
                    ("y",    "Vraies trajectoires",     "Trajectoires mesurées (données réelles)"),
                    ("||·||²","Norme L2 au carré",     "Pénalise les grandes erreurs plus que les petites"),
                ],
            },
        ],
        "fun_fact": (
            "Les grands modèles de langage comme GPT utilisent le même principe fondamental "
            "— apprendre des patterns dans des données — avec des milliards de paramètres. "
            "Le problème de généralisation hors distribution reste un défi central de l'IA."
        ),
    },
}
