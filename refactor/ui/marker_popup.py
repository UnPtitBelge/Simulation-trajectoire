"""Dialogue pour ajouter un marqueur visuel (position de référence).

Déclenché par la touche P dans n'importe quelle vue de simulation.
Émet marker_added(r, theta) quand l'utilisateur valide.
"""

import math

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel,
)


class MarkerPopup(QDialog):
    marker_added = Signal(float, float)  # r, theta

    def __init__(self, r_max: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un marqueur")
        self.setFixedWidth(280)

        layout = QFormLayout(self)
        layout.addRow(QLabel("Position de référence (coordonnées polaires)"))

        self._spin_r = QDoubleSpinBox()
        self._spin_r.setRange(0.0, r_max)
        self._spin_r.setSingleStep(0.01)
        self._spin_r.setDecimals(3)
        self._spin_r.setSuffix(" m")

        self._spin_theta = QDoubleSpinBox()
        self._spin_theta.setRange(0.0, 2 * math.pi)
        self._spin_theta.setSingleStep(0.1)
        self._spin_theta.setDecimals(3)
        self._spin_theta.setSuffix(" rad")

        layout.addRow("r :", self._spin_r)
        layout.addRow("θ :", self._spin_theta)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self):
        self.marker_added.emit(self._spin_r.value(), self._spin_theta.value())
        self.accept()
