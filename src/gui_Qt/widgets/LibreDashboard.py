"""Dashboard interactif pour le mode --libre.

Panneau bas (fixe 280 px) affiché sous la simulation en mode libre.
Trois colonnes séparées par des traits fins :
  1. LE MODÈLE   — titre, sous-titre, équation clé (cliquable → FormulaDialog),
                   trace d'orbite (QPainter)
  2. EN DIRECT   — jauge d'arc (QPainter), position XYZ, historique vitesse (QPainter)
  3. EXPLICATION — sélecteur de niveau (5 niveaux dont "extrêmes" et "comparaison"),
                   texte adapté, anecdote

Performance : la jauge et les labels X/Y/Z sont mis à jour à chaque frame ;
la trace d'orbite et la sparkline ne sont rafraîchies que toutes les 4 frames.

Classes
-------
_ArcGauge       Semi-circular speed gauge drawn with QPainter.
_OrbitTrace     Top-down trajectory miniature drawn with QPainter.
_Sparkline      Speed history polyline drawn with QPainter.
LibreInfoStrip  Main 3-column strip widget (public API).
LibreDashboard  Alias for LibreInfoStrip (backward compatibility).
"""
from __future__ import annotations

import logging
from collections import deque
from math import hypot, log10

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
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
    DASH_STRIP_H, DASH_THROTTLE,
    DASH_GAUGE_W, DASH_GAUGE_H, DASH_GAUGE_HUE_MAX, DASH_GAUGE_PEN_W,
    DASH_GAUGE_FS_NUM, DASH_GAUGE_FS_UNIT,
    DASH_ORBIT_SIZE, DASH_ORBIT_MAXLEN, DASH_ORBIT_ALPHA_LO, DASH_ORBIT_ALPHA_HI,
    DASH_ORBIT_PEN_W, DASH_ORBIT_DOT_R, DASH_ORBIT_ROW_MARGINS, DASH_ORBIT_SPACING,
    DASH_SPARK_H, DASH_SPARK_MAXLEN, DASH_SPARK_PEN_W, DASH_SPARK_YPAD,
    DASH_BTN_H, DASH_SCROLL_W,
    DASH_COL1_MIN_W, DASH_COL2_MIN_W,
    DASH_COL1_MARGINS, DASH_COL2_MARGINS, DASH_COL3_MARGINS,
    DASH_EQ_MARGINS, DASH_EQ_RADIUS, DASH_EQ_ALPHA,
    DASH_CARD_MARGINS, DASH_CARD_RADIUS, DASH_FACT_MARGINS, DASH_FACT_RADIUS,
    DASH_BTN_RADIUS, DASH_CARD_SPACING, DASH_BTN_ROW_SPACING, DASH_COL_SPACING,
    DASH_COL3_SPACING,
    DASH_FS_SECTION, DASH_FS_TITLE, DASH_FS_SUBTITLE, DASH_FS_EQ,
    DASH_FS_AXIS, DASH_FS_VALUE, DASH_FS_EXPL, DASH_FS_FACT_TITLE,
    DASH_FS_FACT_BODY, DASH_FS_BTN,
)
from utils.ui_strings import (
    DASH_SECTION_MODEL, DASH_SECTION_LIVE, DASH_SECTION_TRAJ,
    DASH_SECTION_SPEED, DASH_SECTION_EXPL,
    DASH_LEVELS, DASH_LEVEL_ICONS,
    DASH_GAUGE_UNIT, DASH_FACT_TITLE,
    DASH_LEVEL_EXTREME, DASH_LEVEL_COMPARE,
    DASH_ICON_EXTREME, DASH_ICON_COMPARE,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# _ArcGauge — demi-cercle QPainter
# ---------------------------------------------------------------------------

class _ArcGauge(QWidget):
    """Semi-circular speed gauge drawn with QPainter.

    The arc sweeps from the left (0) to the right (max) across the bottom
    half of the widget.  The fill colour transitions from green (slow) to
    red (fast) via HSV hue rotation.

    Parameters
    ----------
    accent : str
        Hex colour string (unused directly — kept for API symmetry).
    """

    def __init__(self, accent: str) -> None:
        """Initialise the gauge at zero speed."""
        super().__init__()
        self._speed  = 0.0
        self._max    = 1.0
        self._accent = accent
        self.setFixedSize(DASH_GAUGE_W, DASH_GAUGE_H)
        self.setStyleSheet("background: transparent;")

    def set_speed(self, speed: float, max_speed: float) -> None:
        """Update the displayed speed and trigger a repaint.

        Parameters
        ----------
        speed     : float — current speed [m/s].
        max_speed : float — maximum observed speed used to normalise the arc.
        """
        self._speed = max(speed, 0.0)
        self._max   = max(max_speed, 1e-9)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h   = self.width(), self.height()
        cx, cy = w / 2, h - 10
        r      = min(cx - 10, cy - 6)
        rect   = QRect(int(cx - r), int(cy - r), int(2 * r), int(2 * r))
        ratio  = min(self._speed / self._max, 1.0)

        # Arc de fond
        bg = QPen(QColor(_ss.CLR_GAUGE_TRACK), DASH_GAUGE_PEN_W)
        bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(bg)
        p.drawArc(rect, 180 * 16, -180 * 16)

        # Arc de valeur
        if ratio > 0.01:
            hue   = max(int(DASH_GAUGE_HUE_MAX * (1.0 - ratio)), 0)
            color = QColor.fromHsv(hue, 220, 200)
            val   = QPen(color, DASH_GAUGE_PEN_W)
            val.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(val)
            p.drawArc(rect, 180 * 16, -int(ratio * 180 * 16))

        # Valeur numérique
        hue_t = max(int(DASH_GAUGE_HUE_MAX * (1.0 - ratio)), 0)
        tc    = QColor.fromHsv(hue_t, 180, 200) if ratio > 0.05 else QColor(_ss.CLR_DIM)
        p.setPen(QPen(tc))
        p.setFont(QFont("Monospace", DASH_GAUGE_FS_NUM, QFont.Weight.Bold))
        p.drawText(
            QRect(int(cx - 40), int(cy - 34), 80, 24),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._speed:.3f}",
        )
        p.setPen(QPen(QColor(_ss.CLR_DIM)))
        p.setFont(QFont("sans-serif", DASH_GAUGE_FS_UNIT))
        p.drawText(
            QRect(int(cx - 16), int(cy - 12), 32, 12),
            Qt.AlignmentFlag.AlignCenter,
            DASH_GAUGE_UNIT,
        )


# ---------------------------------------------------------------------------
# _OrbitTrace — trace QPainter circulaire
# ---------------------------------------------------------------------------

class _OrbitTrace(QWidget):
    """Top-down trajectory miniature drawn with QPainter.

    Keeps a rolling deque of (x, y) positions and draws them as a fading
    polyline inside a circle background.  The most recent position is
    shown as a filled dot.

    Parameters
    ----------
    accent : str
        Hex colour string for the trail and dot.
    """

    def __init__(self, accent: str) -> None:
        """Initialise the orbit trace with an empty trail."""
        super().__init__()
        self._trail_x: deque[float] = deque(maxlen=DASH_ORBIT_MAXLEN)
        self._trail_y: deque[float] = deque(maxlen=DASH_ORBIT_MAXLEN)
        self._max_r   = 1e-9
        self._accent  = QColor(accent)
        self.setFixedSize(DASH_ORBIT_SIZE, DASH_ORBIT_SIZE)
        self.setStyleSheet("background: transparent;")

    def add_point(self, x: float, y: float) -> None:
        """Append a new (x, y) point and trigger a repaint.

        Parameters
        ----------
        x, y : float — Cartesian position in the simulation coordinate frame.
        """
        self._trail_x.append(x)
        self._trail_y.append(y)
        r = hypot(x, y)
        if r > self._max_r:
            self._max_r = r
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h   = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(cx, cy) - 4

        # Background circle
        p.setPen(QPen(QColor(_ss.CLR_MINI_BORDER), 1))
        p.setBrush(QBrush(QColor(_ss.CLR_MINI_BG)))
        p.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        p.setBrush(Qt.NoBrush)

        xs = list(self._trail_x)
        ys = list(self._trail_y)
        if len(xs) < 2:
            return

        scale = (radius - 6) / self._max_r
        n = len(xs)
        for i in range(1, n):
            alpha = max(DASH_ORBIT_ALPHA_LO, int(DASH_ORBIT_ALPHA_HI * i / n))
            c = QColor(self._accent)
            c.setAlpha(alpha)
            p.setPen(QPen(c, DASH_ORBIT_PEN_W))
            x1 = int(cx + xs[i - 1] * scale)
            y1 = int(cy - ys[i - 1] * scale)
            x2 = int(cx + xs[i] * scale)
            y2 = int(cy - ys[i] * scale)
            p.drawLine(x1, y1, x2, y2)

        # Current dot
        dot_x = int(cx + xs[-1] * scale)
        dot_y = int(cy - ys[-1] * scale)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(self._accent))
        p.drawEllipse(dot_x - DASH_ORBIT_DOT_R, dot_y - DASH_ORBIT_DOT_R, DASH_ORBIT_DOT_R * 2, DASH_ORBIT_DOT_R * 2)


# ---------------------------------------------------------------------------
# _Sparkline — historique vitesse QPainter
# ---------------------------------------------------------------------------

class _Sparkline(QWidget):
    """Speed-history polyline drawn with QPainter.

    Maintains a rolling deque of speed samples and draws them as a
    continuous polyline scaled to the widget height.

    Parameters
    ----------
    accent : str
        Hex colour string for the polyline.
    """

    def __init__(self, accent: str) -> None:
        """Initialise the sparkline with an empty data deque."""
        super().__init__()
        self._data: deque[float] = deque(maxlen=DASH_SPARK_MAXLEN)
        self._accent = QColor(accent)
        self.setFixedHeight(DASH_SPARK_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent;")

    def add_value(self, v: float) -> None:
        """Append a new speed sample and trigger a repaint.

        Parameters
        ----------
        v : float — speed [m/s].
        """
        self._data.append(v)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(_ss.CLR_MINI_BG))

        data = list(self._data)
        if len(data) < 2:
            return
        maxv = max(data) or 1e-9
        n    = len(data)
        pts  = []
        for i, v in enumerate(data):
            x = int(w * i / (n - 1))
            y = int(h - DASH_SPARK_YPAD - (h - DASH_SPARK_YPAD * 2) * v / maxv)
            pts.append(QPoint(x, y))

        pen = QPen(self._accent, DASH_SPARK_PEN_W)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        for i in range(1, len(pts)):
            p.drawLine(pts[i - 1], pts[i])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setStyleSheet(f"background: {_ss.CLR_BORDER}; border: none; max-width: 1px;")
    return f


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {_ss.CLR_DIM}; font-size: {DASH_FS_SECTION}px; font-weight: bold; "
        f"letter-spacing: 1.8px; background: transparent;"
    )
    return lbl


def _hsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background: {_ss.CLR_BORDER}; border: none; max-height: 1px;")
    return f


# ---------------------------------------------------------------------------
# LibreInfoStrip — panneau bas 3 colonnes
# ---------------------------------------------------------------------------

class LibreInfoStrip(QWidget):
    """Fixed-height (280 px) information strip displayed below a libre-mode simulation.

    Three columns separated by thin vertical rules:
    1. LE MODÈLE   — title, subtitle, clickable equation box (→ FormulaDialog),
                     orbit trace miniature.
    2. EN DIRECT   — arc speed gauge, X/Y/Z position cards, speed sparkline.
    3. EXPLICATION — five-level selector, explanation text, fun-fact box.

    Parameters
    ----------
    sim_type : str
        One of ``"2d_mcu"``, ``"3d_cone"``, ``"3d_membrane"``, ``"ml"``.
        Determines whether a Z position card is shown.
    content : dict
        The CONTENT entry for this simulation from ``utils.libre_config.CONTENT``.
    """

    def __init__(self, sim_type: str, content: dict) -> None:
        """Build the three-column strip for *sim_type*."""
        super().__init__()
        self._sim_type  = sim_type
        self._content   = content
        self._level     = "decouverte"
        self._accent    = content.get("color", "#5b8ff9")
        self._has_z     = sim_type in ("3d_cone", "3d_membrane")
        self._max_speed = 1e-9
        self._frame_ctr = 0

        self.setFixedHeight(DASH_STRIP_H)
        self.setStyleSheet(f"background-color: {_ss.CLR_PANEL_BG}; border-top: 1px solid {_ss.CLR_BORDER};")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_col1(), stretch=3)
        root.addWidget(_vsep())
        root.addWidget(self._build_col2(), stretch=2)
        root.addWidget(_vsep())
        root.addWidget(self._build_col3(), stretch=4)

    # ── Column 1: LE MODÈLE ───────────────────────────────────────────────

    def _build_col1(self) -> QWidget:
        """Build the left column: model title, subtitle, equation, orbit trace."""
        col = QWidget()
        col.setMinimumWidth(DASH_COL1_MIN_W)
        col.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(*DASH_COL1_MARGINS)
        lay.setSpacing(DASH_COL_SPACING)

        lay.addWidget(_section_label(DASH_SECTION_MODEL))

        title = QLabel(self._content["title"])
        title.setStyleSheet(
            f"color: {self._accent}; font-size: {DASH_FS_TITLE}px; font-weight: bold; background: transparent;"
        )
        title.setWordWrap(True)
        lay.addWidget(title)

        sub = QLabel(self._content["subtitle"])
        sub.setStyleSheet(f"color: {_ss.CLR_SUBTEXT}; font-size: {DASH_FS_SUBTITLE}px; background: transparent;")
        lay.addWidget(sub)

        # Equation box (clickable — opens FormulaDialog)
        eq_box = QWidget()
        eq_box.setStyleSheet(
            f"background: {_ss.CLR_BASE}; border: 1px solid {_ss.CLR_BORDER}; border-radius: {DASH_EQ_RADIUS}px;"
            f" cursor: pointer;"
        )
        eq_box.setCursor(Qt.CursorShape.PointingHandCursor)
        eq_lay = QVBoxLayout(eq_box)
        eq_lay.setContentsMargins(*DASH_EQ_MARGINS)

        hint_lbl = QLabel("🔍 cliquer pour les détails")
        hint_lbl.setStyleSheet(
            f"color: {_ss.CLR_DIM}; font-size: {DASH_FS_SECTION - 1}px; font-style: italic; background: transparent;"
        )
        eq_lay.addWidget(hint_lbl)

        eq_lbl = QLabel(self._content["key_equation"])
        eq_lbl.setStyleSheet(
            f"color: {self._accent}cc; font-family: Monospace; font-size: {DASH_FS_EQ}px; background: transparent;"
        )
        eq_lbl.setWordWrap(True)
        eq_lay.addWidget(eq_lbl)

        # Store reference so it can open dialog
        formula_details = self._content.get("formula_details", [])
        accent = self._accent
        eq_box.mousePressEvent = lambda e: self._open_formula_dialog(formula_details, accent)
        lay.addWidget(eq_box)

        # Orbit trace
        orbit_row = QWidget()
        orbit_row.setStyleSheet("background: transparent;")
        orbit_lay = QHBoxLayout(orbit_row)
        orbit_lay.setContentsMargins(*DASH_ORBIT_ROW_MARGINS)
        orbit_lay.setSpacing(DASH_ORBIT_SPACING)
        self._orbit = _OrbitTrace(_ss.CLR_ACCENT)
        orbit_lay.addWidget(self._orbit)
        orbit_info = QVBoxLayout()
        orbit_info.setSpacing(2)
        orbit_info.addWidget(_section_label(DASH_SECTION_TRAJ))
        orbit_info.addStretch()
        orbit_lay.addLayout(orbit_info)
        lay.addWidget(orbit_row)

        lay.addStretch()
        return col

    # ── Column 2: EN DIRECT ───────────────────────────────────────────────

    def _build_col2(self) -> QWidget:
        """Build the centre column: arc gauge, XYZ cards, speed sparkline."""
        col = QWidget()
        col.setMinimumWidth(DASH_COL2_MIN_W)
        col.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(*DASH_COL2_MARGINS)
        lay.setSpacing(DASH_COL_SPACING)

        lay.addWidget(_section_label(DASH_SECTION_LIVE))

        # Arc gauge (centered)
        self._gauge = _ArcGauge(self._accent)
        gauge_row = QWidget()
        gauge_row.setStyleSheet("background: transparent;")
        gr_lay = QHBoxLayout(gauge_row)
        gr_lay.setContentsMargins(0, 0, 0, 0)
        gr_lay.addWidget(self._gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(gauge_row)

        # XYZ position cards
        pos_row = QWidget()
        pos_row.setStyleSheet("background: transparent;")
        prl = QHBoxLayout(pos_row)
        prl.setContentsMargins(0, 0, 0, 0)
        prl.setSpacing(DASH_CARD_SPACING)
        self._pos: dict[str, QLabel] = {}
        for axis in ("X", "Y", "Z"):
            card = QWidget()
            card.setStyleSheet(
                f"background: {_ss.CLR_SURFACE0}; border-radius: {DASH_CARD_RADIUS}px; border: 1px solid {_ss.CLR_BORDER};"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(*DASH_CARD_MARGINS)
            cl.setSpacing(1)
            a_lbl = QLabel(axis)
            a_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            a_lbl.setStyleSheet(
                f"color: {_ss.CLR_DIM}; font-size: {DASH_FS_AXIS}px; font-weight: bold; background: transparent;"
            )
            v_lbl = QLabel("—")
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_lbl.setStyleSheet(
                f"color: {_ss.CLR_TEXT}; font-family: Monospace; font-size: {DASH_FS_VALUE}px; background: transparent;"
            )
            cl.addWidget(a_lbl)
            cl.addWidget(v_lbl)
            self._pos[axis] = v_lbl
            prl.addWidget(card)
        lay.addWidget(pos_row)

        lay.addWidget(_section_label(DASH_SECTION_SPEED))
        self._sparkline = _Sparkline(_ss.CLR_ACCENT)
        lay.addWidget(self._sparkline)

        lay.addStretch()
        return col

    # ── Column 3: EXPLICATION ─────────────────────────────────────────────

    def _build_col3(self) -> QWidget:
        """Build the right column: 5-level selector, explanation text, fun-fact."""
        col = QWidget()
        col.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(*DASH_COL3_MARGINS)
        lay.setSpacing(DASH_COL3_SPACING)

        lay.addWidget(_section_label(DASH_SECTION_EXPL))

        # Level selector
        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(DASH_BTN_ROW_SPACING)

        self._btns: dict[str, QPushButton] = {}
        all_levels = list(DASH_LEVELS) + [DASH_LEVEL_EXTREME, DASH_LEVEL_COMPARE]
        all_icons  = list(DASH_LEVEL_ICONS) + [DASH_ICON_EXTREME, DASH_ICON_COMPARE]
        for key, icon in zip(all_levels, all_icons):
            btn = QPushButton(icon)
            btn.setCheckable(True)
            btn.setChecked(key == self._level)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(DASH_BTN_H)
            btn.clicked.connect(lambda _, k=key: self._set_level(k))
            self._btns[key] = btn
            br.addWidget(btn)
        self._refresh_btn_styles()
        lay.addWidget(btn_row)

        lay.addWidget(_hsep())

        # Explanation text (in a scroll area)
        self._expl = QLabel(self._content["levels"][self._level])
        self._expl.setWordWrap(True)
        self._expl.setStyleSheet(
            f"color: {_ss.CLR_TEXT}; font-size: {DASH_FS_EXPL}px; background: transparent; line-height: 1.5;"
        )
        self._expl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._expl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        scroll = QScrollArea()
        scroll.setWidget(self._expl)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ width: {DASH_SCROLL_W}px; background: transparent; }}"
            f"QScrollBar::handle:vertical {{ background: {_ss.CLR_SURFACE2}; border-radius: 1px; }}"
        )
        lay.addWidget(scroll, stretch=1)

        lay.addWidget(_hsep())

        # Fun fact box
        fact_box = QWidget()
        fact_box.setStyleSheet(f"background: {_ss.CLR_SURFACE0}; border-radius: {DASH_FACT_RADIUS}px;")
        fl = QVBoxLayout(fact_box)
        fl.setContentsMargins(*DASH_FACT_MARGINS)
        fl.setSpacing(4)
        ft = QLabel(DASH_FACT_TITLE)
        ft.setStyleSheet(
            f"color: #fbbf24; font-size: {DASH_FS_FACT_TITLE}px; font-weight: bold; background: transparent;"
        )
        fl.addWidget(ft)
        fb = QLabel(self._content["fun_fact"])
        fb.setWordWrap(True)
        fb.setStyleSheet(
            f"color: {_ss.CLR_SUBTEXT}; font-size: {DASH_FS_FACT_BODY}px; font-style: italic; background: transparent;"
        )
        fl.addWidget(fb)
        lay.addWidget(fact_box)

        return col

    # ── Level management ──────────────────────────────────────────────────

    def _set_level(self, level: str) -> None:
        """Switch the explanation text to the selected level.

        Handles both the three standard levels stored under ``content["levels"]``
        and the two extra top-level keys ``"extreme"`` and ``"compare"``.

        Parameters
        ----------
        level : str
            One of ``"decouverte"``, ``"lycee"``, ``"avance"``,
            ``"extreme"``, or ``"compare"``.
        """
        self._level = level
        levels = self._content.get("levels", {})
        if level in levels:
            text = levels[level]
        else:
            # extreme / compare stored as top-level keys
            text = self._content.get(level, "—")
        self._expl.setText(text)
        for k, btn in self._btns.items():
            btn.setChecked(k == level)
        self._refresh_btn_styles()

    def _refresh_btn_styles(self) -> None:
        """Reapply stylesheets to all level buttons based on their checked state."""
        for key, btn in self._btns.items():
            c = _ss.CLR_ACCENT
            if btn.isChecked():
                btn.setStyleSheet(
                    f"QPushButton {{ background: {c}22; color: {c}; "
                    f"font-size: {DASH_FS_BTN}px; font-weight: bold; border-radius: {DASH_BTN_RADIUS}px; "
                    f"border: 1px solid {c}; padding: 2px 4px; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {_ss.CLR_DIM}; "
                    f"font-size: {DASH_FS_BTN}px; border-radius: {DASH_BTN_RADIUS}px; border: 1px solid {_ss.CLR_BORDER}; padding: 2px 4px; }}"
                    f"QPushButton:hover {{ color: {c}; border-color: {c}44; }}"
                )

    def _open_formula_dialog(self, formula_details: list, accent: str) -> None:
        """Open the formula detail popup dialog."""
        from widgets.FormulaDialog import FormulaDialog
        dlg = FormulaDialog(formula_details, accent, parent=self)
        dlg.exec()

    # ── Live data update ──────────────────────────────────────────────────

    def update_data(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        z: float | None = None,
    ) -> None:
        """Receive a new data point and update all live indicators.

        Called every animation frame by the parent SimWidget.
        Heavy widgets (orbit trace, sparkline) are throttled to every
        ``DASH_THROTTLE`` frames.

        Parameters
        ----------
        x, y   : float — current position [m].
        vx, vy : float — current velocity components [m/s].
        z      : float | None — current z position [m] for 3-D sims; None for 2-D.
        """
        speed = hypot(vx, vy)
        self._max_speed = max(self._max_speed, speed)
        self._frame_ctr += 1

        # Every frame (fast path)
        self._gauge.set_speed(speed, self._max_speed)
        self._pos["X"].setText(f"{x:.3f}")
        self._pos["Y"].setText(f"{y:.3f}")
        self._pos["Z"].setText(f"{z:.3f}" if z is not None else "—")

        # Throttled (every DASH_THROTTLE frames)
        if self._frame_ctr % DASH_THROTTLE == 0:
            self._orbit.add_point(x, y)
            self._sparkline.add_value(speed)


# Alias for backward compatibility
LibreDashboard = LibreInfoStrip
