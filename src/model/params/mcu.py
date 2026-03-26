"""MCU presentation presets — 3 visually striking configurations for classroom demos."""

MCU_PRESENTATION_PRESETS: dict[str, dict] = {
    "demo_orbite": {
        "R": 8.0,
        "omega": 1.5,
        "drag": 0.0,
        "label": "Orbite parfaite (MCU pur)",
    },
    "demo_spirale": {
        "R": 10.0,
        "omega": 1.0,
        "drag": 0.25,
        "label": "Spirale amortie",
    },
    "demo_turbine": {
        "R": 5.0,
        "omega": 5.0,
        "drag": 0.0,
        "label": "Rotation rapide",
    },
}
