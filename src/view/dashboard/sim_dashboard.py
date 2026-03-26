"""Dashboard sandbox pour le mode libre — layout 4 panneaux.

Structure :
  ┌─[topbar: titre + bouton retour]──────────────────────────────────────┐
  │ ┌─[gauche: 300px fixe]─────────┬─[droite: flexible]─────────────────┐ │
  │ │ haut-gauche: paramètres      │ haut-droite: simulation            │ │
  │ │ (scroll, stretch=2)          │ (stretch=7)                        │ │
  │ ├──────────────────────────────┤────────────────────────────────────┤ │
  │ │ bas-gauche: info + glossaire │ bas-droite: graphes temps réel     │ │
  │ │ (scroll, stretch=3)          │ (hauteur fixe 200px)               │ │
  │ └──────────────────────────────┴────────────────────────────────────┘ │
  │ [▶ Lecture] [⏸ Pause] [↺ Reset] | Vitesse x1.0 ──● | [F1] [F2] [F3] │
  └────────────────────────────────────────────────────────────────────────┘
"""

import re

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.core.content import GLOSSARY, SIM
from src.ui.ui_helpers import build_preset_buttons
from src.utils.theme import (
    BADGE_RADIUS,
    BLOCK_PADDING,
    CLR_BG,
    CLR_BORDER,
    CLR_DANGER,
    CLR_PLOT_BG,
    CLR_PRIMARY,
    CLR_PRIMARY_DARK,
    CLR_PRIMARY_LIGHT,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_TEXT,
    CLR_TEXT_SECONDARY,
    DASH_CHARTS_H,
    DASH_LEFT_W,
    FS_MD,
    FS_SM,
    FS_XS,
    SLIDER_GROOVE_H,
    SLIDER_GROOVE_RADIUS,
    SLIDER_H,
    SLIDER_HANDLE_MARGIN,
    SLIDER_HANDLE_RADIUS,
    SLIDER_HANDLE_SIZE,
    TAG_RADIUS,
    VSEP_H,
)

_SLIDER_STEPS = 200
_DEBOUNCE_MS = 300
_CHART_MAX_POINTS = 400

# ─── Vitesse de simulation ────────────────────────────────────────────────────
SPEED_STEPS = [0.25, 0.5, 1.0, 1.5, 2.0]
SPEED_LABELS = ["×0.25", "×0.5", "×1", "×1.5", "×2"]


# ─── Helpers sliders params ───────────────────────────────────────────────────

def _to_slider(val: float, spec: dict) -> int:
    lo, hi = spec["min"], spec["max"]
    return round((val - lo) / (hi - lo) * _SLIDER_STEPS)


def _from_slider(pos: int, spec: dict) -> float:
    lo, hi = spec["min"], spec["max"]
    raw = lo + pos / _SLIDER_STEPS * (hi - lo)
    step = spec["step"]
    return round(round(raw / step) * step, 10)


def _fmt(val: float, spec: dict) -> str:
    decimals = max(0, -int(f"{spec['step']:e}".split("e")[1]))
    return f"{val:.{decimals}f}"


# ─── Popup glossaire ──────────────────────────────────────────────────────────

def _show_glossary_popup(term: str, parent: QWidget) -> None:
    definition = GLOSSARY.get(term, "")
    if not definition:
        return
    dlg = QDialog(parent)
    dlg.setWindowTitle(term.capitalize())
    dlg.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
    dlg.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    dlg.setStyleSheet(
        f"QDialog {{ background: {CLR_SURFACE}; border: 1px solid {CLR_PRIMARY}; "
        f"border-radius: {BADGE_RADIUS}; padding: 0; }}"
    )
    dlg.setFixedWidth(300)

    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(6)

    hdr = QLabel(f"<b style='color:{CLR_PRIMARY_DARK}'>{term.capitalize()}</b>")
    hdr.setStyleSheet(f"font-size: {FS_SM};")
    lay.addWidget(hdr)

    body = QLabel(definition)
    body.setWordWrap(True)
    body.setStyleSheet(
        f"font-size: {FS_XS}; color: {CLR_TEXT};"
    )
    lay.addWidget(body)

    close_btn = QPushButton("Fermer")
    close_btn.setProperty("flat", True)
    close_btn.setStyleSheet(f"font-size: {FS_XS}; color: {CLR_TEXT_SECONDARY};")
    close_btn.clicked.connect(dlg.close)
    lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    dlg.adjustSize()
    # Centrer sur le parent
    pos = parent.mapToGlobal(parent.rect().center())
    dlg.move(pos.x() - dlg.width() // 2, pos.y() - dlg.height() // 2)
    dlg.show()


def _apply_glossary_html(text: str) -> str:
    """Entoure les termes du glossaire avec des balises <a> cliquables."""
    terms = sorted(GLOSSARY.keys(), key=len, reverse=True)
    result = text
    for term in terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        replacement = f"<a href='#{term}' style='color:{CLR_PRIMARY}; text-decoration:underline dotted;'>{term}</a>"
        # Ne remplacer que la première occurrence pour ne pas surcharger
        result = pattern.sub(replacement, result, count=1)
    return result.replace("\n", "<br>")


# ─── Panneau haut-gauche : sliders paramètres ─────────────────────────────────

class _ParamsPanel(QWidget):
    """Sliders de paramètres pour la simulation."""

    def __init__(self, plot, parent=None):
        super().__init__(parent)
        self._plot = plot
        self._sliders: dict[str, QSlider] = {}
        self._val_labels: dict[str, QLabel] = {}

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._apply)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 10)
        lay.setSpacing(8)

        header_row = QHBoxLayout()
        title = QLabel("⚙ Paramètres")
        title.setStyleSheet(
            f"font-size: {FS_SM}; font-weight: 600; color: {CLR_PRIMARY_DARK};"
        )
        header_row.addWidget(title, stretch=1)
        self._status = QLabel("✓")
        self._status.setStyleSheet(
            f"font-size: {FS_XS}; color: {CLR_SUCCESS}; font-weight: 500;"
        )
        header_row.addWidget(self._status)
        lay.addLayout(header_row)

        params = plot.params
        ranges = type(params).PARAM_RANGES if params else {}

        if not ranges:
            lbl = QLabel("Aucun paramètre ajustable.")
            lbl.setStyleSheet(f"color: {CLR_TEXT_SECONDARY}; font-size: {FS_XS};")
            lay.addWidget(lbl)
        else:
            for field, spec in ranges.items():
                # Skip non-continuous parameters (discrete, bool) that can't be sliders
                if "min" not in spec:
                    continue
                val = getattr(params, field, spec["min"])
                lay.addWidget(self._make_row(field, spec, val))

        lay.addStretch()
        plot.setup_done.connect(self._sync)

    def _make_row(self, field: str, spec: dict, value: float) -> QWidget:
        w = QWidget()
        wlay = QVBoxLayout(w)
        wlay.setContentsMargins(0, 0, 0, 0)
        wlay.setSpacing(2)

        label_row = QHBoxLayout()
        name = QLabel(spec["label"])
        name.setStyleSheet(f"font-size: {FS_XS}; font-weight: 500;")
        label_row.addWidget(name, stretch=1)
        val_lbl = QLabel(_fmt(value, spec))
        val_lbl.setStyleSheet(
            f"font-size: {FS_XS}; color: {CLR_PRIMARY}; font-family: monospace; font-weight: 600;"
        )
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_row.addWidget(val_lbl)
        wlay.addLayout(label_row)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, _SLIDER_STEPS)
        slider.setValue(_to_slider(value, spec))
        slider.setFixedHeight(SLIDER_H)
        slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ height: {SLIDER_GROOVE_H}; background: {CLR_BORDER}; border-radius: {SLIDER_GROOVE_RADIUS}; }}"
            f"QSlider::handle:horizontal {{ width: {SLIDER_HANDLE_SIZE}; height: {SLIDER_HANDLE_SIZE}; margin: {SLIDER_HANDLE_MARGIN}; "
            f"background: {CLR_PRIMARY}; border-radius: {SLIDER_HANDLE_RADIUS}; }}"
            f"QSlider::sub-page:horizontal {{ background: {CLR_PRIMARY}; border-radius: {SLIDER_GROOVE_RADIUS}; }}"
        )
        slider.valueChanged.connect(
            lambda pos, f=field, s=spec, lbl=val_lbl: self._on_slider(f, s, pos, lbl)
        )
        wlay.addWidget(slider)

        self._sliders[field] = slider
        self._val_labels[field] = val_lbl
        return w

    def _on_slider(self, field: str, spec: dict, pos: int, lbl: QLabel) -> None:
        lbl.setText(_fmt(_from_slider(pos, spec), spec))
        self._status.setText("…")
        self._status.setStyleSheet(f"font-size: {FS_XS}; color: {CLR_TEXT_SECONDARY};")
        self._debounce.start()

    def _apply(self) -> None:
        if self._plot.params is None:
            return
        params = self._plot.params
        for field, spec in type(params).PARAM_RANGES.items():
            if field in self._sliders:
                setattr(params, field, _from_slider(self._sliders[field].value(), spec))
        self._plot.setup()

    def _sync(self) -> None:
        if self._plot.params is None:
            return
        params = self._plot.params
        for field, spec in type(params).PARAM_RANGES.items():
            if field not in self._sliders:
                continue
            val = getattr(params, field, spec["min"])
            self._sliders[field].blockSignals(True)
            self._sliders[field].setValue(_to_slider(val, spec))
            self._sliders[field].blockSignals(False)
            self._val_labels[field].setText(_fmt(val, spec))
        self._status.setText("✓")
        self._status.setStyleSheet(
            f"font-size: {FS_XS}; color: {CLR_SUCCESS}; font-weight: 500;"
        )


# ─── Panneau bas-gauche : infos + glossaire ───────────────────────────────────

class _InfoPanel(QWidget):
    """Texte informatif avec mots du glossaire cliquables."""

    def __init__(self, sim_key: str, parent=None):
        super().__init__(parent)
        info = SIM.get(sim_key, {})

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {CLR_BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"background: {CLR_BG};")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(14, 10, 14, 14)
        lay.setSpacing(10)

        # En-tête avec équations
        eq_text = info.get("equations", "")
        if eq_text:
            eq_hdr = QLabel("📐 Équations")
            eq_hdr.setStyleSheet(
                f"font-size: {FS_XS}; font-weight: 600; color: {CLR_PRIMARY_DARK};"
            )
            lay.addWidget(eq_hdr)
            eq = QLabel(eq_text)
            eq.setWordWrap(True)
            eq.setStyleSheet(
                f"font-family: 'Courier New', monospace; font-size: {FS_XS}; "
                f"color: {CLR_PRIMARY}; background: {CLR_PRIMARY_LIGHT}; "
                f"padding: {BLOCK_PADDING}; border-radius: {TAG_RADIUS};"
            )
            lay.addWidget(eq)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {CLR_BORDER};")
        lay.addWidget(sep)

        # Texte pédagogique avec glossaire cliquable
        info_hdr = QLabel("💡 À comprendre")
        info_hdr.setStyleSheet(
            f"font-size: {FS_XS}; font-weight: 600; color: {CLR_PRIMARY_DARK};"
        )
        lay.addWidget(info_hdr)

        text_raw = info.get("beginner", info.get("intermediate", ""))
        if text_raw:
            html_text = _apply_glossary_html(text_raw)
            text_lbl = QLabel(html_text)
            text_lbl.setWordWrap(True)
            text_lbl.setTextFormat(Qt.TextFormat.RichText)
            text_lbl.setOpenExternalLinks(False)
            text_lbl.setStyleSheet(
                f"font-size: {FS_XS}; color: {CLR_TEXT}; line-height: 1.5;"
            )
            text_lbl.linkActivated.connect(
                lambda href, p=self: _show_glossary_popup(href.lstrip("#"), p)
            )
            lay.addWidget(text_lbl)

        hint = QLabel(
            f"<i style='color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};'>"
            "Les termes <u style='text-decoration:underline dotted;'>soulignés</u> "
            "ont une définition — cliquez pour l'afficher."
            "</i>"
        )
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setWordWrap(True)
        lay.addWidget(hint)

        lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)


# ─── Panneau bas-droite : graphes temps réel ──────────────────────────────────

class _LiveChartsPanel(QWidget):
    """Graphes en temps réel : r(t) avec curseur + métrique live."""

    def __init__(self, plot, parent=None):
        super().__init__(parent)
        self._plot = plot
        self._buffers: dict[str, list] = {}
        self._t_buffer: list = []
        self._curves: dict[str, pg.PlotDataItem] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(4)

        schema = plot.get_metrics_schema()

        # ── Graphe 1 : r(t) précalculé avec curseur de lecture ────────────────
        self._pw1 = pg.PlotWidget()
        self._pw1.setBackground(CLR_PLOT_BG)
        self._pw1.setLabel("left", "r", units="m", color=CLR_PRIMARY)
        self._pw1.getAxis("bottom").hide()
        self._pw1.showGrid(x=False, y=True, alpha=0.15)
        self._pw1.setMenuEnabled(False)
        self._pw1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._cursor = pg.InfiniteLine(
            pos=0, angle=90,
            pen=pg.mkPen(CLR_DANGER, width=1, style=Qt.PenStyle.DashLine),
        )
        self._chart_data: dict | None = None
        lay.addWidget(self._pw1, stretch=1)

        # ── Graphe 2 : première métrique temps réel ───────────────────────────
        self._pw2: pg.PlotWidget | None = None
        self._live_key: str | None = None
        self._live_label: str = ""

        if schema:
            first = schema[0]
            self._live_key = str(first["key"])
            self._live_label = first.get("label", first["key"])
            self._live_unit = first.get("unit", "")
            self._live_color = first.get("color", CLR_PRIMARY)

            self._pw2 = pg.PlotWidget()
            self._pw2.setBackground(CLR_PLOT_BG)
            self._pw2.setLabel(
                "left", self._live_label,
                units=self._live_unit,
                color=self._live_color,
            )
            self._pw2.getAxis("bottom").hide()
            self._pw2.showGrid(x=False, y=True, alpha=0.15)
            self._pw2.setMenuEnabled(False)
            self._pw2.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self._live_curve = self._pw2.plot(
                [], [], pen=pg.mkPen(self._live_color, width=2)
            )
            self._buffers[self._live_key] = []
            self._t_buffer = []
            lay.addWidget(self._pw2, stretch=1)

        plot.setup_done.connect(self._on_setup_done)
        plot.frame_updated.connect(self._on_frame)
        self._on_setup_done()

    def _on_setup_done(self) -> None:
        data = self._plot.get_chart_data()
        self._chart_data = data
        self._pw1.clear()
        if data is not None:
            self._pw1.addItem(self._cursor)
            self._pw1.plot(data["t"], data["r"], pen=pg.mkPen(CLR_PRIMARY, width=2))
            if len(data["t"]) > 0:
                self._cursor.setValue(data["t"][0])
        # reset live buffers
        if self._live_key:
            self._buffers[self._live_key] = []
            self._t_buffer = []

    def _on_frame(self, i: int) -> None:
        # Mettre à jour le curseur r(t)
        if self._chart_data is not None:
            t_arr = self._chart_data["t"]
            if i < len(t_arr):
                self._cursor.setValue(t_arr[i])

        # Mettre à jour le graphe live
        if self._live_key and self._pw2 is not None:
            metrics = self._plot.get_frame_metrics(i)
            if self._live_key in metrics:
                dt = (
                    getattr(self._plot.params, "dt", self._plot._frame_ms / 1000.0)
                    if self._plot.params else self._plot._frame_ms / 1000.0
                )
                t_val = i * dt
                buf = self._buffers[self._live_key]
                buf.append(metrics[self._live_key])
                self._t_buffer.append(t_val)
                if len(buf) > _CHART_MAX_POINTS:
                    self._buffers[self._live_key] = buf[-_CHART_MAX_POINTS:]
                    self._t_buffer = self._t_buffer[-_CHART_MAX_POINTS:]
                if len(buf) > 1:
                    self._live_curve.setData(
                        np.array(self._t_buffer),
                        np.array(self._buffers[self._live_key]),
                    )


# ─── Barre de contrôle vitesse ────────────────────────────────────────────────

class _SpeedWidget(QWidget):
    """Slider discret pour la vitesse de simulation."""

    def __init__(self, plot, parent=None):
        super().__init__(parent)
        self._plot = plot
        self._idx = SPEED_STEPS.index(1.0)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lbl = QLabel("Vitesse :")
        lbl.setStyleSheet(f"font-size: {FS_XS}; color: {CLR_TEXT_SECONDARY};")
        lay.addWidget(lbl)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, len(SPEED_STEPS) - 1)
        self._slider.setValue(self._idx)
        self._slider.setFixedWidth(90)
        self._slider.setFixedHeight(SLIDER_H)
        self._slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ height: {SLIDER_GROOVE_H}; background: {CLR_BORDER}; border-radius: {SLIDER_GROOVE_RADIUS}; }}"
            f"QSlider::handle:horizontal {{ width: {SLIDER_HANDLE_SIZE}; height: {SLIDER_HANDLE_SIZE}; margin: {SLIDER_HANDLE_MARGIN}; "
            f"background: {CLR_PRIMARY}; border-radius: {SLIDER_HANDLE_RADIUS}; }}"
            f"QSlider::sub-page:horizontal {{ background: {CLR_PRIMARY}; border-radius: {SLIDER_GROOVE_RADIUS}; }}"
        )
        self._slider.valueChanged.connect(self._on_change)
        lay.addWidget(self._slider)

        self._val_lbl = QLabel(SPEED_LABELS[self._idx])
        self._val_lbl.setStyleSheet(
            f"font-size: {FS_XS}; color: {CLR_PRIMARY}; font-family: monospace; font-weight: 600; min-width: 32px;"
        )
        lay.addWidget(self._val_lbl)

    def _on_change(self, idx: int) -> None:
        self._idx = idx
        factor = SPEED_STEPS[idx]
        self._val_lbl.setText(SPEED_LABELS[idx])
        self._plot.set_speed(factor)


# ─── Dashboard principal ──────────────────────────────────────────────────────

class SimDashboard(QWidget):
    """Dashboard sandbox 4 panneaux pour une simulation — mode libre."""

    def __init__(self, sim_key: str, plot, on_back=None, parent=None):
        super().__init__(parent)
        self.sim_key = sim_key
        self._plot = plot
        info = SIM.get(sim_key, {})

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Barre supérieure ──────────────────────────────────────────────────
        topbar = QWidget()
        topbar.setStyleSheet(f"background: {CLR_BG}; border-bottom: 1px solid {CLR_BORDER};")
        topbar_lay = QHBoxLayout(topbar)
        topbar_lay.setContentsMargins(12, 6, 12, 6)

        if on_back:
            back_btn = QPushButton("← Menu")
            back_btn.setProperty("flat", True)
            back_btn.clicked.connect(on_back)
            topbar_lay.addWidget(back_btn)

        sim_title = QLabel(info.get("title", sim_key))
        sim_title.setStyleSheet(f"font-size: {FS_MD}; font-weight: 600;")
        topbar_lay.addWidget(sim_title, stretch=1)

        tagline = info.get("tagline", "")
        if tagline:
            tl = QLabel(f"— {tagline}")
            tl.setStyleSheet(
                f"font-size: {FS_XS}; color: {CLR_TEXT_SECONDARY}; font-style: italic;"
            )
            topbar_lay.addWidget(tl)

        root.addWidget(topbar)

        # ── Corps : layout horizontal fixe (gauche / droite) ─────────────────
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # ── Colonne gauche fixe (290px) ───────────────────────────────────────
        left_col = QWidget()
        left_col.setFixedWidth(DASH_LEFT_W)
        left_col.setStyleSheet(
            f"background: {CLR_BG}; border-right: 1px solid {CLR_BORDER};"
        )
        left_lay = QVBoxLayout(left_col)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # Haut-gauche : paramètres (scrollable)
        params_scroll = QScrollArea()
        params_scroll.setWidgetResizable(True)
        params_scroll.setFrameShape(QFrame.Shape.NoFrame)
        params_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        params_scroll.setStyleSheet(f"QScrollArea {{ background: {CLR_BG}; }}")
        params_scroll.setWidget(_ParamsPanel(plot))
        left_lay.addWidget(params_scroll, stretch=2)

        sep_h = QFrame()
        sep_h.setFrameShape(QFrame.Shape.HLine)
        sep_h.setStyleSheet(f"color: {CLR_BORDER};")
        left_lay.addWidget(sep_h)

        # Bas-gauche : infos + glossaire
        left_lay.addWidget(_InfoPanel(sim_key), stretch=3)

        body_lay.addWidget(left_col)

        # ── Colonne droite (simulation + graphes) ─────────────────────────────
        right_col = QWidget()
        right_lay = QVBoxLayout(right_col)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        plot.widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._sim_host = QWidget()
        self._sim_host_lay = QVBoxLayout(self._sim_host)
        self._sim_host_lay.setContentsMargins(0, 0, 0, 0)
        self._sim_host_lay.setSpacing(0)
        self._sim_host_lay.addWidget(plot.widget)
        right_lay.addWidget(self._sim_host, stretch=7)

        sep_h2 = QFrame()
        sep_h2.setFrameShape(QFrame.Shape.HLine)
        sep_h2.setStyleSheet(f"color: {CLR_BORDER};")
        right_lay.addWidget(sep_h2)

        self._charts = _LiveChartsPanel(plot)
        self._charts.setFixedHeight(DASH_CHARTS_H)
        right_lay.addWidget(self._charts)

        body_lay.addWidget(right_col, stretch=1)

        root.addWidget(body, stretch=1)

        # ── Barre de contrôle ─────────────────────────────────────────────────
        self._ctrl_bar = QWidget()
        self._ctrl_bar.setObjectName("ctrlBar")
        self._ctrl_bar.setStyleSheet(
            f"QWidget#ctrlBar {{ background: {CLR_BG}; border-top: 1px solid {CLR_BORDER}; }}"
        )
        ctrl_lay = QHBoxLayout(self._ctrl_bar)
        ctrl_lay.setContentsMargins(12, 6, 12, 6)
        ctrl_lay.setSpacing(6)

        b_play = QPushButton("▶ Lecture")
        b_play.clicked.connect(plot.start)
        ctrl_lay.addWidget(b_play)

        b_stop = QPushButton("⏸ Pause")
        b_stop.setProperty("secondary", True)
        b_stop.clicked.connect(plot.stop)
        ctrl_lay.addWidget(b_stop)

        b_reset = QPushButton("↺ Reset")
        b_reset.setProperty("secondary", True)
        b_reset.clicked.connect(plot.reset)
        ctrl_lay.addWidget(b_reset)

        ctrl_lay.addWidget(_vsep())
        ctrl_lay.addWidget(_SpeedWidget(plot))
        ctrl_lay.addWidget(_vsep())

        build_preset_buttons(plot, ctrl_lay)
        ctrl_lay.addStretch()

        root.addWidget(self._ctrl_bar)

        # Masque les contrôles si le calcul est encore en cours au moment
        # de la construction du dashboard — ils réapparaissent sur setup_done.
        if not plot._ready:
            self._ctrl_bar.hide()
            self._charts.hide()
            plot.setup_done.connect(self._on_plot_ready)

    def _on_plot_ready(self) -> None:
        """Appelé depuis setup_done : rend les contrôles visibles."""
        self._ctrl_bar.show()
        self._charts.show()

    def showEvent(self, event) -> None:
        """Reclaims plot.widget in case another view has reparented it."""
        super().showEvent(event)
        w = self._plot.widget
        if w.parent() is not self._sim_host:
            while self._sim_host_lay.count():
                item = self._sim_host_lay.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            self._sim_host_lay.addWidget(w)
            w.show()


def _vsep() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setStyleSheet(f"color: {CLR_BORDER};")
    sep.setFixedHeight(VSEP_H)
    return sep
