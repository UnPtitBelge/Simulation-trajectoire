"""Reusable UI builder helpers shared across dashboard and scenario views."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton


def build_preset_buttons(plot, row: QHBoxLayout) -> None:
    """Add F1/F2/F3 preset buttons for *plot* into *row*.

    Uses plot.get_presets() (Loi de Déméter) instead of navigating
    through plot.params internals.
    """
    row.addWidget(QLabel("Préréglages :"))
    for i, (_key, preset) in enumerate(plot.get_presets().items()):
        b = QPushButton(f"F{i + 1}: {preset['label']}")
        b.setProperty("secondary", True)
        b.clicked.connect(lambda _, idx=i: plot.apply_preset(idx))
        row.addWidget(b)
