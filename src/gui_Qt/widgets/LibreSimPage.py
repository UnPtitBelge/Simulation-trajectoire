"""Page simulation + tableau de bord MD3 pour le mode libre.

Chaque page affiche :
- À gauche : le widget OpenGL/pyqtgraph de la simulation (zone principale).
- À droite : une barre latérale MD3 fixe (360 px) avec trois cartes :
    1. Carte Modèle  — titre, sous-titre, équation clé (cliquable).
    2. Carte Live    — jauge d'arc, position XYZ, sparkline de vitesse.
    3. Carte Explication — sélecteur de niveau (chips), texte adapté,
                          anecdote « Le savais-tu ? ».

Architecture
------------
La préparation lourde (``_prepare_simulation``) est déléguée à un
``QThread`` pour ne pas bloquer l'event loop.  Un overlay de chargement
couvre la zone de simulation jusqu'à la fin du calcul.

La simulation démarre automatiquement dès que le calcul est terminé.

Classes publiques
-----------------
LibreSimPage
    Widget autonome pour une simulation en mode libre.

    Méthodes de contrôle externes (appelées par MainWindow) :
    ``start_animation()``, ``stop_animation()``, ``reset_animation()``.
"""
from __future__ import annotations

import logging
from collections import deque
from math import hypot

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
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
    MD3_SIDEBAR_W, MD3_CARD_RADIUS, MD3_CARD_PADDING, MD3_CARD_SPACING,
    MD3_SIDEBAR_MARGINS, MD3_SIDEBAR_SPACING,
    MD3_FS_SECTION, MD3_FS_TITLE, MD3_FS_SUBTITLE, MD3_FS_EQ,
    MD3_FS_VALUE, MD3_FS_AXIS, MD3_FS_EXPL, MD3_FS_FACT, MD3_FS_CHIP,
    MD3_GAUGE_W, MD3_GAUGE_H, MD3_GAUGE_PEN_W,
    MD3_SPARK_H, MD3_SPARK_MAXLEN, MD3_SPARK_PEN_W,
    MD3_ORBIT_SIZE, MD3_ORBIT_MAXLEN, MD3_ORBIT_ALPHA_LO, MD3_ORBIT_ALPHA_HI,
    MD3_ORBIT_PEN_W, MD3_ORBIT_DOT_R,
    MD3_THROTTLE,
    DASH_GAUGE_HUE_MAX,
)
from utils.ui_strings import (
    MD3_SECTION_MODEL, MD3_SECTION_LIVE, MD3_SECTION_EXPL,
    DASH_LEVELS, DASH_LEVEL_ICONS, DASH_LEVEL_EXTREME, DASH_LEVEL_COMPARE,
    DASH_ICON_EXTREME, DASH_ICON_COMPARE,
    DASH_GAUGE_UNIT, DASH_FACT_TITLE,
)
from utils.ui_constants import SIM_COLORS

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background thread
# ---------------------------------------------------------------------------

class _PrepareWorker(QThread):
    """Exécute ``_prepare_simulation()`` hors du thread principal."""

    done = Signal()

    def __init__(self, plot) -> None:
        super().__init__()
        self._plot = plot

    def run(self) -> None:
        self._plot._prepare_simulation()
        self.done.emit()


# ---------------------------------------------------------------------------
# Mini-widgets QPainter (réutilisés du dashboard original, adaptés MD3)
# ---------------------------------------------------------------------------

class _ArcGauge(QWidget):
    """Jauge demi-cercle QPainter — vitesse courante vs maximum observé."""

    def __init__(self, accent: str) -> None:
        super().__init__()
        self._speed = 0.0
        self._max = 1.0
        self._accent = accent
        self.setFixedSize(MD3_GAUGE_W, MD3_GAUGE_H)
        self.setStyleSheet("background: transparent;")

    def set_speed(self, speed: float, max_speed: float) -> None:
        self._speed = max(speed, 0.0)
        self._max = max(max_speed, 1e-9)
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h - 10
        r = min(cx - 10, cy - 6)
        from PySide6.QtCore import QRect
        rect = QRect(int(cx - r), int(cy - r), int(2 * r), int(2 * r))
        ratio = min(self._speed / self._max, 1.0)

        # Arc de fond (outline-variant)
        bg = QPen(QColor(_ss.MD3_OUTLINE_VAR), MD3_GAUGE_PEN_W)
        bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(bg)
        p.drawArc(rect, 180 * 16, -180 * 16)

        # Arc de valeur (couleur HSV vert → rouge)
        if ratio > 0.01:
            hue = max(int(DASH_GAUGE_HUE_MAX * (1.0 - ratio)), 0)
            color = QColor.fromHsv(hue, 200, 180)
            val = QPen(color, MD3_GAUGE_PEN_W)
            val.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(val)
            p.drawArc(rect, 180 * 16, -int(ratio * 180 * 16))

        # Valeur numérique
        hue_t = max(int(DASH_GAUGE_HUE_MAX * (1.0 - ratio)), 0)
        tc = QColor.fromHsv(hue_t, 180, 160) if ratio > 0.05 else QColor(_ss.MD3_ON_SURFACE_DIM)
        p.setPen(QPen(tc))
        p.setFont(QFont("Monospace", 12, QFont.Weight.Bold))
        p.drawText(
            QRect(int(cx - 40), int(cy - 34), 80, 24),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._speed:.3f}",
        )
        p.setPen(QPen(QColor(_ss.MD3_ON_SURFACE_DIM)))
        p.setFont(QFont("sans-serif", 8))
        p.drawText(
            QRect(int(cx - 16), int(cy - 12), 32, 12),
            Qt.AlignmentFlag.AlignCenter,
            DASH_GAUGE_UNIT,
        )


class _OrbitTrace(QWidget):
    """Miniature de trajectoire vue de dessus (QPainter)."""

    def __init__(self, accent: str) -> None:
        super().__init__()
        self._trail_x: deque[float] = deque(maxlen=MD3_ORBIT_MAXLEN)
        self._trail_y: deque[float] = deque(maxlen=MD3_ORBIT_MAXLEN)
        self._max_r = 1e-9
        self._accent = QColor(accent)
        self.setFixedSize(MD3_ORBIT_SIZE, MD3_ORBIT_SIZE)
        self.setStyleSheet("background: transparent;")

    def add_point(self, x: float, y: float) -> None:
        self._trail_x.append(x)
        self._trail_y.append(y)
        r = hypot(x, y)
        if r > self._max_r:
            self._max_r = r
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(cx, cy) - 4

        # Fond circulaire
        p.setPen(QPen(QColor(_ss.MD3_OUTLINE_VAR), 1))
        p.setBrush(QBrush(QColor(_ss.MD3_SURFACE_VAR)))
        p.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        p.setBrush(Qt.NoBrush)

        xs = list(self._trail_x)
        ys = list(self._trail_y)
        if len(xs) < 2:
            return
        scale = (radius - 6) / self._max_r
        n = len(xs)
        for i in range(1, n):
            alpha = max(MD3_ORBIT_ALPHA_LO, int(MD3_ORBIT_ALPHA_HI * i / n))
            c = QColor(self._accent)
            c.setAlpha(alpha)
            p.setPen(QPen(c, MD3_ORBIT_PEN_W))
            p.drawLine(
                int(cx + xs[i - 1] * scale), int(cy - ys[i - 1] * scale),
                int(cx + xs[i] * scale),     int(cy - ys[i] * scale),
            )
        # Point courant
        dot_x = int(cx + xs[-1] * scale)
        dot_y = int(cy - ys[-1] * scale)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(self._accent))
        p.drawEllipse(
            dot_x - MD3_ORBIT_DOT_R, dot_y - MD3_ORBIT_DOT_R,
            MD3_ORBIT_DOT_R * 2,     MD3_ORBIT_DOT_R * 2,
        )


class _Sparkline(QWidget):
    """Historique de vitesse sous forme de courbe (QPainter)."""

    def __init__(self, accent: str) -> None:
        super().__init__()
        self._data: deque[float] = deque(maxlen=MD3_SPARK_MAXLEN)
        self._accent = QColor(accent)
        self.setFixedHeight(MD3_SPARK_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent;")

    def add_value(self, v: float) -> None:
        self._data.append(v)
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Fond léger
        p.fillRect(self.rect(), QColor(_ss.MD3_SURFACE_VAR))

        data = list(self._data)
        if len(data) < 2:
            return
        maxv = max(data) or 1e-9
        n = len(data)
        ypad = 4
        from PySide6.QtCore import QPoint
        pts = [
            QPoint(
                int(w * i / (n - 1)),
                int(h - ypad - (h - ypad * 2) * v / maxv),
            )
            for i, v in enumerate(data)
        ]
        pen = QPen(self._accent, MD3_SPARK_PEN_W)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        for i in range(1, len(pts)):
            p.drawLine(pts[i - 1], pts[i])


# ---------------------------------------------------------------------------
# Helpers de mise en page MD3
# ---------------------------------------------------------------------------

def _md3_card(parent_layout: QVBoxLayout | None = None) -> QWidget:
    """Crée un widget carte MD3 (fond blanc, bordure arrondie, ombre légère)."""
    card = QWidget()
    card.setStyleSheet(
        f"QWidget {{ background: {_ss.MD3_SURFACE}; "
        f"border-radius: {MD3_CARD_RADIUS}px; "
        f"border: 1px solid {_ss.MD3_OUTLINE_VAR}; }}"
    )
    if parent_layout is not None:
        parent_layout.addWidget(card)
    return card


def _section_lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {_ss.MD3_ON_SURFACE_DIM}; font-size: {MD3_FS_SECTION}px; "
        f"font-weight: 700; letter-spacing: 1.6px; background: transparent;"
    )
    return lbl


def _hsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background: {_ss.MD3_OUTLINE_VAR}; border: none; max-height: 1px;")
    return f


# ---------------------------------------------------------------------------
# Barre latérale MD3
# ---------------------------------------------------------------------------

class _MD3Sidebar(QWidget):
    """Panneau latéral droit (360 px) avec trois cartes MD3.

    Reçoit les données de simulation via :meth:`update_data`.
    """

    def __init__(self, sim_type: str, content: dict) -> None:
        super().__init__()
        self._sim_type = sim_type
        self._content = content
        self._has_z = sim_type in ("3d_cone", "3d_membrane")
        self._accent = content.get("color", _ss.MD3_PRIMARY)
        self._max_speed = 1e-9
        self._frame_ctr = 0

        self.setFixedWidth(MD3_SIDEBAR_W)
        self.setStyleSheet(
            f"background: {_ss.MD3_BG}; border-left: 1px solid {_ss.MD3_OUTLINE_VAR};"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(*MD3_SIDEBAR_MARGINS)
        root.setSpacing(MD3_SIDEBAR_SPACING)

        root.addWidget(self._build_model_card())
        root.addWidget(self._build_live_card())
        root.addWidget(self._build_explanation_card(), stretch=1)

    # ── Carte 1 : Modèle ───────────────────────────────────────────────────

    def _build_model_card(self) -> QWidget:
        card = _md3_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(*MD3_CARD_PADDING)
        lay.setSpacing(MD3_CARD_SPACING)

        lay.addWidget(_section_lbl(MD3_SECTION_MODEL))

        # Titre coloré avec accent de la sim
        accent_bar = QWidget()
        accent_bar.setFixedSize(3, 18)
        accent_bar.setStyleSheet(
            f"background: {self._accent}; border-radius: 2px; border: none;"
        )

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(accent_bar)

        title = QLabel(self._content.get("title", "—"))
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE}; font-size: {MD3_FS_TITLE}px; "
            f"font-weight: 700; background: transparent;"
        )
        title_row.addWidget(title, stretch=1)
        lay.addLayout(title_row)

        sub = QLabel(self._content.get("subtitle", ""))
        sub.setWordWrap(True)
        sub.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: {MD3_FS_SUBTITLE}px; "
            f"background: transparent;"
        )
        lay.addWidget(sub)

        # Équation cliquable
        eq_box = QWidget()
        eq_box.setStyleSheet(
            f"background: {_ss.MD3_SURFACE_VAR}; border-radius: 8px; "
            f"border: 1px solid {_ss.MD3_OUTLINE_VAR};"
        )
        eq_box.setCursor(Qt.CursorShape.PointingHandCursor)
        eq_lay = QVBoxLayout(eq_box)
        eq_lay.setContentsMargins(10, 6, 10, 6)
        eq_lay.setSpacing(2)

        hint_lbl = QLabel("🔍  cliquer pour les détails")
        hint_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_DIM}; font-size: 11px; "
            f"font-style: italic; background: transparent;"
        )
        eq_lay.addWidget(hint_lbl)

        eq_lbl = QLabel(self._content.get("key_equation", ""))
        eq_lbl.setWordWrap(True)
        eq_lbl.setStyleSheet(
            f"color: {self._accent}; font-family: Monospace; "
            f"font-size: {MD3_FS_EQ}px; background: transparent;"
        )
        eq_lay.addWidget(eq_lbl)

        formula_details = self._content.get("formula_details", [])
        accent = self._accent
        eq_box.mousePressEvent = lambda _: self._open_formula_dialog(formula_details, accent)
        lay.addWidget(eq_box)

        # Trace d'orbite
        orbit_row = QHBoxLayout()
        orbit_row.setSpacing(10)
        self._orbit = _OrbitTrace(self._accent)
        orbit_row.addWidget(self._orbit)
        orbit_info = QVBoxLayout()
        orbit_info.setSpacing(2)
        orbit_info.addWidget(_section_lbl("TRAJECTOIRE"))
        orbit_info.addStretch()
        orbit_row.addLayout(orbit_info)
        lay.addLayout(orbit_row)

        return card

    # ── Carte 2 : Données en direct ────────────────────────────────────────

    def _build_live_card(self) -> QWidget:
        card = _md3_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(*MD3_CARD_PADDING)
        lay.setSpacing(MD3_CARD_SPACING)

        lay.addWidget(_section_lbl(MD3_SECTION_LIVE))

        # Jauge d'arc centrée
        self._gauge = _ArcGauge(self._accent)
        lay.addWidget(self._gauge, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Cartes de position XYZ
        pos_row = QHBoxLayout()
        pos_row.setSpacing(6)
        self._pos: dict[str, QLabel] = {}
        axes = ("X", "Y", "Z") if self._has_z else ("X", "Y")
        for axis in axes:
            pos_card = QWidget()
            pos_card.setStyleSheet(
                f"background: {_ss.MD3_SURFACE_VAR}; border-radius: 6px; "
                f"border: 1px solid {_ss.MD3_OUTLINE_VAR};"
            )
            pcl = QVBoxLayout(pos_card)
            pcl.setContentsMargins(6, 4, 6, 4)
            pcl.setSpacing(1)
            a_lbl = QLabel(axis)
            a_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            a_lbl.setStyleSheet(
                f"color: {_ss.MD3_ON_SURFACE_DIM}; font-size: {MD3_FS_AXIS}px; "
                f"font-weight: 700; background: transparent;"
            )
            v_lbl = QLabel("—")
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_lbl.setStyleSheet(
                f"color: {_ss.MD3_ON_SURFACE}; font-family: Monospace; "
                f"font-size: {MD3_FS_VALUE}px; background: transparent;"
            )
            pcl.addWidget(a_lbl)
            pcl.addWidget(v_lbl)
            self._pos[axis] = v_lbl
            pos_row.addWidget(pos_card)
        lay.addLayout(pos_row)

        # Sparkline
        lay.addWidget(_section_lbl("VITESSE"))
        self._sparkline = _Sparkline(self._accent)
        lay.addWidget(self._sparkline)

        return card

    # ── Carte 3 : Explication ──────────────────────────────────────────────

    def _build_explanation_card(self) -> QWidget:
        card = _md3_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(*MD3_CARD_PADDING)
        lay.setSpacing(MD3_CARD_SPACING)

        lay.addWidget(_section_lbl(MD3_SECTION_EXPL))

        # Sélecteur de niveau (chips MD3)
        chip_row = QHBoxLayout()
        chip_row.setSpacing(6)
        chip_row.setContentsMargins(0, 0, 0, 0)

        self._level = "decouverte"
        self._chips: dict[str, QPushButton] = {}
        all_keys = list(DASH_LEVELS) + [DASH_LEVEL_EXTREME, DASH_LEVEL_COMPARE]
        all_icons = list(DASH_LEVEL_ICONS) + [DASH_ICON_EXTREME, DASH_ICON_COMPARE]
        for key, icon in zip(all_keys, all_icons):
            chip = QPushButton(icon)
            chip.setCheckable(True)
            chip.setChecked(key == self._level)
            chip.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            chip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            chip.setFixedHeight(24)
            chip.clicked.connect(lambda _, k=key: self._set_level(k))
            self._chips[key] = chip
            chip_row.addWidget(chip)
        self._refresh_chip_styles()
        lay.addLayout(chip_row)

        lay.addWidget(_hsep())

        # Texte d'explication (scrollable)
        self._expl_lbl = QLabel(self._content.get("levels", {}).get(self._level, ""))
        self._expl_lbl.setWordWrap(True)
        self._expl_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._expl_lbl.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self._expl_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE}; font-size: {MD3_FS_EXPL}px; "
            f"background: transparent; line-height: 1.5;"
        )

        scroll = QScrollArea()
        scroll.setWidget(self._expl_lbl)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ width: 4px; background: transparent; }}"
            f"QScrollBar::handle:vertical {{ background: {_ss.MD3_OUTLINE}; border-radius: 2px; }}"
        )
        lay.addWidget(scroll, stretch=1)

        lay.addWidget(_hsep())

        # Anecdote
        fact_box = QWidget()
        fact_box.setStyleSheet(
            f"background: {_ss.MD3_PRIMARY_CONT}; border-radius: 8px; "
            f"border: 1px solid {_ss.MD3_OUTLINE_VAR};"
        )
        fl = QVBoxLayout(fact_box)
        fl.setContentsMargins(10, 8, 10, 8)
        fl.setSpacing(4)
        ft = QLabel(DASH_FACT_TITLE)
        ft.setStyleSheet(
            f"color: {_ss.MD3_PRIMARY}; font-size: {MD3_FS_CHIP}px; "
            f"font-weight: 700; background: transparent;"
        )
        fl.addWidget(ft)
        fb = QLabel(self._content.get("fun_fact", ""))
        fb.setWordWrap(True)
        fb.setStyleSheet(
            f"color: {_ss.MD3_ON_PRIMARY_CONT}; font-size: {MD3_FS_FACT}px; "
            f"background: transparent;"
        )
        fl.addWidget(fb)
        lay.addWidget(fact_box)

        return card

    # ── Niveau ─────────────────────────────────────────────────────────────

    def _set_level(self, level: str) -> None:
        self._level = level
        levels = self._content.get("levels", {})
        text = levels[level] if level in levels else self._content.get(level, "—")
        self._expl_lbl.setText(text)
        for k, chip in self._chips.items():
            chip.setChecked(k == level)
        self._refresh_chip_styles()

    def _refresh_chip_styles(self) -> None:
        for key, chip in self._chips.items():
            if chip.isChecked():
                chip.setStyleSheet(
                    f"QPushButton {{ background: {_ss.MD3_PRIMARY_CONT}; "
                    f"color: {_ss.MD3_ON_PRIMARY_CONT}; border: 1px solid {_ss.MD3_PRIMARY}; "
                    f"border-radius: 12px; font-size: {MD3_FS_CHIP}px; "
                    f"font-weight: 700; padding: 1px 6px; }}"
                )
            else:
                chip.setStyleSheet(
                    f"QPushButton {{ background: transparent; "
                    f"color: {_ss.MD3_ON_SURFACE_VAR}; "
                    f"border: 1px solid {_ss.MD3_OUTLINE}; "
                    f"border-radius: 12px; font-size: {MD3_FS_CHIP}px; padding: 1px 6px; }}"
                    f"QPushButton:hover {{ background: {_ss.MD3_SURFACE_TINT}; "
                    f"color: {_ss.MD3_PRIMARY}; border-color: {_ss.MD3_PRIMARY}; }}"
                )

    def _open_formula_dialog(self, formula_details: list, accent: str) -> None:
        from widgets.FormulaDialog import FormulaDialog
        dlg = FormulaDialog(formula_details, accent, parent=self)
        dlg.exec()

    # ── Mise à jour live ───────────────────────────────────────────────────

    def update_data(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        z: float | None = None,
    ) -> None:
        """Met à jour tous les indicateurs avec les données de la frame courante.

        Jauge et labels XYZ à chaque frame.
        Orbite et sparkline tous les ``MD3_THROTTLE`` frames.
        """
        speed = hypot(vx, vy)
        self._max_speed = max(self._max_speed, speed)
        self._frame_ctr += 1

        self._gauge.set_speed(speed, self._max_speed)
        self._pos["X"].setText(f"{x:.3f}")
        self._pos["Y"].setText(f"{y:.3f}")
        if "Z" in self._pos:
            self._pos["Z"].setText(f"{z:.3f}" if z is not None else "—")

        if self._frame_ctr % MD3_THROTTLE == 0:
            self._orbit.add_point(x, y)
            self._sparkline.add_value(speed)


# ---------------------------------------------------------------------------
# LibreSimPage — page principale
# ---------------------------------------------------------------------------

class LibreSimPage(QWidget):
    """Page simulation + barre latérale MD3 pour le mode libre.

    Crée le plot de simulation, lance sa préparation en arrière-plan,
    affiche un overlay de chargement, et connecte les données de chaque
    frame au panneau latéral.

    Parameters
    ----------
    sim_type : str
        Type de simulation : ``"2d_mcu"``, ``"3d_cone"``, ``"3d_membrane"``
        ou ``"ml"``.
    params : object
        Instance du dataclass de paramètres pour ce type de simulation.
    content : dict
        Entrée de ``libre_config.CONTENT`` pour ce type.
    """

    def __init__(self, sim_type: str, params, content: dict) -> None:
        super().__init__()
        self._sim_type = sim_type
        self._content = content

        self.setStyleSheet(f"background: {_ss.MD3_BG};")

        # ── Création du plot ───────────────────────────────────────────────
        self.plot = self._make_plot(sim_type, params)

        # ── Layout principal (horizontal) ──────────────────────────────────
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Zone de simulation (plot + overlay de chargement)
        self._plot_container = QWidget()
        self._plot_container.setStyleSheet("background: #000000;")
        self._grid = QGridLayout(self._plot_container)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.addWidget(self.plot.widget, 0, 0)

        self._loading = QWidget()
        self._loading.setStyleSheet(f"background: rgba(0,0,0,200);")
        _ll = QVBoxLayout(self._loading)
        _ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _loading_lbl = QLabel("Calcul en cours…")
        _loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _loading_lbl.setStyleSheet(
            f"color: #ffffff; font-size: 16px; background: transparent;"
        )
        _ll.addWidget(_loading_lbl)
        self._grid.addWidget(self._loading, 0, 0)

        root.addWidget(self._plot_container, stretch=1)

        # Barre latérale MD3
        self._sidebar = _MD3Sidebar(sim_type, content)
        root.addWidget(self._sidebar)

        # ── Préparation en arrière-plan ────────────────────────────────────
        self._worker = _PrepareWorker(self.plot)
        self._worker.done.connect(self._on_ready)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

        log.debug("LibreSimPage créée — sim_type=%s", sim_type)

    # ── Factory plots ──────────────────────────────────────────────────────

    @staticmethod
    def _make_plot(sim_type: str, params) -> object:
        """Instancie le plot correspondant au type de simulation."""
        if sim_type == "2d_mcu":
            from simulations.sim2d.PlotMCU import PlotMCU
            return PlotMCU(params)
        elif sim_type == "3d_cone":
            from simulations.sim3d.PlotCone import PlotCone
            return PlotCone(params)
        elif sim_type == "3d_membrane":
            from simulations.sim3d.PlotMembrane import PlotMembrane
            return PlotMembrane(params)
        elif sim_type == "ml":
            from simulations.simML.PlotML import PlotML
            return PlotML(params)
        raise ValueError(f"Type de simulation inconnu : {sim_type!r}")

    # ── Callback préparation terminée ──────────────────────────────────────

    def _on_ready(self) -> None:
        self.plot._prepared = True
        self.plot.current_frame = 0
        self.plot._draw_initial_frame()
        self._loading.setVisible(False)
        self._worker = None
        # Connexion des données de frame
        self.plot.frame_updated.connect(self._on_frame)
        # Démarrage automatique
        self.start_animation()
        log.info("LibreSimPage prête — sim_type=%s", self._sim_type)

    # ── Mise à jour frame → sidebar ────────────────────────────────────────

    def _on_frame(self, idx: int) -> None:
        """Lit les trajectoires du plot et met à jour la barre latérale."""
        if self._sim_type == "ml":
            if self.plot._pred_traj.shape[0] == 0:
                return
            i = min(idx, self.plot._pred_traj.shape[0] - 1)
            x, y = self.plot._pred_traj[i]
            dt = self.plot.sim_params.frame_ms / 1000.0
            if i > 0:
                px, py = self.plot._pred_traj[i - 1]
                vx, vy = (x - px) / dt, (y - py) / dt
            else:
                vx, vy = 0.0, 0.0
            self._sidebar.update_data(x=x, y=y, vx=vx, vy=vy)
        else:
            if not self.plot.trajectory_xs or idx >= len(self.plot.trajectory_xs):
                return
            kwargs = dict(
                x=self.plot.trajectory_xs[idx],
                y=self.plot.trajectory_ys[idx],
                vx=self.plot.trajectory_vxs[idx] if self.plot.trajectory_vxs else 0.0,
                vy=self.plot.trajectory_vys[idx] if self.plot.trajectory_vys else 0.0,
            )
            if self._sim_type in ("3d_cone", "3d_membrane"):
                kwargs["z"] = self.plot.trajectory_zs[idx]
            self._sidebar.update_data(**kwargs)

    # ── Contrôle de la simulation ──────────────────────────────────────────

    def start_animation(self) -> None:
        """Repart de l'image 0 et lance l'animation."""
        if not self.plot._prepared:
            return
        self.plot.stop_animation()
        self.plot.start_animation()

    def stop_animation(self) -> None:
        """Arrête l'animation sans rembobiner."""
        self.plot.stop_animation()

    def reset_animation(self) -> None:
        """Rembobine à l'image 0 sans relancer."""
        if not self.plot._prepared:
            return
        self.plot.reset_animation()

    def reload_with_params(self, params) -> None:
        """Remplace la simulation courante par une nouvelle avec *params*.

        Arrête l'animation, dispose le plot précédent, crée un nouveau
        plot du même type, et relance la préparation en arrière-plan.
        La simulation redémarre automatiquement une fois prête.

        Parameters
        ----------
        params : dataclass instance
            Paramètres compatibles avec le type de simulation de la page.
        """
        # Arrêter l'animation et déconnecter les signaux.
        self.stop_animation()
        try:
            self.plot.frame_updated.disconnect(self._on_frame)
        except RuntimeError:
            pass

        # Arrêter un éventuel worker en cours.
        if self._worker is not None:
            self._worker.quit()
            self._worker.wait()
            self._worker = None

        # Retirer l'ancien widget de la grille (sauf l'overlay de chargement).
        for i in range(self._grid.count() - 1, -1, -1):
            item = self._grid.itemAt(i)
            if item and item.widget() is not None and item.widget() is not self._loading:
                w = item.widget()
                self._grid.removeWidget(w)
                w.setParent(None)

        # Créer le nouveau plot et l'insérer.
        self.plot = self._make_plot(self._sim_type, params)
        self._grid.addWidget(self.plot.widget, 0, 0)
        self._loading.raise_()
        self._loading.setVisible(True)

        # Préparer en arrière-plan.
        self._worker = _PrepareWorker(self.plot)
        self._worker.done.connect(self._on_ready)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()
        log.debug("LibreSimPage.reload_with_params — sim_type=%s", self._sim_type)
