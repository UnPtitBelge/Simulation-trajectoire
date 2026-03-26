"""MCU 2D — Mouvement Circulaire Uniforme.

Pure analytical formula: x=R·cos(ωt), y=R·sin(ωt).
Optional exponential drag for spiral decay.
Avec frottement (drag>0): arrêt dès que r < center_radius (collision bille centrale).
"""

import logging
import math

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from src.core.geometry import disk_xy
from src.core.params.mcu import MCUParams
from src.simulations.base import Plot
from src.utils.theme import CLR_PLOT_BG, CLR_PLOT_CENTER, CLR_PLOT_PARTICLE

log = logging.getLogger(__name__)


def _hex(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


_BG = _hex(CLR_PLOT_BG)
_CEN = _hex(CLR_PLOT_CENTER)
_PAR = _hex(CLR_PLOT_PARTICLE)


class PlotMCU(Plot):
    SIM_KEY = "mcu"

    def __init__(self, params: MCUParams | None = None):
        _p = params or MCUParams()
        super().__init__(_p)
        self.params: MCUParams = _p
        self.widget = pg.PlotWidget()
        self.widget.setBackground(CLR_PLOT_BG)
        self.widget.setMenuEnabled(False)
        self.widget.getViewBox().setAspectLocked(True, 1.0)
        self.widget.hideAxis("bottom")
        self.widget.hideAxis("left")
        # Keep mouse interaction but prevent focus stealing
        self.widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.xs = []
        self.ys = []

        self.center = self.widget.plot([], [], fillLevel=0)
        self.orbit = self.widget.plot(
            [],
            [],
            pen=pg.mkPen(
                color=(*_PAR, 80), width=1, style=pg.QtCore.Qt.PenStyle.DashLine
            ),
        )
        self.ball = pg.ScatterPlotItem(
            size=10,
            brush=pg.mkBrush(*_PAR, 230),
            pen=pg.mkPen(color=(*_PAR, 255), width=1),
        )
        self.widget.addItem(self.ball)

        self._shortcut = QShortcut(QKeySequence("Ctrl+T"), self.widget)
        self._shortcut.activated.connect(self._toggle_orbit)

    def _get_cache_data(self) -> dict:
        return {"xs": self.xs[:], "ys": self.ys[:], "_n_frames": self._n_frames}

    def _set_cache_data(self, data: dict) -> None:
        self.xs = data["xs"]
        self.ys = data["ys"]
        self._n_frames = data["_n_frames"]

    def _compute(self):
        p = self.params
        n = int(p.n_frames)

        R = p.R
        omega = p.omega
        drag = p.drag

        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        decay = np.exp(-drag * t)
        xs_arr = R * np.cos(omega * t) * decay
        ys_arr = R * np.sin(omega * t) * decay

        # Avec frottement : arrêt dès que r < center_radius (collision bille centrale)
        # r[i] = R * decay[i] (exact, sans sqrt)
        if drag > 0:
            r_arr = R * decay
            hit = np.where(r_arr < p.center_radius)[0]
            if len(hit) > 0:
                i_stop = int(hit[0])
                xs_arr = xs_arr[: i_stop + 1]
                ys_arr = ys_arr[: i_stop + 1]
                n = i_stop + 1
                log.info("MCU stopped at frame %d: ball reached center.", i_stop)

        self.xs = xs_arr.tolist()
        self.ys = ys_arr.tolist()
        self._n_frames = n

    def _draw_initial(self):
        p = self.params
        cr, R = p.center_radius, p.R
        margin = R * 1.25

        cx, cy = disk_xy(0, 0, cr, 64)
        self.center.setData(
            cx,
            cy,
            pen=pg.mkPen(color=(*_CEN, 200), width=1),
            fillLevel=0.0,
            brush=pg.mkBrush(*_CEN, 180),
        )
        ox, oy = disk_xy(0, 0, R, 200)
        self.orbit.setData(ox, oy)
        self.widget.setRange(
            xRange=(-margin, margin), yRange=(-margin, margin), padding=0
        )
        if self.xs:
            self.ball.setData([self.xs[0]], [self.ys[0]])
            self.frame_updated.emit(0)

    def _draw(self, i):
        if 0 <= i < len(self.xs):
            self.ball.setData([self.xs[i]], [self.ys[i]])

    def get_metrics_schema(self) -> list[dict]:
        from src.utils.theme import (
            CLR_PRIMARY,
            CLR_SUCCESS,
            CLR_TEXT_SECONDARY,
            CLR_WARNING,
        )

        return [
            {
                "key": "r",
                "label": "Rayon",
                "unit": "m",
                "fmt": ".3f",
                "color": CLR_PRIMARY,
            },
            {
                "key": "theta",
                "label": "Angle",
                "unit": "°",
                "fmt": ".1f",
                "color": CLR_SUCCESS,
            },
            {
                "key": "speed",
                "label": "Vitesse",
                "unit": "m/s",
                "fmt": ".3f",
                "color": CLR_WARNING,
            },
            {
                "key": "t",
                "label": "Temps",
                "unit": "s",
                "fmt": ".2f",
                "color": CLR_TEXT_SECONDARY,
            },
            {
                "key": "tours",
                "label": "Tours",
                "unit": "",
                "fmt": ".2f",
                "color": "#6B48FF",
            },
        ]

    def get_chart_data(self) -> dict | None:
        if not self.xs:
            return None
        t_arr = np.arange(len(self.xs)) * (self.params.frame_ms / 1000.0)
        r_arr = np.sqrt(np.array(self.xs) ** 2 + np.array(self.ys) ** 2)
        return {"t": t_arr, "r": r_arr, "label": "r (m)"}

    def get_frame_metrics(self, i: int) -> dict:
        if not (0 <= i < len(self.xs)):
            return {}
        x, y = self.xs[i], self.ys[i]
        r = math.sqrt(x * x + y * y)
        theta = math.degrees(math.atan2(y, x))
        if i > 0:
            dx = x - self.xs[i - 1]
            dy = y - self.ys[i - 1]
            dt_display = self.params.frame_ms / 1000.0
            speed = math.sqrt(dx * dx + dy * dy) / max(dt_display, 1e-9)
        else:
            speed = abs(self.params.omega) * r
        t_sec = i * self.params.frame_ms / 1000.0
        tours = abs(self.params.omega) * t_sec / (2 * math.pi)
        return {"r": r, "theta": theta, "speed": speed, "t": t_sec, "tours": tours}

    def _toggle_orbit(self):
        self.orbit.setVisible(not self.orbit.isVisible())
