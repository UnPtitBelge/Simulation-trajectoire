"""ML presentation presets — 3 configurations pour la présentation.

Les presets correspondent aux mêmes scénarios que les modèles à équations :
F1 — CI standard      : trajectoire de référence (test_ic 0)
F2 — CI dynamique     : trajectoire avec dynamique différente (test_ic 1)
F3 — hors distribution: conditions initiales inconnues du modèle (test_ic 2)

n_train = 15 pour tous (dataset complet — la variation vient des CI de test).
"""

ML_PRESENTATION_PRESETS: dict[str, dict] = {
    "pres_standard": {
        "n_train": 15,
        "test_ic": 0,
        "label": "CI standard",
    },
    "pres_dynamique": {
        "n_train": 15,
        "test_ic": 1,
        "label": "CI trajectoire 17",
    },
    "pres_bord": {
        "n_train": 15,
        "test_ic": 2,
        "label": "Hors distribution",
    },
}
