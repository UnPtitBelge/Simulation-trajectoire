"""MCU presets — 3 configurations par défaut.

F1 — vitesse lente   : orbite standard, ω faible
F2 — vitesse rapide  : même rayon, ω élevé
F3 — rayon étendu    : même vitesse que F1 mais rayon grand (proche du bord)
"""

MCU_PRESETS: dict[str, dict] = {
    "pres_lente": {
        "R": 10.0,
        "omega": 1.0,
        "drag": 0.0,
        "label": "Vitesse lente",
    },
    "pres_rapide": {
        "R": 10.0,
        "omega": 3.0,
        "drag": 0.0,
        "label": "Vitesse rapide",
    },
    "pres_bord": {
        "R": 18.0,
        "omega": 1.0,
        "drag": 0.0,
        "label": "Rayon étendu (proche du bord)",
    },
}
