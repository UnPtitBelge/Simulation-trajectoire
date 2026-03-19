"""NavBar — Navigation bar widget for libre mode.

Displays the main question label and four simulation-tab buttons.
Emits signals when the user selects a simulation or clicks the home button.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from utils import stylesheet as _ss
from utils.ui_constants import (
    NAV_H, NAV_HOME_BTN_H, NAV_BTN_H, NAV_BTN_SPACING, NAV_MARGINS,
    NAV_HOME_SPACING, NAV_BTN_FS, NAV_BTN_PAD, NAV_BTN_RADIUS,
    NAV_HOVER_ALPHA, NAV_ACTIVE_ALPHA,
    SIM_COLORS,
)
from utils.ui_strings import NAV_QUESTION, NAV_HOME_BTN, NAV_SIM_LABELS


class LibreNavBar(QWidget):
    """Navigation bar for libre mode: question label and 4 simulation-tab buttons.

    Signals
    -------
    tab_selected(int)
        Emitted with the 0-based simulation index (0 = MCU, 1 = Cône,
        2 = Membrane, 3 = ML) when the user clicks a tab button.
    home_selected()
        Emitted when the user clicks the home (Scénarios) button.
    """

    tab_selected = Signal(int)
    home_selected = Signal()

    _LABELS = NAV_SIM_LABELS
    _COLORS = [SIM_COLORS[k] for k in ["2d_mcu", "3d_cone", "3d_membrane", "ml"]]

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the navigation bar and build all child widgets."""
        super().__init__(parent)
        self.setFixedHeight(NAV_H)
        self.setObjectName("libreNavBar")
        self._btns: list[QPushButton] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*NAV_MARGINS)
        layout.setSpacing(0)

        home_btn = QPushButton(NAV_HOME_BTN)
        home_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        home_btn.setFixedHeight(NAV_HOME_BTN_H)
        home_btn.clicked.connect(self.home_selected.emit)
        home_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {_ss.CLR_ACCENT}; "
            f"border: 1px solid {_ss.CLR_ACCENT}; border-radius: {NAV_BTN_RADIUS}px; "
            f"font-size: {NAV_BTN_FS}px; font-weight: 700; padding: {NAV_BTN_PAD}; min-width: 0; }}"
            f"QPushButton:hover {{ background: {_ss.CLR_ACCENT_LIGHT}; }}"
        )
        layout.addWidget(home_btn)
        layout.addSpacing(NAV_HOME_SPACING)

        question = QLabel(NAV_QUESTION)
        question.setObjectName("libreNavTitle")
        layout.addWidget(question)
        layout.addStretch()

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        bc = QHBoxLayout(btn_container)
        bc.setContentsMargins(0, 0, 0, 0)
        bc.setSpacing(NAV_BTN_SPACING)

        for i, (label, color) in enumerate(zip(self._LABELS, self._COLORS)):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setFixedHeight(NAV_BTN_H)
            btn.clicked.connect(lambda checked, idx=i: self.tab_selected.emit(idx))
            self._btns.append(btn)
            bc.addWidget(btn)

        layout.addWidget(btn_container)
        self._refresh_styles(0)

    def set_active(self, idx: int) -> None:
        """Highlight the button at *idx*, or clear all highlights if idx < 0.

        Parameters
        ----------
        idx : int
            0-based button index to activate.  Pass ``-1`` to deactivate all
            buttons (used when the landing page is visible, i.e. no simulation
            is currently active).
        """
        for btn in self._btns:
            btn.setChecked(False)
        if 0 <= idx < len(self._btns):
            self._btns[idx].setChecked(True)
        self._refresh_styles(idx)

    def _refresh_styles(self, active: int) -> None:
        """Reapply stylesheets based on which button is currently checked.

        Parameters
        ----------
        active : int
            Index of the active button (used only to satisfy the signature;
            the actual check state is read from ``btn.isChecked()``).
        """
        for i, (btn, color) in enumerate(zip(self._btns, self._COLORS)):
            if btn.isChecked():
                btn.setStyleSheet(
                    f"QPushButton {{ background: {color}{NAV_ACTIVE_ALPHA}; color: {color}; "
                    f"border: 1px solid {color}; border-radius: {NAV_BTN_RADIUS}px; "
                    f"font-size: {NAV_BTN_FS}px; font-weight: 700; padding: {NAV_BTN_PAD}; min-width: 0; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {_ss.CLR_DIM}; "
                    f"border: 1px solid {_ss.CLR_BORDER}; border-radius: {NAV_BTN_RADIUS}px; "
                    f"font-size: {NAV_BTN_FS}px; padding: {NAV_BTN_PAD}; min-width: 0; }}"
                    f"QPushButton:hover {{ color: {color}; border-color: {color}{NAV_HOVER_ALPHA}; }}"
                )
