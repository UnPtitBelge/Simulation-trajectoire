from PySide6.QtCore import Qt

PRESENTATION_KEYS = {
    "sim_1": Qt.Key.Key_1,
    "sim_2": Qt.Key.Key_2,
    "sim_3": Qt.Key.Key_3,
    "sim_4": Qt.Key.Key_4,
    "play_pause": Qt.Key.Key_Space,
    "reset": Qt.Key.Key_R,
    "preset_1": Qt.Key.Key_F1,
    "preset_2": Qt.Key.Key_F2,
    "preset_3": Qt.Key.Key_F3,
    "next": Qt.Key.Key_Right,
    "prev": Qt.Key.Key_Left,
    "mark": Qt.Key.Key_M,
    "clear_markers": Qt.Key.Key_Delete,
    "quit": Qt.Key.Key_Escape,
}

SHORTCUT_LABELS = [
    ("1–4", "Changer de simulation"),
    ("← →", "Simulation précédente / suivante"),
    ("Espace", "Lecture / Pause"),
    ("R", "Réinitialiser"),
    ("F1–F3", "Conditions initiales prédéfinies"),
    ("Échap", "Quitter / Retour"),
]
