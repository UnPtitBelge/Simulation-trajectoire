"""MetricsPanel — bande de métriques temps réel sous la simulation.

Chaque simulation expose get_metrics_schema() + get_frame_metrics(i).
MetricsPanel s'abonne au signal frame_updated du Plot et rafraîchit
les cartes (_MetricCard) à chaque tick sans aucun calcul supplémentaire.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.utils.theme import (
    CLR_BORDER,
    CLR_PRIMARY,
    CLR_SURFACE,
    CLR_TEXT_SECONDARY,
    FS_METRIC,
    FS_XS,
    METRIC_CARD_H,
)


class _MetricCard(QFrame):
    """Carte affichant une valeur numérique + unité + libellé."""

    def __init__(self, label: str, unit: str = "", color: str = CLR_PRIMARY, parent=None):
        super().__init__(parent)
        self._fmt = ".3f"
        self.setStyleSheet(
            f"QFrame {{ background: {CLR_SURFACE}; border: 1px solid {CLR_BORDER}; "
            f"border-radius: 8px; }}"
        )
        self.setFixedHeight(METRIC_CARD_H)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(1)

        self._val_lbl = QLabel("—")
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val_lbl.setStyleSheet(
            f"font-size: {FS_METRIC}; font-weight: 600; color: {color};"
        )
        lay.addWidget(self._val_lbl)

        suffix = f" ({unit})" if unit else ""
        caption = QLabel(f"{label}{suffix}")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption.setStyleSheet(
            f"font-size: {FS_XS}; color: {CLR_TEXT_SECONDARY};"
        )
        lay.addWidget(caption)

    def set_value(self, val: float, fmt: str = ".3f") -> None:
        try:
            if fmt == ".0f" or fmt == "d":
                text = str(int(round(val)))
            else:
                text = format(val, fmt)
        except (ValueError, TypeError):
            text = "—"
        self._val_lbl.setText(text)


class MetricsPanel(QWidget):
    """Bande horizontale de _MetricCard mis à jour à chaque frame.

    Usage :
        panel = MetricsPanel(plot)
        layout.addWidget(panel)

    Si la simulation ne fournit pas de schéma (get_metrics_schema() → []),
    le widget se cache automatiquement.
    """

    def __init__(self, plot, parent=None):
        super().__init__(parent)
        self._plot = plot
        self._cards: dict[str, tuple["_MetricCard", str]] = {}

        schema = plot.get_metrics_schema()
        if not schema:
            self.hide()
            return

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(6)

        for entry in schema:
            card = _MetricCard(
                entry.get("label", entry["key"]),
                entry.get("unit", ""),
                entry.get("color", CLR_PRIMARY),
            )
            outer.addWidget(card, stretch=1)
            self._cards[entry["key"]] = (card, entry.get("fmt", ".3f"))

        plot.frame_updated.connect(self._on_frame)

    def _on_frame(self, i: int) -> None:
        if not self._cards:
            return
        metrics = self._plot.get_frame_metrics(i)
        for key, (card, fmt) in self._cards.items():
            if key in metrics:
                card.set_value(metrics[key], fmt)
