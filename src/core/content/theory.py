"""Theory content — 13 chapters aligned with the fiche théorique.

Each key matches a Chapter.theory_key in chapters.py.
Structure preserved: {title, icon, sections: [{subtitle, text}]}.
Tone: educational but accessible, playful where appropriate.
"""

THEORY: dict[str, dict] = {
    # ── Ch.1 — Modèle ───────────────────────────────────────────────────────
    "modele": {
        "title": "1. Qu'est-ce qu'un modèle ?",
        "icon": "?",
        "sections": [
            {
                "subtitle": "Définition",
                "text": (
                    "Un modèle est une représentation simplifiée d'un système réel, "
                    "traduite en équations, règles et paramètres pour qu'un ordinateur "
                    "puisse la manipuler.\n\n"
                    "Pensez-y comme une carte routière : elle ne montre pas chaque "
                    "caillou, mais elle vous amène à destination. Un modèle n'est "
                    "jamais la réalité — c'est une carte, pas le territoire."
                ),
            },
            {
                "subtitle": "Les ingrédients d'un modèle",
                "text": (
                    "Tout modèle repose sur :\n"
                    "• Des hypothèses (ce qu'on garde et ce qu'on ignore)\n"
                    "• Des équations qui relient les grandeurs\n"
                    "• Des paramètres à mesurer ou estimer\n"
                    "• Un domaine de validité (où le modèle est fiable)\n\n"
                    "Exemple : le MCU suppose que la bille tourne en cercle "
                    "à vitesse constante. Simple ? Oui. Utile ? Ça dépend de la question !"
                ),
            },
            {
                "subtitle": "Mécaniste vs empirique",
                "text": (
                    "Modèle mécaniste : fondé sur des lois physiques (Newton, Laplace…). "
                    "On comprend pourquoi il fonctionne.\n\n"
                    "Modèle empirique : fondé sur des données observées. Il prédit, "
                    "mais ne nous dit pas forcément pourquoi (régressions, réseaux de neurones…).\n\n"
                    "Dans cette app, on explore les deux : physique (cône, membrane) "
                    "et données (ML)."
                ),
            },
            {
                "subtitle": "Cycle de vie d'un modèle",
                "text": (
                    "1. Observer le phénomène réel\n"
                    "2. Formaliser en maths (choisir les hypothèses)\n"
                    "3. Implémenter en code\n"
                    "4. Valider par comparaison avec l'expérience\n"
                    "5. Raffiner ou rejeter le modèle\n\n"
                    "Ce cycle ne s'arrête jamais vraiment — un modèle est toujours "
                    "perfectible."
                ),
            },
        ],
    },

    # ── Ch.2 — Simulation ────────────────────────────────────────────────────
    "simulation": {
        "title": "2. Qu'est-ce qu'une simulation ?",
        "icon": "▶",
        "sections": [
            {
                "subtitle": "Définition",
                "text": (
                    "Simuler, c'est faire tourner un modèle dans le temps sur un "
                    "ordinateur pour observer le comportement prédit — sans avoir "
                    "à réaliser l'expérience en vrai.\n\n"
                    "On avance pas à pas (chaque Δt) et on calcule l'état suivant "
                    "à partir de l'état actuel."
                ),
            },
            {
                "subtitle": "Temps continu → temps discret",
                "text": (
                    "La physique est continue : le monde évolue sans interruption.\n"
                    "L'ordinateur est discret : il ne connaît que des instants séparés.\n\n"
                    "On découpe le temps en petits pas Δt et on approxime l'évolution "
                    "continue. Plus Δt est petit, plus c'est précis — mais plus c'est "
                    "coûteux en calculs."
                ),
            },
            {
                "subtitle": "Pourquoi simuler ?",
                "text": (
                    "• Tester des scénarios dangereux ou coûteux (crash-tests, satellites)\n"
                    "• Comprendre des systèmes trop complexes pour une solution exacte\n"
                    "• Prédire le futur à partir de l'état présent\n"
                    "• Optimiser des paramètres (meilleur angle de tir !)\n\n"
                    "La simulation est l'outil quotidien des ingénieurs, physiciens, "
                    "biologistes, économistes…"
                ),
            },
            {
                "subtitle": "Limites fondamentales",
                "text": (
                    "• La simulation n'est jamais plus vraie que le modèle\n"
                    "• Des erreurs numériques s'accumulent à chaque pas\n"
                    "• Un modèle valide dans un régime peut être faux dans un autre\n\n"
                    "C'est pour ça qu'on valide toujours avec des données réelles !"
                ),
            },
        ],
    },

    # ── Ch.3 — MCU ───────────────────────────────────────────────────────────
    "mcu": {
        "title": "3. Le MCU — un premier modèle",
        "icon": "○",
        "sections": [
            {
                "subtitle": "Hypothèses",
                "text": (
                    "Le Mouvement Circulaire Uniforme est le modèle le plus simple :\n"
                    "• La bille se déplace sur un cercle de rayon R constant\n"
                    "• Sa vitesse ‖v‖ est constante (pas de frottement)\n"
                    "• Seule l'accélération centripète a = v²/R existe\n\n"
                    "C'est un modèle « jouet » — il n'est pas réaliste, mais il "
                    "illustre parfaitement ce que signifie modéliser."
                ),
            },
            {
                "subtitle": "Équations",
                "text": (
                    "x(t) = R · cos(ω·t + φ₀)\n"
                    "y(t) = R · sin(ω·t + φ₀)\n"
                    "ω = v / R    (vitesse angulaire, rad/s)\n"
                    "a = ω²·R = v²/R    (accélération centripète)\n\n"
                    "C'est analytiquement exact : pas d'erreur numérique, "
                    "pas de Δt, pas d'approximation."
                ),
            },
            {
                "subtitle": "Ce que ce modèle fait bien… et mal",
                "text": (
                    "Points forts : exact, simple, zéro erreur.\n"
                    "Limites : il impose une trajectoire circulaire. Si la bille "
                    "ralentit ou si la surface n'est pas plate, ce modèle est faux.\n\n"
                    "Le MCU est un modèle prescriptif : on dicte la trajectoire.\n"
                    "Les modèles Newton et Laplace sont prédictifs : on donne les "
                    "forces et le mouvement émerge. C'est la différence fondamentale."
                ),
            },
        ],
    },

    # ── Ch.4 — Newton / Cône ─────────────────────────────────────────────────
    "newton_cone": {
        "title": "4. Newton — trajectoire sur un cône",
        "icon": "△",
        "sections": [
            {
                "subtitle": "Géométrie et forces",
                "text": (
                    "Le cône a une pente constante α. Trois forces agissent :\n"
                    "• Poids centripète : F_r = m·g·sin(α) — attire vers le centre\n"
                    "• Frottement de Coulomb : F_f = μ·N, opposé à la vitesse\n"
                    "• Force normale : N = m·g·cos(α)\n\n"
                    "Le frottement de Coulomb est sec : il s'oppose au glissement "
                    "avec une force constante (pas proportionnelle à la vitesse)."
                ),
            },
            {
                "subtitle": "Équations du mouvement (polaires)",
                "text": (
                    "r̈ − r·θ̇² = −g·sin(α) − μ·g·cos(α)·ṙ/‖v‖\n"
                    "r·θ̈ + 2·ṙ·θ̇ = −μ·g·cos(α)·(r·θ̇)/‖v‖\n"
                    "‖v‖ = √(ṙ² + r²·θ̇²)\n\n"
                    "Ces équations sont non-linéaires (à cause du terme ṙ/‖v‖). "
                    "Pas de solution analytique → on doit simuler."
                ),
            },
            {
                "subtitle": "Comportement attendu",
                "text": (
                    "• Sans frottement : spirale conservant le moment cinétique\n"
                    "• Avec frottement : spirale serrée vers le centre\n"
                    "• Précession : les orbites tournent ~151° entre deux passages "
                    "au même rayon\n\n"
                    "Le frottement de Coulomb est discontinu en v=0 (la bille "
                    "s'arrête net). Cette non-linéarité est un défi pour l'intégrateur."
                ),
            },
        ],
    },

    # ── Ch.5 — Laplace / Membrane ────────────────────────────────────────────
    "laplace_membrane": {
        "title": "5. Laplace — membrane élastique",
        "icon": "◎",
        "sections": [
            {
                "subtitle": "Forme de la membrane",
                "text": (
                    "Sous charge ponctuelle au centre, la membrane satisfait "
                    "l'équation de Laplace : ∇²z = 0 (hors du point de charge).\n\n"
                    "Solution : z(r) = −A·ln(R/r)\n"
                    "où A = F/(2πT), F = force, T = tension de la membrane.\n\n"
                    "Contrairement au cône (z ∝ r), la membrane logarithmique est "
                    "plus plate au centre et plus raide en périphérie."
                ),
            },
            {
                "subtitle": "Force centripète effective",
                "text": (
                    "La pente locale vaut dz/dr = A/r.\n"
                    "La force centripète : F_r = −m·g·A/r\n\n"
                    "Plus on est loin du centre, plus la force est faible. "
                    "C'est l'inverse du cône où la force est constante !"
                ),
            },
            {
                "subtitle": "Comparaison cône / membrane",
                "text": (
                    "Cône : pente constante → force constante → trajectoire régulière\n"
                    "Membrane : pente ∝ 1/r → force variable → dynamique plus riche\n\n"
                    "Résultat expérimental : notre surface réelle se comporte comme "
                    "un cône (pente quasi-constante). Le modèle de Newton est donc "
                    "plus fidèle à la réalité que le modèle de Laplace, malgré sa "
                    "moindre sophistication mathématique."
                ),
            },
        ],
    },

    # ── Ch.6 — Intégration numérique ─────────────────────────────────────────
    "integration": {
        "title": "6. Intégration numérique",
        "icon": "∫",
        "sections": [
            {
                "subtitle": "Le problème",
                "text": (
                    "Les équations de Newton et Laplace sont des EDO. Leur solution "
                    "analytique n'existe généralement pas → on avance pas à pas.\n\n"
                    "À chaque pas Δt, on calcule la nouvelle position et vitesse "
                    "à partir des forces. Mais comment, exactement ?"
                ),
            },
            {
                "subtitle": "Euler semi-implicite (ordre 1)",
                "text": (
                    "v(t+Δt) = v(t) + a(t)·Δt    (vitesse d'abord)\n"
                    "x(t+Δt) = x(t) + v(t+Δt)·Δt  (puis position avec la NOUVELLE vitesse)\n\n"
                    "Simple à coder, mais erreur O(Δt) par pas. L'énergie peut "
                    "dériver — la trajectoire s'éloigne lentement de la vraie."
                ),
            },
            {
                "subtitle": "Verlet / Störmer-Verlet (ordre 2, symplectique)",
                "text": (
                    "x(t+Δt) = x(t) + v(t)·Δt + ½·a(t)·Δt²\n"
                    "a(t+Δt) = forces(x(t+Δt))    (recalcul)\n"
                    "v(t+Δt) = v(t) + ½·[a(t) + a(t+Δt)]·Δt\n\n"
                    "Erreur O(Δt²) — deux fois plus précis qu'Euler pour le même Δt. "
                    "Symplectique = conserve l'énergie à long terme. "
                    "Recommandé pour notre expérience."
                ),
            },
            {
                "subtitle": "RK4 — Runge-Kutta (ordre 4)",
                "text": (
                    "Évalue l'accélération 4 fois par pas (k₁…k₄) et fait "
                    "une moyenne pondérée. Erreur O(Δt⁴) — très précis.\n\n"
                    "Coûte 4× plus de calcul par pas. Pas symplectique, mais "
                    "excellent pour les trajectoires courtes."
                ),
            },
            {
                "subtitle": "Comparaison",
                "text": (
                    "Euler : rapide, imprécis, énergie dérive\n"
                    "Verlet : bon compromis, conserve l'énergie\n"
                    "RK4 : ultra-précis, plus coûteux\n\n"
                    "Activez la superposition des 3 intégrateurs sur le cône "
                    "pour voir la différence en temps réel !"
                ),
            },
        ],
    },

    # ── Ch.7 — Bon modèle ────────────────────────────────────────────────────
    "bon_modele": {
        "title": "7. Qu'est-ce qu'un bon modèle ?",
        "icon": "✓",
        "sections": [
            {
                "subtitle": "Les critères",
                "text": (
                    "Un bon modèle est :\n"
                    "• Prédictif : il prédit des données qu'il n'a pas vues\n"
                    "• Parcimonieux (Rasoir d'Occam) : le plus simple qui explique les données\n"
                    "• Interprétable : on comprend pourquoi il fonctionne\n"
                    "• Robuste : stable quand les conditions varient un peu\n"
                    "• Validable : on peut le tester et le réfuter"
                ),
            },
            {
                "subtitle": "Retour sur nos modèles",
                "text": (
                    "MCU : trop simple (prescriptif), mais utile comme référence.\n"
                    "Cône/Newton : meilleur modèle pour notre expérience — pente constante = hypothèse valide.\n"
                    "Membrane/Laplace : plus complexe, mais moins fidèle à notre surface réelle.\n"
                    "ML : complémentaire si on a beaucoup de données."
                ),
            },
            {
                "subtitle": "Sous-ajustement et sur-ajustement",
                "text": (
                    "Sous-ajustement (underfitting) : le modèle est trop simple — "
                    "il ne capture pas la dynamique réelle. Ex : le MCU qui ignore "
                    "le frottement.\n\n"
                    "Sur-ajustement (overfitting) : le modèle colle parfaitement "
                    "aux données mais ne généralise pas. Ex : un polynôme de degré 20 "
                    "passant par chaque point de mesure. Il a appris le bruit, pas "
                    "le phénomène.\n\n"
                    "Le bon modèle est celui qui généralise à de nouvelles expériences."
                ),
            },
        ],
    },

    # ── Ch.8 — Machine Learning ──────────────────────────────────────────────
    "machine_learning": {
        "title": "8. Machine Learning",
        "icon": "🧠",
        "sections": [
            {
                "subtitle": "Principe",
                "text": (
                    "Au lieu de dériver les équations depuis la physique, on laisse "
                    "l'algorithme apprendre les relations directement depuis les "
                    "données observées.\n\n"
                    "On lui donne des paires (entrée, sortie) et il trouve la "
                    "fonction qui les relie le mieux."
                ),
            },
            {
                "subtitle": "Avantages",
                "text": (
                    "• Capture des effets non modélisés (vibrations, irrégularités)\n"
                    "• S'améliore avec plus de données\n"
                    "• Gère des surfaces arbitraires sans hypothèse géométrique"
                ),
            },
            {
                "subtitle": "Inconvénients",
                "text": (
                    "• Boîte noire : difficile d'interpréter pourquoi cette prédiction\n"
                    "• Nécessite beaucoup de données\n"
                    "• Peut échouer hors distribution d'entraînement\n"
                    "• Ne respecte pas forcément les lois de conservation (énergie, moment)"
                ),
            },
        ],
    },

    # ── Ch.9 — RL vs MLP ─────────────────────────────────────────────────────
    "rl_vs_mlp": {
        "title": "9. Régression linéaire vs MLP",
        "icon": "⚖",
        "sections": [
            {
                "subtitle": "Régression linéaire",
                "text": (
                    "Le modèle ML le plus simple : ŷ = w₀ + w₁·x₁ + … + wₙ·xₙ\n\n"
                    "On minimise l'erreur quadratique moyenne (MSE) sur les données.\n"
                    "Simple, rapide, interprétable — mais ne capture que des "
                    "relations linéaires."
                ),
            },
            {
                "subtitle": "Le Perceptron Multicouche (MLP)",
                "text": (
                    "Un réseau de neurones empilant des couches avec des fonctions "
                    "d'activation non-linéaires (ReLU, tanh…).\n\n"
                    "h = σ(W·x + b)    (couche cachée)\n"
                    "ŷ = W_out · h + b_out    (sortie)\n\n"
                    "Théorème d'approximation universelle : un MLP suffisamment "
                    "large peut approcher n'importe quelle fonction continue."
                ),
            },
            {
                "subtitle": "Comparaison dans notre contexte",
                "text": (
                    "Les équations du cône contiennent x/√(x²+y²) — un terme "
                    "fondamentalement non-linéaire. La régression linéaire ne peut "
                    "pas le capturer.\n\n"
                    "Le MLP, avec ses couches non-linéaires, peut apprendre cette "
                    "relation… mais il lui faut beaucoup de données.\n\n"
                    "Avec 15 trajectoires : RL ≈ MLP (trop peu de données).\n"
                    "Avec 10 000+ trajectoires synthétiques : MLP >> RL."
                ),
            },
        ],
    },

    # ── Ch.10 — Limites de la simulation ─────────────────────────────────────
    "limites_simulation": {
        "title": "10. Les limitations de la simulation",
        "icon": "⚠",
        "sections": [
            {
                "subtitle": "Limitations physiques",
                "text": (
                    "• Hypothèses simplificatrices : chaque modèle ignore des phénomènes "
                    "(chaleur, vibrations, imperfections de la bille)\n"
                    "• Conditions aux limites : que se passe-t-il au bord ?\n"
                    "• Non-linéarités et chaos : une infime différence dans les CI "
                    "→ trajectoires radicalement différentes"
                ),
            },
            {
                "subtitle": "Limitations computationnelles",
                "text": (
                    "• Diviser Δt par 2 = doubler le nombre de calculs\n"
                    "• Compromis précision / vitesse\n"
                    "• N billes en interaction → O(N²) : ça explose !\n\n"
                    "C'est pour ça qu'on choisit le Δt le plus grand "
                    "qui donne encore une précision acceptable."
                ),
            },
            {
                "subtitle": "Manque de données",
                "text": (
                    "• Les paramètres (μ, γ, A…) doivent être mesurés — "
                    "une mauvaise estimation fausse tout\n"
                    "• Sans données expérimentales de validation, on ne sait pas "
                    "si le modèle est bon"
                ),
            },
        ],
    },

    # ── Ch.11 — Erreurs numériques ───────────────────────────────────────────
    "erreurs_numeriques": {
        "title": "11. Les erreurs numériques",
        "icon": "≈",
        "sections": [
            {
                "subtitle": "Erreur de troncature",
                "text": (
                    "Quand on discrétise une dérivée, on « tronque » le développement :\n"
                    "f(t+Δt) = f(t) + f'(t)·Δt + O(Δt²)\n\n"
                    "Le O(Δt²) qu'on ignore est l'erreur de troncature.\n"
                    "Euler : O(Δt). Verlet : O(Δt²). RK4 : O(Δt⁴)."
                ),
            },
            {
                "subtitle": "Erreur d'arrondi",
                "text": (
                    "Les floats ont ~15 chiffres significatifs en double précision. "
                    "Chaque opération ajoute une petite erreur.\n\n"
                    "Paradoxe : réduire Δt à l'extrême augmente le nombre d'opérations "
                    "→ plus d'erreurs d'arrondi qui finissent par dominer !"
                ),
            },
            {
                "subtitle": "Instabilité numérique",
                "text": (
                    "Certains intégrateurs divergent si Δt est trop grand : "
                    "les erreurs s'amplifient à chaque pas.\n\n"
                    "Condition de stabilité d'Euler : Δt < 2/ω_max\n"
                    "Verlet est naturellement plus stable (symplectique)."
                ),
            },
            {
                "subtitle": "Bonne pratique : convergence",
                "text": (
                    "1. Simuler avec un Δt donné\n"
                    "2. Diviser Δt par 2 et re-simuler\n"
                    "3. Si la différence est négligeable → solution convergée\n\n"
                    "Simple, efficace, et ça marche pour n'importe quel intégrateur."
                ),
            },
        ],
    },

    # ── Ch.12 — Erreurs humaines ─────────────────────────────────────────────
    "erreurs_humaines": {
        "title": "12. Les erreurs humaines et de mesure",
        "icon": "👤",
        "sections": [
            {
                "subtitle": "Erreurs de mesure",
                "text": (
                    "• Biais systématique : capteur mal étalonné → décalage constant\n"
                    "• Bruit aléatoire : vibrations, résolution limitée de la caméra\n"
                    "• Erreur sur les CI : si on mesure mal (x₀, y₀, vx₀, vy₀), "
                    "toute la trajectoire sera décalée\n\n"
                    "Propagation : δy = |∂y/∂x| · δx — l'erreur s'amplifie !"
                ),
            },
            {
                "subtitle": "Erreurs de modélisation",
                "text": (
                    "• Mauvais choix de modèle (MCU quand la physique impose Laplace)\n"
                    "• Mauvaise estimation des paramètres (sous-estimer μ → trop rapide)\n"
                    "• Bug dans le code (un signe − manquant = force inversée !)\n"
                    "• Validation insuffisante (tester sur les données d'entraînement)"
                ),
            },
            {
                "subtitle": "Le workflow scientifique rigoureux",
                "text": (
                    "1. Séparer les données en train / test\n"
                    "2. Valider sur des conditions différentes\n"
                    "3. Quantifier l'incertitude sur chaque paramètre\n"
                    "4. Vérifier les limites physiques (conservation d'énergie)\n"
                    "5. Documenter toutes les hypothèses\n\n"
                    "La rigueur ne garantit pas la vérité, mais elle garantit "
                    "qu'on peut retracer nos erreurs."
                ),
            },
        ],
    },

    # ── Ch.13 — Conclusion ───────────────────────────────────────────────────
    "conclusion": {
        "title": "13. Conclusion",
        "icon": "★",
        "sections": [
            {
                "subtitle": "« All models are wrong, but some are useful »",
                "text": (
                    "— George E. P. Box, statisticien (1919–2013)\n\n"
                    "À travers le voyage de la bille sur la membrane, nous avons "
                    "traversé l'essentiel de la philosophie de la modélisation."
                ),
            },
            {
                "subtitle": "Ce que nous avons appris",
                "text": (
                    "• Un modèle est un choix d'hypothèses, pas une vérité\n"
                    "• La simulation traduit ces hypothèses en calculs\n"
                    "• L'intégrateur numérique introduit ses propres erreurs\n"
                    "• Le ML peut compléter la physique quand on a des données\n"
                    "• Valider, c'est comparer modèle et réalité — pas se contenter "
                    "de résultats qui « ont l'air bien »"
                ),
            },
            {
                "subtitle": "La hiérarchie de nos modèles",
                "text": (
                    "MCU : prescriptif, trop simple — utile comme référence.\n"
                    "Newton + Coulomb (cône) : meilleur modèle pour notre expérience.\n"
                    "Laplace (membrane) : plus complexe, moins fidèle à notre surface réelle.\n"
                    "ML (MLP) : complémentaire avec assez de données — mais opaque."
                ),
            },
            {
                "subtitle": "Le vrai enjeu",
                "text": (
                    "Simuler la réalité par ordinateur, c'est apprendre à poser "
                    "des hypothèses, à les tester, à accepter l'erreur comme partie "
                    "intégrante du processus scientifique.\n\n"
                    "La bille ne fera jamais exactement ce que notre modèle prédit. "
                    "Et c'est précisément cet écart qui est la source la plus riche "
                    "d'apprentissage.\n\n"
                    "Simuler, c'est apprendre à se tromper avec rigueur."
                ),
            },
        ],
    },
}


# ── Glossaire ────────────────────────────────────────────────────────────────

GLOSSARY: dict[str, str] = {
    "modèle": (
        "Représentation simplifiée d'un système réel, traduite en équations "
        "et paramètres. Carte, pas territoire."
    ),
    "simulation": (
        "Exécution pas à pas d'un modèle sur ordinateur pour observer "
        "le comportement prédit du système."
    ),
    "intégration numérique": (
        "Technique pour résoudre des EDO par petits pas Δt. Euler, Verlet "
        "et RK4 sont les trois méthodes de cette app."
    ),
    "Euler semi-implicite": (
        "Intégrateur d'ordre 1 : met à jour la vitesse d'abord, puis la position "
        "avec la nouvelle vitesse. Simple mais peu précis."
    ),
    "Verlet": (
        "Intégrateur d'ordre 2 symplectique : conserve l'énergie sur le long terme. "
        "Recommandé pour les systèmes mécaniques."
    ),
    "RK4": (
        "Runge-Kutta d'ordre 4 : évalue l'accélération 4 fois par pas. "
        "Très précis, mais coûteux."
    ),
    "symplectique": (
        "Un intégrateur qui préserve la structure géométrique de l'espace des phases. "
        "En pratique : l'énergie ne dérive pas à long terme."
    ),
    "frottement de Coulomb": (
        "Frottement sec entre deux surfaces : force constante F = μ·N, "
        "opposée à la vitesse. Discontinu en v=0."
    ),
    "frottement visqueux": (
        "Frottement proportionnel à la vitesse : F = −γ·v. "
        "Modèle fluide, plus doux que Coulomb."
    ),
    "précession": (
        "Rotation progressive du plan de l'orbite. Sur le cône : ~151° "
        "entre deux passages au même rayon."
    ),
    "Laplace": (
        "Équation ∇²z = 0 : décrit la forme d'une membrane élastique "
        "sous charge ponctuelle. Solution : z = −A·ln(R/r)."
    ),
    "singularité": (
        "Point où une grandeur diverge (ex : pente = A/r → ∞ quand r → 0). "
        "Dans le code : clamper r ≥ r_min pour éviter la division par zéro."
    ),
    "régression linéaire": (
        "Modèle ML le plus simple : ŷ = w₀ + w₁·x₁ + … + wₙ·xₙ. "
        "Rapide mais limité aux relations linéaires."
    ),
    "MLP": (
        "Perceptron Multicouche — réseau de neurones à couches cachées. "
        "Peut approximer toute fonction continue (théorème d'approximation universelle)."
    ),
    "R²": (
        "Coefficient de détermination : proportion de la variance expliquée "
        "par le modèle. R² = 1 = parfait, R² = 0 = aussi bon que la moyenne."
    ),
    "RMSE": (
        "Root Mean Squared Error : racine de l'erreur quadratique moyenne. "
        "En unités de la sortie (mètres, pixels…)."
    ),
    "overfitting": (
        "Sur-ajustement : le modèle colle aux données d'entraînement mais "
        "ne généralise pas. Il a appris le bruit."
    ),
    "underfitting": (
        "Sous-ajustement : le modèle est trop simple pour capturer la dynamique. "
        "Ex : MCU sur une membrane."
    ),
    "conditions initiales": (
        "L'état du système au temps t=0 (position, vitesse). Toute la "
        "trajectoire en découle — c'est le Δ qui crée le chaos."
    ),
    "convergence": (
        "La simulation est convergée quand réduire Δt ne change plus le résultat. "
        "Test : diviser Δt par 2 et comparer."
    ),
    "Latin Hypercube": (
        "Technique d'échantillonnage qui garantit une couverture uniforme "
        "de l'espace des paramètres. Utilisée dans sim-to-real."
    ),
}
