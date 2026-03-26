"""Simulation content data - titles, descriptions, equations, and explanations."""

APP_TITLE = "Simulation Trajectoire"

WELCOME_TITLE = "Comment les ordinateurs simulent-ils la réalité ?"
WELCOME_SUBTITLE = (
    "Explorez la physique des trajectoires à travers cinq simulations interactives."
)
WELCOME_INTRO = (
    "Cette application accompagne une expérience concrète : une bille lancée sur "
    "une surface courbée (cône ou membrane). Chaque simulation propose une façon "
    "différente de décrire ce phénomène.\n\n"
    "Ce que vous découvrirez :\n"
    "• Qu'est-ce qu'un modèle ? (MCU 2D)\n"
    "• Comment Newton décrit le mouvement sur un cône (3D Cône)\n"
    "• Pourquoi plus d'équations ≠ meilleur modèle (3D Membrane)\n"
    "• Ce que le Machine Learning sait — et ne sait pas — faire\n"
    "• Sim-to-Real : entraîner le ML sur des données synthétiques\n\n"
    "Message central : un modèle n'est pas jugé au nombre d'équations "
    "qu'il contient, mais par la pertinence de ses hypothèses."
)

SIM = {
    "mcu": {
        "title": "MCU 2D — Qu'est-ce qu'un modèle ?",
        "short": "Mouvement circulaire uniforme : formule exacte, zéro approximation.",
        "tagline": "Un modèle, c'est un ensemble de décisions sur ce qu'on garde et ce qu'on ignore.",
        "equations": "x(t) = R·cos(ωt)   y(t) = R·sin(ωt)",
        "beginner": (
            "Imaginez une balle attachée à une ficelle qu'on fait tourner. "
            "Elle tourne en cercle à vitesse constante — c'est le mouvement "
            "circulaire uniforme (MCU).\n\n"
            "Ici, la position est donnée par une formule exacte. "
            "Il n'y a pas d'approximation, pas d'erreur. "
            "L'équation EST la réalité — du moins pour ce cas simple.\n\n"
            "Un modèle, c'est un ensemble de décisions sur ce qu'on garde "
            "et ce qu'on ignore. Ici on a tout gardé car c'est simple."
        ),
        "intermediate": (
            "Le MCU est décrit par :\n"
            "  x(t) = R·cos(ωt),  y(t) = R·sin(ωt)\n\n"
            "La vitesse a pour norme v = Rω et l'accélération centripète "
            "est a = Rω² = v²/R, dirigée vers le centre.\n\n"
            "Avec amortissement : r(t) = R·exp(-γt), "
            "la trajectoire devient une spirale logarithmique.\n\n"
            "Ce modèle est analytique : on calcule la position exacte "
            "à chaque instant, sans intégration numérique."
        ),
        "advanced": (
            "En coordonnées polaires amorties :\n"
            "  r(t) = R·exp(-γt),  θ(t) = ωt\n\n"
            "Composantes de vitesse : vᵣ = -γR·exp(-γt),  v_θ = ωR·exp(-γt)\n"
            "Énergie cinétique : E(t) = ½m(γ²+ω²)R²·exp(-2γt)\n\n"
            "Le moment cinétique L = mr²θ̇ = mωR²·exp(-2γt) décroît "
            "avec le frottement. Sans frottement : L = constante.\n\n"
            "Limite du modèle : dès qu'on ajoute une surface 3D ou des "
            "conditions initiales complexes, cette formule ne suffit plus."
        ),
    },
    "cone": {
        "title": "Cône 3D — Modéliser avec Newton",
        "short": "Bille sur cône de pente constante. Newton + frottement de Coulomb.",
        "tagline": "Un bon modèle est un modèle dont on connaît et assume les hypothèses.",
        "equations": "z(r) = -pente·(R−r)  a = g·sin(α) = cst  frottement: μ·g·cos(α)",
        "beginner": (
            "On lance une bille sur la paroi intérieure d'un entonnoir. "
            "Elle ne tombe pas tout droit — elle orbite ! L'orbite n'est pas "
            "un cercle parfait : elle se décale à chaque tour (précession). "
            "Avec le temps, le frottement fait spiraler la bille vers le centre.\n\n"
            "Pour simuler ça, on utilise les lois de Newton. La pente du cône "
            "est constante, donc la force de gravité le long de la surface "
            "est la même partout. Un seul paramètre à mesurer : la pente."
        ),
        "intermediate": (
            "Surface : z(r) = -pente·(R − r), pente = tan(α)\n"
            "Accélération gravitationnelle le long de la surface :\n"
            "  a_grav = g·sin(α) = constante\n\n"
            "Frottement de Coulomb (opposé à la vitesse) :\n"
            "  F_frot = μ·m·g·cos(α)·v̂\n\n"
            "Simplifications explicites :\n"
            "  • Pas de résistance de l'air\n"
            "  • Pas de rotation propre (point matériel)\n"
            "  • Pente parfaitement constante\n\n"
            "Intégration : Euler semi-implicite (v puis x).\n"
            "Résultat : des orbites en rosette avec précession ≈ 151°/tour."
        ),
        "advanced": (
            "En coordonnées cartésiennes (x,y), avec r = √(x²+y²) :\n\n"
            "  sin(α) = pente/√(1+pente²)\n"
            "  cos(α) = 1/√(1+pente²)\n\n"
            "  aₓ = −g·sin(α)·x/r − μ·g·cos(α)·vₓ/|v|\n"
            "  aᵧ = −g·sin(α)·y/r − μ·g·cos(α)·vᵧ/|v|\n\n"
            "Euler semi-implicite :\n"
            "  v(t+dt) = v(t) + a·dt\n"
            "  x(t+dt) = x(t) + v(t+dt)·dt\n\n"
            "Ce schéma est symplectique d'ordre 1 : il conserve mieux "
            "l'énergie qu'un Euler explicite classique.\n\n"
            "Ce modèle est bon car sa simplification (pente constante) "
            "colle bien à l'objet physique réel (un cône en plastique)."
        ),
    },
    "membrane": {
        "title": "Membrane 3D — Plus d'équations ≠ meilleur",
        "short": "Laplace : z(r) = −(F/2πT)·ln(R/r). Force en 1/r, diverge au centre.",
        "tagline": "La complexité mathématique ne garantit pas la précision.",
        "equations": "z(r) = −(F/2πT)·ln(R/r)   dz/dr = F/(2πT·r)   Verlet vitesse",
        "beginner": (
            "Même bille, mêmes conditions initiales, mais sur une surface "
            "calculée par l'équation de Laplace. Cette équation décrit "
            "une membrane élastique idéale sous tension.\n\n"
            "Résultat surprenant : la trajectoire est MOINS réaliste "
            "que celle du cône ! Pourquoi ? Parce que la membrane en "
            "caoutchouc réelle ressemble plus à un cône (pente constante) "
            "qu'à un profil logarithmique.\n\n"
            "Leçon : la complexité mathématique ne garantit pas la précision."
        ),
        "intermediate": (
            "Solution de Laplace pour une membrane circulaire en tension T, "
            "charge ponctuelle F au centre, fixée au bord (r=R) :\n"
            "  z(r) = −(F/2πT)·ln(R/r)\n\n"
            "La pente varie en 1/r : dz/dr = F/(2πT·r)\n"
            "  → Près du bord : pente ≈ 0 → force trop faible\n"
            "  → Près du centre : pente → ∞ → force trop forte\n\n"
            "Intégration : Verlet vitesse (ordre 2, plus précis).\n"
            "Projection exacte de la gravité sur le plan tangent.\n"
            "Précession ≈ 105°/tour (vs 151° pour le cône)."
        ),
        "advanced": (
            "L'équation de Laplace ∇²z = 0 en symétrie cylindrique :\n"
            "  (1/r)·d/dr(r·dz/dr) = 0  →  z(r) = C₁·ln(r) + C₂\n\n"
            "Avec z(R)=0 et une charge F au centre :\n"
            "  C₁ = F/(2πT),  C₂ = −C₁·ln(R)\n"
            "  z(r) = −A·ln(R/r),  A = F/(2πT)\n\n"
            "Dynamique en cartésien avec Verlet vitesse :\n"
            "  slope(r) = A/r\n"
            "  sin(α) = slope/√(1+slope²)\n"
            "  cos(α) = 1/√(1+slope²)\n\n"
            "  x½ = x + ½dt·vₓ\n"
            "  aₓ = −g·sin(α)·x/r − μ·g·cos(α)·vₓ/|v|\n"
            "  vₓ += aₓ·dt\n"
            "  x = x½ + ½dt·vₓ\n\n"
            "Le paradoxe : ce modèle est mathématiquement rigoureux "
            "mais physiquement inadapté. Le cône, simple, décrit mieux "
            "la réalité car ses hypothèses correspondent à l'objet."
        ),
    },
    "ml": {
        "title": "Machine Learning — Sans équations",
        "short": "Régression entraînée sur des données réelles. Pas de physique.",
        "tagline": "Le ML mémorise des exemples. Les modèles physiques encodent une compréhension.",
        "equations": "entrée : (x₀,y₀,vx₀,vy₀)   sortie : (x₁…x₂₀, y₁…y₂₀)   min Σ(y−ŷ)²",
        "beginner": (
            "Et si on supprimait les équations ? Le Machine Learning "
            "apprend à prédire la trajectoire à partir de données, "
            "sans jamais voir une seule équation de physique.\n\n"
            "Ici, on lui montre jusqu'à 15 trajectoires filmées : "
            "il apprend que depuis telle position et telle vitesse initiale, "
            "la bille suit tel chemin. On lui donne ensuite de nouvelles "
            "conditions initiales — et il prédit les 20 positions suivantes.\n\n"
            "Hors de ses données d'entraînement, il échoue — "
            "souvent sans le signaler."
        ),
        "intermediate": (
            "Deux régressions linéaires sur 17 trajectoires de suivi vidéo :\n"
            "  model_x : (x₀, y₀, vx₀, vy₀) → (x₁, …, x₂₀)\n"
            "  model_y : (x₀, y₀, vx₀, vy₀) → (y₁, …, y₂₀)\n\n"
            "Chaque trajectoire = 1 échantillon. "
            "15 trajectoires pour l'entraînement, 2 retenues pour le test. "
            "Le modèle apprend la physique implicitement — sans connaître g.\n\n"
            "Métriques : R² et RMSE (en pixels) sur les 20 positions cibles.\n"
            "Moins de trajectoires d'entraînement → moins bonne généralisation."
        ),
        "advanced": (
            "Solution par moindres carrés : B = (XᵀX)⁻¹Xᵀy\n"
            "X : matrice (n_train × 4) des conditions initiales\n"
            "y : matrice (n_train × 20) des positions cibles\n\n"
            "Avec n_train = 15 et p = 4 variables, le système est "
            "surcontraint (15 > 4) : chaque régression est bien posée.\n\n"
            "Différence fondamentale avec les modèles physiques :\n"
            "• Modèle physique → encode de la compréhension (lois de Newton)\n"
            "• ML → encode des patterns (corrélations statistiques)\n"
            "• Physique → extrapole hors du domaine observé\n"
            "• ML → interpole seulement dans le domaine d'entraînement\n\n"
            "Le ML ne modélise pas la réalité — il mémorise des exemples. "
            "Avec 3 trajectoires seulement, l'erreur RMSE triple. "
            "Hors distribution (y₀ = 300 px, jamais vu), la prédiction diverge."
        ),
    },
    "sim_to_real": {
        "title": "Sim-to-Real — Données synthétiques",
        "short": "Entraîner le ML sur des simulations plutôt que sur des données réelles.",
        "tagline": "La simulation peut remplacer la réalité… si le modèle physique est bon.",
        "equations": "données cône → CSV → régression linéaire → prédiction trajectoire",
        "beginner": (
            "Et si, au lieu de filmer une vraie bille des centaines de fois, "
            "on entraînait le modèle ML sur des simulations ?\n\n"
            "C'est le concept du Sim-to-Real : on génère ici 150 trajectoires "
            "de bille sur cône (simulation Newton), on les enregistre dans un "
            "tableau, puis on entraîne la régression linéaire dessus.\n\n"
            "Résultat : avec beaucoup de données synthétiques, le modèle "
            "prédit très bien. La simulation remplace le laboratoire — "
            "à condition que le modèle physique soit fidèle à la réalité."
        ),
        "intermediate": (
            "Pipeline Sim-to-Real :\n"
            "  1. Générer N trajectoires cône (CI aléatoires : r₀, v₀, φ₀)\n"
            "  2. Enregistrer (x, y, vx, vy) dans un CSV\n"
            "  3. Entraîner deux régressions linéaires (x et y séparés)\n"
            "  4. Évaluer sur les 2 dernières trajectoires (holdout)\n\n"
            "Avantage clé : N peut être aussi grand qu'on veut — "
            "la simulation est gratuite, les données réelles sont chères.\n\n"
            "Limite : si le modèle physique (cône) ne correspond pas "
            "à la réalité expérimentale, les prédictions seront biaisées. "
            "C'est le 'reality gap' du Sim-to-Real."
        ),
        "advanced": (
            "Avec N_train = 148 trajectoires, la matrice X est (148 × 4).\n"
            "XᵀX est (4 × 4) et bien conditionnée (CI très diversifiées).\n\n"
            "Contrairement au cas avec 15 trajectoires réelles :\n"
            "  • Le ratio n/p = 148/4 = 37 (vs 15/4 = 3.75)\n"
            "  • La variance des estimateurs est ≈ 10× plus faible\n"
            "  • Le R² sur holdout est typiquement > 0.99\n\n"
            "Le 'reality gap' se quantifie en comparant :\n"
            "  • RMSE (sim-to-real, holdout synthétique) ≈ très faible\n"
            "  • RMSE (sim-to-real, données réelles) → peut être élevé\n"
            "    si la simulation (cône idéal) ne capture pas les non-linéarités "
            "    de la surface réelle (bord, rugosité, déformation).\n\n"
            "En robotique, le reality gap est le principal obstacle "
            "au déploiement de politiques apprises en simulation."
        ),
    },
}
