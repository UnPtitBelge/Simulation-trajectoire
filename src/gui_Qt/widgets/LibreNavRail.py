"""Barre de navigation verticale Material Design 3 pour le mode libre.

Rail de navigation MD3 positionné sur le côté gauche de la fenêtre libre.
Affiche un logo, cinq éléments de navigation et un bouton de fermeture.

Architecture MD3
----------------
- Fond blanc, bordure droite fine (outline-variant).
- Chaque item : icône centrée + libellé en dessous.
- Item actif : indicateur en « pilule » (primary container).
- Item inactif : couleur on-surface-variant.
- Bouton exit (✕) ancré en bas.

Classes publiques
-----------------
LibreNavRail
    Rail MD3 : signaux ``page_selected(int)`` et ``exit_requested()``.
"""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from utils import stylesheet as _ss
from utils.ui_constants import (
    MD3_RAIL_W,
    MD3_RAIL_ITEM_H,
    MD3_RAIL_INDICATOR_W,
    MD3_RAIL_INDICATOR_H,
    MD3_RAIL_ICON_PT,
    MD3_RAIL_LABEL_FS,
    MD3_RAIL_LOGO_H,
)
from utils.ui_strings import MD3_NAV_LABELS, MD3_NAV_ICONS, MD3_APP_TITLE

log = logging.getLogger(__name__)

# Nombre de pages gérées : 4 simulations + 1 page scénarios.
_PAGE_COUNT = 5


class _NavItem(QWidget):
    """Un élément de navigation MD3 : icône + libellé + indicateur actif.

    Parameters
    ----------
    icon : str
        Caractère unicode utilisé comme icône.
    label : str
        Texte affiché sous l'icône.
    """

    clicked = Signal()

    def __init__(self, icon: str, label: str) -> None:
        super().__init__()
        self.setFixedSize(MD3_RAIL_W, MD3_RAIL_ITEM_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Conteneur indicateur (pill MD3)
        self._indicator = QWidget()
        self._indicator.setFixedSize(MD3_RAIL_INDICATOR_W, MD3_RAIL_INDICATOR_H)

        ind_layout = QVBoxLayout(self._indicator)
        ind_layout.setContentsMargins(0, 0, 0, 0)
        ind_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_lbl = QLabel(icon)
        font = QFont()
        font.setPointSize(MD3_RAIL_ICON_PT)
        self._icon_lbl.setFont(font)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("background: transparent;")
        ind_layout.addWidget(self._icon_lbl)
        layout.addWidget(self._indicator, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._label_lbl = QLabel(label)
        self._label_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_lbl.setStyleSheet(
            f"font-size: {MD3_RAIL_LABEL_FS}px; background: transparent; font-weight: 500;"
        )
        layout.addWidget(self._label_lbl)

        self.setStyleSheet("background: transparent;")
        self._apply_styles()

    def set_active(self, active: bool) -> None:
        """Met à jour l'apparence selon l'état actif/inactif."""
        self._active = active
        self._apply_styles()

    def _apply_styles(self) -> None:
        if self._active:
            self._indicator.setStyleSheet(
                f"background: {_ss.MD3_NAV_INDICATOR}; border-radius: {MD3_RAIL_INDICATOR_H // 2}px;"
            )
            self._icon_lbl.setStyleSheet(
                f"color: {_ss.MD3_NAV_ACTIVE_CLR}; background: transparent;"
            )
            self._label_lbl.setStyleSheet(
                f"color: {_ss.MD3_NAV_ACTIVE_CLR}; font-size: {MD3_RAIL_LABEL_FS}px; "
                f"background: transparent; font-weight: 700;"
            )
        else:
            self._indicator.setStyleSheet(
                f"background: transparent; border-radius: {MD3_RAIL_INDICATOR_H // 2}px;"
            )
            self._icon_lbl.setStyleSheet(
                f"color: {_ss.MD3_NAV_INACTIVE}; background: transparent;"
            )
            self._label_lbl.setStyleSheet(
                f"color: {_ss.MD3_NAV_INACTIVE}; font-size: {MD3_RAIL_LABEL_FS}px; "
                f"background: transparent; font-weight: 400;"
            )

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.clicked.emit()


class LibreNavRail(QWidget):
    """Rail de navigation MD3 pour le mode libre.

    Affiche 5 destinations de navigation (4 simulations + Scénarios) plus
    un bouton de fermeture ancré en bas.

    Signals
    -------
    page_selected(int)
        Émis avec l'index 0-basé de la page sélectionnée :
        0 = MCU, 1 = Cône, 2 = Membrane, 3 = ML, 4 = Scénarios.
    exit_requested()
        Émis lorsque l'utilisateur clique sur le bouton de fermeture.
    """

    page_selected = Signal(int)
    exit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Construit le rail avec logo, items de navigation et bouton exit."""
        super().__init__(parent)
        self.setFixedWidth(MD3_RAIL_W)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setObjectName("libreNavRail")
        self.setStyleSheet(
            f"QWidget#libreNavRail {{ "
            f"background-color: {_ss.MD3_NAV_BG}; "
            f"border-right: 1px solid {_ss.MD3_OUTLINE_VAR}; }}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)
        root.setSpacing(0)

        # Logo / titre
        logo = QWidget()
        logo.setFixedHeight(MD3_RAIL_LOGO_H)
        logo.setStyleSheet("background: transparent;")
        logo_lay = QVBoxLayout(logo)
        logo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl = QLabel(MD3_APP_TITLE)
        logo_font = QFont()
        logo_font.setPointSize(9)
        logo_font.setWeight(QFont.Weight.Bold)
        logo_lbl.setFont(logo_font)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet(
            f"color: {_ss.MD3_PRIMARY}; background: transparent; letter-spacing: 0.5px;"
        )
        logo_lay.addWidget(logo_lbl)
        root.addWidget(logo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {_ss.MD3_OUTLINE_VAR}; border: none; max-height: 1px;")
        root.addWidget(sep)

        root.addSpacing(8)

        # Items de navigation
        self._items: list[_NavItem] = []
        for i, (icon, label) in enumerate(zip(MD3_NAV_ICONS, MD3_NAV_LABELS)):
            item = _NavItem(icon, label)
            item.clicked.connect(lambda idx=i: self._on_item_clicked(idx))
            self._items.append(item)
            root.addWidget(item, alignment=Qt.AlignmentFlag.AlignHCenter)

        root.addStretch()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background: {_ss.MD3_OUTLINE_VAR}; border: none; max-height: 1px;")
        root.addWidget(sep2)

        # Bouton exit (✕)
        exit_btn = QPushButton("✕")
        exit_btn.setFixedSize(40, 40)
        exit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {_ss.MD3_ON_SURFACE_VAR}; "
            f"border: none; border-radius: 20px; font-size: 16px; }}"
            f"QPushButton:hover {{ background: {_ss.MD3_SURFACE_VAR}; color: {_ss.MD3_ON_SURFACE}; }}"
        )
        exit_btn.clicked.connect(self.exit_requested.emit)
        root.addWidget(exit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # État initial : aucun item actif
        self._active_idx: int = -1

    def set_active(self, idx: int) -> None:
        """Met en surbrillance l'item à l'index *idx* (-1 = aucun).

        Parameters
        ----------
        idx : int
            Index de la page active (0–4), ou -1 pour tout désactiver.
        """
        if idx == self._active_idx:
            return
        for i, item in enumerate(self._items):
            item.set_active(i == idx)
        self._active_idx = idx

    def _on_item_clicked(self, idx: int) -> None:
        self.set_active(idx)
        self.page_selected.emit(idx)
        log.debug("LibreNavRail — page sélectionnée : %d", idx)
