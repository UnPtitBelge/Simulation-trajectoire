"""Dashboard interactif pour le mode --libre.

Panneau bas (fixe 280 px) affiché sous la simulation en mode libre.
Trois colonnes séparées par des traits fins :
  1. LE MODÈLE   — titre, sous-titre, équation clé, trace d'orbite (QPainter)
  2. EN DIRECT   — jauge d'arc (QPainter), position XYZ, historique vitesse (QPainter)
  3. EXPLICATION — sélecteur de niveau, texte adapté, anecdote

Performance : la jauge et les labels X/Y/Z sont mis à jour à chaque frame ;
la trace d'orbite et la sparkline ne sont rafraîchies que toutes les 4 frames.
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

log = logging.getLogger(__name__)

_LEVELS      = ["decouverte", "lycee", "avance"]
_LEVEL_ICONS = ["🔍 Découverte", "📐 Lycée", "∑ Avancé"]
_STRIP_HEIGHT = 280

# Throttle factor for orbit/sparkline redraws
_THROTTLE = 4


# ---------------------------------------------------------------------------
# _ArcGauge — demi-cercle QPainter
# ---------------------------------------------------------------------------

class _ArcGauge(QWidget):
    """Jauge de vitesse en demi-cercle dessinée avec QPainter."""

    def __init__(self, accent: str) -> None:
        super().__init__()
        self._speed  = 0.0
        self._max    = 1.0
        self._accent = accent
        self.setFixedSize(160, 88)
        self.setStyleSheet("background: transparent;")

    def set_speed(self, speed: float, max_speed: float) -> None:
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
        bg = QPen(QColor("#1a1d2e"), 8)
        bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(bg)
        p.drawArc(rect, 180 * 16, -180 * 16)

        # Arc de valeur
        if ratio > 0.01:
            hue   = max(int(120 * (1.0 - ratio)), 0)
            color = QColor.fromHsv(hue, 220, 200)
            val   = QPen(color, 8)
            val.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(val)
            p.drawArc(rect, 180 * 16, -int(ratio * 180 * 16))

        # Valeur numérique
        hue_t = max(int(120 * (1.0 - ratio)), 0)
        tc    = QColor.fromHsv(hue_t, 180, 200) if ratio > 0.05 else QColor("#4f5472")
        p.setPen(QPen(tc))
        p.setFont(QFont("Monospace", 12, QFont.Weight.Bold))
        p.drawText(
            QRect(int(cx - 40), int(cy - 34), 80, 24),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._speed:.3f}",
        )
        p.setPen(QPen(QColor("#4f5472")))
        p.setFont(QFont("sans-serif", 7))
        p.drawText(
            QRect(int(cx - 16), int(cy - 12), 32, 12),
            Qt.AlignmentFlag.AlignCenter,
            "m/s",
        )


# ---------------------------------------------------------------------------
# _OrbitTrace — trace QPainter circulaire
# ---------------------------------------------------------------------------

class _OrbitTrace(QWidget):
    """Miniature de la trajectoire vue de dessus, dessinée avec QPainter."""

    def __init__(self, accent: str) -> None:
        super().__init__()
        self._trail_x: deque[float] = deque(maxlen=300)
        self._trail_y: deque[float] = deque(maxlen=300)
        self._max_r   = 1e-9
        self._accent  = QColor(accent)
        self.setFixedSize(100, 100)
        self.setStyleSheet("background: transparent;")

    def add_point(self, x: float, y: float) -> None:
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
        p.setPen(QPen(QColor("#1a1d2e"), 1))
        p.setBrush(QBrush(QColor("#070810")))
        p.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        p.setBrush(Qt.NoBrush)

        xs = list(self._trail_x)
        ys = list(self._trail_y)
        if len(xs) < 2:
            return

        scale = (radius - 6) / self._max_r
        n = len(xs)
        for i in range(1, n):
            alpha = max(30, int(220 * i / n))
            c = QColor(self._accent)
            c.setAlpha(alpha)
            p.setPen(QPen(c, 1.2))
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
        p.drawEllipse(dot_x - 4, dot_y - 4, 8, 8)


# ---------------------------------------------------------------------------
# _Sparkline — historique vitesse QPainter
# ---------------------------------------------------------------------------

class _Sparkline(QWidget):
    """Polyline de vitesse dessinée avec QPainter."""

    def __init__(self, accent: str) -> None:
        super().__init__()
        self._data: deque[float] = deque(maxlen=80)
        self._accent = QColor(accent)
        self.setFixedHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent;")

    def add_value(self, v: float) -> None:
        self._data.append(v)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#070810"))

        data = list(self._data)
        if len(data) < 2:
            return
        maxv = max(data) or 1e-9
        n    = len(data)
        pts  = []
        for i, v in enumerate(data):
            x = int(w * i / (n - 1))
            y = int(h - 3 - (h - 6) * v / maxv)
            pts.append(QPoint(x, y))

        pen = QPen(self._accent, 1.5)
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
    f.setStyleSheet("background: #232640; border: none; max-width: 1px;")
    return f


def _section_label(text: str, color: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {color}; font-size: 9px; font-weight: bold; "
        f"letter-spacing: 1.8px; background: transparent;"
    )
    return lbl


def _hsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background: #232640; border: none; max-height: 1px;")
    return f


# ---------------------------------------------------------------------------
# LibreInfoStrip — panneau bas 3 colonnes
# ---------------------------------------------------------------------------

class LibreInfoStrip(QWidget):
    """Panneau bas fixe (280 px) affiché sous la simulation en mode libre."""

    def __init__(self, sim_type: str, content: dict) -> None:
        super().__init__()
        self._sim_type  = sim_type
        self._content   = content
        self._level     = "decouverte"
        self._accent    = content.get("color", "#5b8ff9")
        self._has_z     = sim_type in ("3d_cone", "3d_membrane")
        self._max_speed = 1e-9
        self._frame_ctr = 0

        self.setFixedHeight(_STRIP_HEIGHT)
        self.setStyleSheet(f"background-color: #131520; border-top: 1px solid #232640;")

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
        col = QWidget()
        col.setMinimumWidth(240)
        col.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(16, 12, 12, 12)
        lay.setSpacing(6)

        lay.addWidget(_section_label("LE MODÈLE", self._accent))

        title = QLabel(self._content["title"])
        title.setStyleSheet(
            f"color: {self._accent}; font-size: 16px; font-weight: bold; background: transparent;"
        )
        title.setWordWrap(True)
        lay.addWidget(title)

        sub = QLabel(self._content["subtitle"])
        sub.setStyleSheet("color: #8890b0; font-size: 11px; background: transparent;")
        lay.addWidget(sub)

        # Equation box
        eq_box = QWidget()
        eq_box.setStyleSheet(
            f"background: #0e0f15; border: 1px solid {self._accent}44; border-radius: 5px;"
        )
        eq_lay = QVBoxLayout(eq_box)
        eq_lay.setContentsMargins(10, 6, 10, 6)
        eq_lbl = QLabel(self._content["key_equation"])
        eq_lbl.setStyleSheet(
            f"color: {self._accent}cc; font-family: Monospace; font-size: 11px; background: transparent;"
        )
        eq_lbl.setWordWrap(True)
        eq_lay.addWidget(eq_lbl)
        lay.addWidget(eq_box)

        # Orbit trace
        orbit_row = QWidget()
        orbit_row.setStyleSheet("background: transparent;")
        orbit_lay = QHBoxLayout(orbit_row)
        orbit_lay.setContentsMargins(0, 4, 0, 0)
        orbit_lay.setSpacing(8)
        self._orbit = _OrbitTrace(self._accent)
        orbit_lay.addWidget(self._orbit)
        orbit_info = QVBoxLayout()
        orbit_info.setSpacing(2)
        orbit_info.addWidget(_section_label("TRAJECTOIRE", self._accent))
        orbit_info.addStretch()
        orbit_lay.addLayout(orbit_info)
        lay.addWidget(orbit_row)

        lay.addStretch()
        return col

    # ── Column 2: EN DIRECT ───────────────────────────────────────────────

    def _build_col2(self) -> QWidget:
        col = QWidget()
        col.setMinimumWidth(180)
        col.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(6)

        lay.addWidget(_section_label("EN DIRECT", self._accent))

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
        prl.setSpacing(4)
        self._pos: dict[str, QLabel] = {}
        for axis in ("X", "Y", "Z"):
            card = QWidget()
            card.setStyleSheet(
                "background: #1f2235; border-radius: 4px; border: 1px solid #232640;"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(6, 4, 6, 4)
            cl.setSpacing(1)
            a_lbl = QLabel(axis)
            a_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            a_lbl.setStyleSheet(
                "color: #4f5472; font-size: 8px; font-weight: bold; background: transparent;"
            )
            v_lbl = QLabel("—")
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_lbl.setStyleSheet(
                "color: #dde1f0; font-family: Monospace; font-size: 11px; background: transparent;"
            )
            cl.addWidget(a_lbl)
            cl.addWidget(v_lbl)
            self._pos[axis] = v_lbl
            prl.addWidget(card)
        lay.addWidget(pos_row)

        lay.addWidget(_section_label("VITESSE", self._accent))
        self._sparkline = _Sparkline(self._accent)
        lay.addWidget(self._sparkline)

        lay.addStretch()
        return col

    # ── Column 3: EXPLICATION ─────────────────────────────────────────────

    def _build_col3(self) -> QWidget:
        col = QWidget()
        col.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(12, 12, 16, 12)
        lay.setSpacing(8)

        lay.addWidget(_section_label("EXPLICATION", self._accent))

        # Level selector
        btn_row = QWidget()
        btn_row.setStyleSheet("background: transparent;")
        br = QHBoxLayout(btn_row)
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(5)

        self._btns: dict[str, QPushButton] = {}
        for key, icon in zip(_LEVELS, _LEVEL_ICONS):
            btn = QPushButton(icon)
            btn.setCheckable(True)
            btn.setChecked(key == self._level)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(28)
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
            "color: #b8bcd0; font-size: 12px; background: transparent; line-height: 1.5;"
        )
        self._expl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._expl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        scroll = QScrollArea()
        scroll.setWidget(self._expl)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { width: 3px; background: transparent; }"
            "QScrollBar::handle:vertical { background: #363b58; border-radius: 1px; }"
        )
        lay.addWidget(scroll, stretch=1)

        lay.addWidget(_hsep())

        # Fun fact box
        fact_box = QWidget()
        fact_box.setStyleSheet("background: #1f2235; border-radius: 5px;")
        fl = QVBoxLayout(fact_box)
        fl.setContentsMargins(10, 8, 10, 8)
        fl.setSpacing(4)
        ft = QLabel("💡  Le savais-tu ?")
        ft.setStyleSheet(
            "color: #fbbf24; font-size: 10px; font-weight: bold; background: transparent;"
        )
        fl.addWidget(ft)
        fb = QLabel(self._content["fun_fact"])
        fb.setWordWrap(True)
        fb.setStyleSheet(
            "color: #8890b0; font-size: 11px; font-style: italic; background: transparent;"
        )
        fl.addWidget(fb)
        lay.addWidget(fact_box)

        return col

    # ── Level management ──────────────────────────────────────────────────

    def _set_level(self, level: str) -> None:
        self._level = level
        self._expl.setText(self._content["levels"][level])
        for k, btn in self._btns.items():
            btn.setChecked(k == level)
        self._refresh_btn_styles()

    def _refresh_btn_styles(self) -> None:
        colors = {"decouverte": "#06d6a0", "lycee": "#5b8ff9", "avance": "#ef476f"}
        for key, btn in self._btns.items():
            c = colors[key]
            if btn.isChecked():
                btn.setStyleSheet(
                    f"QPushButton {{ background: {c}22; color: {c}; "
                    f"font-size: 10px; font-weight: bold; border-radius: 4px; "
                    f"border: 1px solid {c}; padding: 2px 4px; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: #4f5472; "
                    f"font-size: 10px; border-radius: 4px; border: 1px solid #232640; padding: 2px 4px; }}"
                    f"QPushButton:hover {{ color: {c}; border-color: {c}44; }}"
                )

    # ── Live data update ──────────────────────────────────────────────────

    def update_data(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        z: float | None = None,
    ) -> None:
        speed = hypot(vx, vy)
        self._max_speed = max(self._max_speed, speed)
        self._frame_ctr += 1

        # Every frame (fast path)
        self._gauge.set_speed(speed, self._max_speed)
        self._pos["X"].setText(f"{x:.3f}")
        self._pos["Y"].setText(f"{y:.3f}")
        self._pos["Z"].setText(f"{z:.3f}" if z is not None else "—")

        # Throttled (every _THROTTLE frames)
        if self._frame_ctr % _THROTTLE == 0:
            self._orbit.add_point(x, y)
            self._sparkline.add_value(speed)


# Alias for backward compatibility
LibreDashboard = LibreInfoStrip
