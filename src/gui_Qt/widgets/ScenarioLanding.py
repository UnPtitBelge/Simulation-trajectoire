"""ScenarioLanding — Grouped scenario selection page.

Shows all preconfigured scenarios grouped by simulation type.
Each group has a coloured section header and a horizontal row of
scenario cards.  Emits ``scenario_selected(int)`` with the 0-based
index into ``libre_config.SCENARIOS`` when a card is activated.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
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
    LANDING_MARGINS, LANDING_SPACING, LANDING_CARDS_GAP,
    LANDING_CARD_MARGINS, LANDING_CARD_SPACING, LANDING_CARD_RADIUS,
    LANDING_ACCENT_H, LANDING_ACCENT_R,
    LANDING_FS_HEADER, LANDING_FS_SUB,
    LANDING_FS_TITLE, LANDING_FS_CARD_SUB,
    LANDING_FS_BTN, LANDING_BTN_RADIUS, LANDING_BTN_ALPHA, LANDING_BTN_H_ALPHA,
    SIM_COLORS,
)
from utils.ui_strings import LANDING_HEADER, LANDING_SUBTITLE, LANDING_BTN


_SIM_DISPLAY_NAMES = {
    "2d_mcu":       "2D  —  Mouvement Circulaire Uniforme",
    "3d_cone":      "3D  —  Surface Conique",
    "3d_membrane":  "3D  —  Membrane de Laplace",
    "ml":           "Machine Learning",
}


class ScenarioLanding(QWidget):
    """Scrollable landing page grouping all scenarios by simulation type.

    Parameters
    ----------
    scenarios : list
        ``libre_config.SCENARIOS`` — list of ``ScenarioConfig`` objects.
    parent : QWidget | None
        Optional parent widget.

    Signals
    -------
    scenario_selected(int)
        Emitted with the 0-based index into the ``scenarios`` list when the
        user activates a card.
    """

    scenario_selected = Signal(int)

    def __init__(
        self,
        scenarios: list,
        parent: QWidget | None = None,
    ) -> None:
        """Build the landing page with a header and grouped scenario cards."""
        super().__init__(parent)
        self._scenarios = scenarios

        root = QVBoxLayout(self)
        root.setContentsMargins(*LANDING_MARGINS)
        root.setSpacing(LANDING_SPACING)

        # ── Header ────────────────────────────────────────────────────────
        header = QLabel(LANDING_HEADER)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            f"color: {_ss.CLR_TEXT}; font-size: {LANDING_FS_HEADER}px; "
            f"font-weight: 800; letter-spacing: 1px; background: transparent;"
        )
        root.addWidget(header)

        sub = QLabel(LANDING_SUBTITLE)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            f"color: {_ss.CLR_SUBTEXT}; font-size: {LANDING_FS_SUB}px; background: transparent;"
        )
        root.addWidget(sub)

        # ── Scrollable groups area ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ width: 6px; background: transparent; }}"
            f"QScrollBar::handle:vertical {{ background: {_ss.CLR_SURFACE2}; border-radius: 3px; }}"
        )

        groups_widget = QWidget()
        groups_widget.setStyleSheet("background: transparent;")
        groups_lay = QVBoxLayout(groups_widget)
        groups_lay.setSpacing(LANDING_SPACING * 2)
        groups_lay.setContentsMargins(0, 0, 0, 0)

        from utils.libre_config import SIM_TYPE_ORDER
        for sim_type in SIM_TYPE_ORDER:
            group = self._build_group(sim_type)
            if group is not None:
                groups_lay.addWidget(group)

        groups_lay.addStretch()
        scroll.setWidget(groups_widget)
        root.addWidget(scroll, stretch=1)

    def _build_group(self, sim_type: str) -> QWidget | None:
        """Build a section (header + cards row) for one simulation type.

        Returns ``None`` if there are no scenarios for that type.
        """
        type_scenarios = [
            (i, s) for i, s in enumerate(self._scenarios)
            if s.sim_type == sim_type
        ]
        if not type_scenarios:
            return None

        color = SIM_COLORS.get(sim_type, _ss.CLR_ACCENT)

        section = QWidget()
        section.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(section)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        # Section title row
        title_row = QWidget()
        title_row.setStyleSheet("background: transparent;")
        tr = QHBoxLayout(title_row)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(10)

        accent_dot = QWidget()
        accent_dot.setFixedSize(6, 28)
        accent_dot.setStyleSheet(
            f"background: {color}; border-radius: 3px;"
        )
        tr.addWidget(accent_dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        name = _SIM_DISPLAY_NAMES.get(sim_type, sim_type)
        title_lbl = QLabel(name)
        title_lbl.setStyleSheet(
            f"color: {color}; font-size: {LANDING_FS_TITLE}px; "
            f"font-weight: 700; background: transparent;"
        )
        tr.addWidget(title_lbl)
        tr.addStretch()
        lay.addWidget(title_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            f"background: {color}44; border: none; max-height: 1px;"
        )
        lay.addWidget(sep)

        # Cards row
        cards_row = QWidget()
        cards_row.setStyleSheet("background: transparent;")
        cr = QHBoxLayout(cards_row)
        cr.setContentsMargins(0, 4, 0, 0)
        cr.setSpacing(LANDING_CARDS_GAP)

        for global_idx, scenario in type_scenarios:
            card = self._make_card(global_idx, scenario, color)
            cr.addWidget(card)

        cr.addStretch()
        lay.addWidget(cards_row)

        return section

    def _make_card(self, idx: int, scenario, color: str) -> QWidget:
        """Build a single clickable scenario card.

        Parameters
        ----------
        idx      Global index in ``self._scenarios``.
        scenario ``ScenarioConfig`` instance.
        color    Hex colour for the accent bar and button.
        """
        card = QWidget()
        card.setFixedWidth(220)
        card.setStyleSheet(
            f"QWidget {{ background: {_ss.CLR_SURFACE0}; "
            f"border-radius: {LANDING_CARD_RADIUS}px; "
            f"border: 1px solid {_ss.CLR_BORDER}; }}"
            f"QWidget:hover {{ background: {_ss.CLR_SURFACE1}; "
            f"border-color: {color}66; }}"
        )
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(*LANDING_CARD_MARGINS)
        lay.setSpacing(LANDING_CARD_SPACING)

        # Top accent bar
        accent_bar = QWidget()
        accent_bar.setFixedHeight(LANDING_ACCENT_H)
        accent_bar.setStyleSheet(
            f"background: {color}; border-radius: {LANDING_ACCENT_R}px; border: none;"
        )
        lay.addWidget(accent_bar)

        # Title
        title_lbl = QLabel(scenario.title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"color: {_ss.CLR_TEXT}; font-size: {LANDING_FS_TITLE}px; "
            f"font-weight: 700; background: transparent; border: none;"
        )
        lay.addWidget(title_lbl)

        # Subtitle
        if scenario.subtitle:
            sub_lbl = QLabel(scenario.subtitle)
            sub_lbl.setWordWrap(True)
            sub_lbl.setStyleSheet(
                f"color: {_ss.CLR_SUBTEXT}; font-size: {LANDING_FS_CARD_SUB}px; "
                f"background: transparent; border: none;"
            )
            lay.addWidget(sub_lbl)

        lay.addStretch()

        # Launch button
        btn = QPushButton(LANDING_BTN)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setStyleSheet(
            f"QPushButton {{ background: {color}{LANDING_BTN_ALPHA}; color: {color}; "
            f"border: 1px solid {color}; border-radius: {LANDING_BTN_RADIUS}px; "
            f"padding: 6px 16px; font-size: {LANDING_FS_BTN}px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {color}{LANDING_BTN_H_ALPHA}; }}"
        )
        btn.clicked.connect(lambda: self.scenario_selected.emit(idx))
        lay.addWidget(btn)

        card.mousePressEvent = lambda e, i=idx: self.scenario_selected.emit(i)
        return card
