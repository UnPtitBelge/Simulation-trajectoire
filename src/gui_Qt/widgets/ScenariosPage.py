"""Page Scénarios MD3 pour le mode libre.

Affiche deux sections :

1. Grille de scénarios préconfigurés — cartes MD3 groupées par type de
   simulation, avec un bouton « Lancer » qui sélectionne la page de
   simulation correspondante dans la fenêtre principale.

2. Section Comparaison — widget côte à côte permettant de placer
   n'importe quelles deux simulations en regard.

Architecture
------------
La page est un ``QScrollArea`` contenant un ``QWidget`` vertical.
Le widget ``ComparisonWidget`` est encapsulé dans la même page et peut
être affiché / masqué selon les besoins.

Classes publiques
-----------------
ScenariosPage
    Page scrollable avec cartes de scénarios et comparaison.
    Signal ``scenario_launch_requested(sim_type_idx: int)``.
"""
from __future__ import annotations

import logging

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
    MD3_CARD_RADIUS,
    MD3_SCEN_CARD_W, MD3_SCEN_CARD_H, MD3_SCEN_CHIP_H,
    MD3_SCEN_HEADER_FS, MD3_SCEN_SECTION_FS, MD3_SCEN_CARD_FS, MD3_SCEN_SUB_FS,
    SIM_COLORS,
)
from utils.ui_strings import (
    MD3_SCEN_TITLE, MD3_SCEN_SUBTITLE, MD3_SCEN_LAUNCH_BTN,
    MD3_SCEN_COMPARE_HDR, MD3_SCEN_COMPARE_SUB, MD3_SCEN_SIM_NAMES,
)

log = logging.getLogger(__name__)

# Noms complets affichés dans les en-têtes de section.
_SECTION_NAMES: dict[str, str] = {
    "2d_mcu":      "2D — Mouvement Circulaire Uniforme",
    "3d_cone":     "3D — Surface Conique (Newton)",
    "3d_membrane": "3D — Membrane de Laplace",
    "ml":          "Machine Learning — Prédiction de trajectoire",
}


def _hsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background: {_ss.MD3_OUTLINE_VAR}; border: none; max-height: 1px;")
    return f


class ScenariosPage(QWidget):
    """Page scrollable listant les scénarios et la section comparaison.

    Parameters
    ----------
    scenarios : list[ScenarioConfig]
        Liste complète des scénarios (tous types).
    sim_type_order : list[str]
        Ordre d'affichage des types de simulation.

    Signals
    -------
    scenario_launch_requested(int)
        Émis avec l'index 0-basé du *type* de simulation (0=MCU, 1=Cône,
        2=Membrane, 3=ML) quand l'utilisateur clique sur « Lancer ».
        La fenêtre principale navigue alors vers la page de simulation
        correspondante et y charge le scénario sélectionné.
    """

    # (type_idx, scenario_idx_in_type)
    scenario_launch_requested = Signal(int, int)

    def __init__(self, scenarios: list, sim_type_order: list[str]) -> None:
        super().__init__()
        self._scenarios = scenarios
        self._type_order = sim_type_order
        self._sim_page_refs: list[object] = []  # rempli par la MainWindow

        self.setStyleSheet(f"background: {_ss.MD3_BG};")

        # Scroll area principale
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ width: 6px; background: transparent; }}"
            f"QScrollBar::handle:vertical {{ background: {_ss.MD3_OUTLINE}; border-radius: 3px; }}"
        )

        content = QWidget()
        content.setStyleSheet(f"background: {_ss.MD3_BG};")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(48, 36, 48, 48)
        content_lay.setSpacing(36)

        # ── En-tête ───────────────────────────────────────────────────────
        header_lbl = QLabel(MD3_SCEN_TITLE)
        header_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE}; font-size: {MD3_SCEN_HEADER_FS}px; "
            f"font-weight: 700; background: transparent;"
        )
        content_lay.addWidget(header_lbl)

        sub_lbl = QLabel(MD3_SCEN_SUBTITLE)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: 15px; background: transparent;"
        )
        content_lay.addWidget(sub_lbl)
        content_lay.addWidget(_hsep())

        # ── Sections par type de simulation ───────────────────────────────
        by_type: dict[str, list] = {t: [] for t in sim_type_order}
        for sc in scenarios:
            if sc.sim_type in by_type:
                by_type[sc.sim_type].append(sc)

        for type_idx, stype in enumerate(sim_type_order):
            section = self._build_section(stype, by_type[stype], type_idx)
            content_lay.addWidget(section)

        content_lay.addWidget(_hsep())

        # ── Section Comparaison ───────────────────────────────────────────
        cmp_header = QLabel(MD3_SCEN_COMPARE_HDR)
        cmp_header.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE}; font-size: {MD3_SCEN_SECTION_FS}px; "
            f"font-weight: 700; background: transparent;"
        )
        content_lay.addWidget(cmp_header)

        cmp_sub = QLabel(MD3_SCEN_COMPARE_SUB)
        cmp_sub.setWordWrap(True)
        cmp_sub.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: 13px; background: transparent;"
        )
        content_lay.addWidget(cmp_sub)

        from widgets.ComparisonWidget import ComparisonWidget
        self._comparison = ComparisonWidget(scenarios)
        self._comparison.setMinimumHeight(480)
        self._comparison.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        content_lay.addWidget(self._comparison)

        scroll.setWidget(content)

        # La scroll area prend toute la place
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Construction d'une section par type ───────────────────────────────

    def _build_section(
        self, sim_type: str, scenarios: list, type_idx: int
    ) -> QWidget:
        """Crée une section avec son titre et ses cartes de scénarios."""
        section = QWidget()
        section.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(section)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        # En-tête de section : barre colorée + nom
        accent = SIM_COLORS.get(sim_type, _ss.MD3_PRIMARY)
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        bar = QWidget()
        bar.setFixedSize(4, 20)
        bar.setStyleSheet(f"background: {accent}; border-radius: 2px; border: none;")
        header_row.addWidget(bar)

        sect_lbl = QLabel(_SECTION_NAMES.get(sim_type, sim_type))
        sect_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE}; font-size: {MD3_SCEN_SECTION_FS}px; "
            f"font-weight: 600; background: transparent;"
        )
        header_row.addWidget(sect_lbl)
        header_row.addStretch()

        # Badge « N scénarios »
        count_badge = QLabel(f"{len(scenarios)} scénario{'s' if len(scenarios) > 1 else ''}")
        count_badge.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: 12px; background: transparent;"
        )
        header_row.addWidget(count_badge)
        lay.addLayout(header_row)

        # Rangée de cartes
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        cards_row.setContentsMargins(0, 0, 0, 0)
        for scen_idx, sc in enumerate(scenarios):
            card = self._make_card(sc, accent, type_idx, scen_idx)
            cards_row.addWidget(card)
        cards_row.addStretch()
        lay.addLayout(cards_row)

        return section

    # ── Carte de scénario MD3 ─────────────────────────────────────────────

    def _make_card(
        self, scenario, accent: str, type_idx: int, scen_idx: int
    ) -> QWidget:
        """Crée une carte MD3 pour un scénario."""
        card = QWidget()
        card.setFixedSize(MD3_SCEN_CARD_W, MD3_SCEN_CARD_H)
        card.setStyleSheet(
            f"QWidget {{ background: {_ss.MD3_SURFACE}; "
            f"border-radius: {MD3_CARD_RADIUS}px; "
            f"border: 1px solid {_ss.MD3_OUTLINE_VAR}; }}"
        )

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        # Chip de type de simulation
        chip = QLabel(MD3_SCEN_SIM_NAMES.get(scenario.sim_type, scenario.sim_type))
        chip.setFixedHeight(MD3_SCEN_CHIP_H)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setStyleSheet(
            f"color: {accent}; background: {accent}22; "
            f"border: 1px solid {accent}55; border-radius: {MD3_SCEN_CHIP_H // 2}px; "
            f"font-size: 11px; font-weight: 600; padding: 0 8px;"
        )
        lay.addWidget(chip, alignment=Qt.AlignmentFlag.AlignLeft)

        # Titre
        title_lbl = QLabel(scenario.title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE}; font-size: {MD3_SCEN_CARD_FS}px; "
            f"font-weight: 700; background: transparent; border: none;"
        )
        lay.addWidget(title_lbl)

        # Sous-titre
        sub_lbl = QLabel(scenario.subtitle)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: {MD3_SCEN_SUB_FS}px; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(sub_lbl)

        lay.addStretch()

        # Bouton Lancer (MD3 tonal button)
        btn = QPushButton(f"{MD3_SCEN_LAUNCH_BTN}  →")
        btn.setFixedHeight(32)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: {accent}1A; color: {accent}; "
            f"border: 1px solid {accent}44; border-radius: 16px; "
            f"font-size: 13px; font-weight: 600; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: {accent}33; border-color: {accent}; }}"
        )
        btn.clicked.connect(
            lambda _, ti=type_idx, si=scen_idx: self.scenario_launch_requested.emit(ti, si)
        )
        lay.addWidget(btn)

        return card

    # ── Arrêt de la comparaison ───────────────────────────────────────────

    def stop_comparison(self) -> None:
        """Arrête les simulations en comparaison (appelé à la navigation)."""
        self._comparison.stop_all()
