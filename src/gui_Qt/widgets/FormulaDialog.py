"""FormulaDialog — Popup dialog showing formula term definitions.

Opened when the user clicks the equation box in LibreInfoStrip.
Displays each formula line with a table of variable → description mappings.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from utils import stylesheet as _ss
from utils.ui_constants import (
    FORMULA_DLG_MIN_W,
    FORMULA_DLG_MIN_H,
    FORMULA_DLG_SPACING,
    FORMULA_DLG_MARGINS,
    FORMULA_DLG_FS,
)
from utils.ui_strings import FORMULA_POPUP_TITLE, FORMULA_CLOSE_BTN


class FormulaDialog(QDialog):
    """Modal popup displaying a formula with term-by-term definitions.

    Parameters
    ----------
    formula_details : list[dict]
        Each dict has keys:
        - ``formula`` (str) — the formula string to display
        - ``terms``   (list[tuple[str,str,str]]) — (symbol, label, description)
    accent : str
        Hex colour for the formula text and accent bar (per-simulation colour).
    parent : QWidget | None
        Parent widget (for positioning).
    """

    def __init__(
        self,
        formula_details: list[dict],
        accent: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(FORMULA_POPUP_TITLE)
        self.setModal(True)
        self.setMinimumSize(FORMULA_DLG_MIN_W, FORMULA_DLG_MIN_H)
        self.setStyleSheet(
            f"QDialog {{ background-color: {_ss.CLR_BASE}; color: {_ss.CLR_TEXT}; }}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(*FORMULA_DLG_MARGINS)
        root.setSpacing(FORMULA_DLG_SPACING)

        # Title
        title = QLabel(FORMULA_POPUP_TITLE)
        title.setStyleSheet(
            f"color: {accent}; font-size: {FORMULA_DLG_FS + 4}px; font-weight: 800; background: transparent;"
        )
        root.addWidget(title)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(FORMULA_DLG_SPACING * 2)
        content_lay.setContentsMargins(0, 0, 0, 0)

        for entry in formula_details:
            content_lay.addWidget(self._build_entry(entry, accent))

        content_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # Close button
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {_ss.CLR_BORDER}; border: none; max-height: 1px;")
        root.addWidget(sep)

        close_btn = QPushButton(FORMULA_CLOSE_BTN)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: {_ss.CLR_SURFACE0}; color: {_ss.CLR_TEXT}; "
            f"border: 1px solid {_ss.CLR_BORDER}; border-radius: 6px; padding: 6px 24px; "
            f"font-size: {FORMULA_DLG_FS}px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {_ss.CLR_SURFACE1}; border-color: {accent}; color: {accent}; }}"
        )
        close_btn.clicked.connect(self.accept)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_row.addWidget(close_btn)
        root.addLayout(close_row)

    def _build_entry(self, entry: dict, accent: str) -> QWidget:
        """Build one formula block: coloured formula string + terms table."""
        block = QWidget()
        block.setStyleSheet(
            f"QWidget {{ background: {_ss.CLR_SURFACE0}; border-radius: 8px; "
            f"border: 1px solid {_ss.CLR_BORDER}; }}"
        )
        lay = QVBoxLayout(block)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        # Formula line
        formula_lbl = QLabel(entry["formula"])
        formula_lbl.setFont(QFont("Monospace", FORMULA_DLG_FS))
        formula_lbl.setStyleSheet(
            f"color: {accent}; font-weight: bold; background: transparent; border: none;"
        )
        formula_lbl.setWordWrap(True)
        lay.addWidget(formula_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            f"background: {_ss.CLR_BORDER}; border: none; max-height: 1px;"
        )
        lay.addWidget(sep)

        # Terms rows
        for symbol, label, description in entry.get("terms", []):
            row = QWidget()
            row.setStyleSheet("background: transparent; border: none;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 2, 0, 2)
            rl.setSpacing(10)

            sym_lbl = QLabel(symbol)
            sym_lbl.setFont(QFont("Monospace", FORMULA_DLG_FS - 1))
            sym_lbl.setStyleSheet(
                f"color: {accent}cc; font-weight: bold; background: transparent; border: none;"
            )
            sym_lbl.setFixedWidth(60)
            sym_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rl.addWidget(sym_lbl)

            arrow = QLabel("→")
            arrow.setStyleSheet(f"color: {_ss.CLR_DIM}; background: transparent; border: none;")
            rl.addWidget(arrow)

            lab_lbl = QLabel(f"<b>{label}</b>")
            lab_lbl.setStyleSheet(
                f"color: {_ss.CLR_TEXT}; font-size: {FORMULA_DLG_FS - 1}px; background: transparent; border: none;"
            )
            lab_lbl.setFixedWidth(160)
            lab_lbl.setWordWrap(True)
            rl.addWidget(lab_lbl)

            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(
                f"color: {_ss.CLR_SUBTEXT}; font-size: {FORMULA_DLG_FS - 2}px; background: transparent; border: none;"
            )
            desc_lbl.setWordWrap(True)
            desc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            rl.addWidget(desc_lbl, stretch=1)

            lay.addWidget(row)

        return block
