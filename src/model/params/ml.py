"""ML presets — 3 configurations par défaut."""

ML_PRESETS: dict[str, dict] = {
    "peu_donnees": {
        "n_train": 3,
        "test_ic": 0,
        "label": "Peu de données",
    },
    "donnees_completes": {
        "n_train": 15,
        "test_ic": 0,
        "label": "Données complètes",
    },
    "hors_distribution": {
        "n_train": 15,
        "test_ic": 2,
        "label": "Hors distribution",
    },
}
