"""Panneau de contrôle générique : sélecteur de presets + spinboxes pour les CI.

Construction dynamique depuis le dictionnaire de config TOML.
Les noms de paramètres ne sont pas hardcodés ici.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QLabel,
    QVBoxLayout, QWidget,
)



class ControlsPanel(QWidget):
    """Panneau latéral avec sélecteur preset et spinboxes CI.

    cfg doit contenir :
      - cfg["preset"]  : dict {nom: {param: valeur, ...}}
      - cfg["ranges"]  : dict {param: [min, max]}
    """

    params_changed = Signal(dict)  # émis à chaque modification de valeur

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._presets: dict = cfg.get("preset", {})
        self._ranges:  dict = cfg.get("ranges",  {})
        self._spinboxes: dict[str, QDoubleSpinBox] = {}

        self._vbox = QVBoxLayout(self)
        layout = self._vbox
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Sélecteur de preset ──
        preset_box = QGroupBox("Preset")
        preset_layout = QVBoxLayout(preset_box)
        self._combo = QComboBox()
        for name in self._presets:
            self._combo.addItem(name)
        self._combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self._combo)
        layout.addWidget(preset_box)

        # ── Conditions initiales ──
        ci_box = QGroupBox("Conditions initiales")
        form = QFormLayout(ci_box)
        form.setSpacing(8)

        first_preset = next(iter(self._presets.values()), {})
        for param, value in first_preset.items():
            lo, hi = self._ranges.get(param, [0.0, 1.0])
            spin = QDoubleSpinBox()
            spin.setRange(lo, hi)
            spin.setDecimals(4)
            spin.setSingleStep((hi - lo) / 100)
            spin.setValue(value)
            spin.valueChanged.connect(self._on_value_changed)
            self._spinboxes[param] = spin
            form.addRow(QLabel(param), spin)

        layout.addWidget(ci_box)
        layout.addStretch()

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_preset_changed(self, index: int) -> None:
        name = self._combo.itemText(index)
        values = self._presets.get(name, {})
        for param, spin in self._spinboxes.items():
            if param in values:
                spin.blockSignals(True)
                spin.setValue(values[param])
                spin.blockSignals(False)
        self.params_changed.emit(self.current_params())

    def _on_value_changed(self) -> None:
        self.params_changed.emit(self.current_params())

    # ── API ────────────────────────────────────────────────────────────────────

    def current_params(self) -> dict:
        return {param: spin.value() for param, spin in self._spinboxes.items()}

    def add_extra_widget(self, label: str, widget: QWidget) -> None:
        """Ajoute un widget supplémentaire en bas du panneau (ex. sélecteur contexte ML)."""
        box = QGroupBox(label)
        box_layout = QVBoxLayout(box)
        box_layout.addWidget(widget)
        self._vbox.insertWidget(self._vbox.count() - 1, box)
