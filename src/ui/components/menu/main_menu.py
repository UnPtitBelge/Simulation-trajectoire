"""Libre-mode menu builder — educational landing page."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.core.content import WELCOME_SUBTITLE, WELCOME_TITLE
from src.utils.shortcuts import SHORTCUT_LABELS
from src.utils.theme import (
    CLR_BORDER,
    CLR_SURFACE,
    CLR_TEXT_SECONDARY,
    FS_MD,
    FS_3XL,
)


def make_card(title: str, text: str, callback, parent=None) -> QFrame:
    c = QFrame(parent)
    c.setProperty("card", True)
    c.setFixedHeight(170)
    lay = QVBoxLayout(c)
    lay.setContentsMargins(16, 16, 16, 16)
    lay.setSpacing(8)
    t = QLabel(f"<b style='font-size:{FS_MD}'>{title}</b>")
    d = QLabel(text)
    d.setWordWrap(True)
    d.setProperty("role", "secondary")
    b = QPushButton("Ouvrir")
    b.setFixedWidth(90)
    b.clicked.connect(callback)
    lay.addWidget(t)
    lay.addWidget(d, stretch=1)
    lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignRight)
    return c


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("role", "section")
    return lbl


def build_menu(
    on_open_comparison,
    on_open_theory=None,
) -> tuple[QWidget, QGridLayout]:
    """Build the libre-mode menu. Returns (root_widget, sim_card_grid)."""
    root = QWidget()
    outer = QVBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    # ── Compact welcome header ────────────────────────────────────────────────
    welcome = QWidget()
    welcome.setStyleSheet(
        f"background: {CLR_SURFACE}; border-bottom: 1px solid {CLR_BORDER};"
    )
    w_lay = QVBoxLayout(welcome)
    w_lay.setContentsMargins(40, 24, 40, 20)
    w_lay.setSpacing(6)

    title_lbl = QLabel(WELCOME_TITLE)
    title_lbl.setStyleSheet(f"font-size:{FS_3XL}; font-weight:500;")
    w_lay.addWidget(title_lbl)

    subtitle_lbl = QLabel(WELCOME_SUBTITLE)
    subtitle_lbl.setStyleSheet(f"font-size:{FS_MD}; color:{CLR_TEXT_SECONDARY};")
    w_lay.addWidget(subtitle_lbl)

    outer.addWidget(welcome)

    # ── Scrollable content ────────────────────────────────────────────────────
    content = QWidget()
    content_lay = QVBoxLayout(content)
    content_lay.setContentsMargins(40, 24, 40, 24)
    content_lay.setSpacing(16)

    desc = QLabel(
        "Modifiez librement les paramètres et observez le comportement "
        "des simulations en temps réel grâce aux sliders intégrés."
    )
    desc.setWordWrap(True)
    desc.setProperty("role", "secondary")
    content_lay.addWidget(desc)

    content_lay.addWidget(_section_label("Simulations"))
    sim_grid = QGridLayout()
    sim_grid.setSpacing(14)
    content_lay.addLayout(sim_grid)

    if on_open_theory:
        content_lay.addWidget(_section_label("Apprendre"))
        theory_btn = QPushButton("Théorie de la modélisation")
        theory_btn.setFixedHeight(48)
        theory_btn.setProperty("secondary", True)
        theory_btn.clicked.connect(on_open_theory)
        content_lay.addWidget(theory_btn)

    content_lay.addWidget(_section_label("Outils"))
    cb = QPushButton("Comparer deux simulations")
    cb.setFixedHeight(44)
    cb.clicked.connect(on_open_comparison)
    content_lay.addWidget(cb)

    content_lay.addWidget(_section_label("Raccourcis clavier"))
    for key, desc_text in SHORTCUT_LABELS:
        row = QLabel(f"  <b>{key}</b> — {desc_text}")
        row.setProperty("role", "secondary")
        content_lay.addWidget(row)

    content_lay.addStretch()

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(content)
    outer.addWidget(scroll, stretch=1)

    return root, sim_grid
