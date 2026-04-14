"""Vue MCU — mouvement circulaire uniforme en 2D (pyqtgraph)."""

import math

import numpy as np
import pyqtgraph as pg

from config.theme import CLR_PLOT_PARTICLE, CLR_PRIMARY, RGB_MARKER
from physics.mcu import compute_mcu
from ui.base_sim_widget import BaseSimWidget


class MCUWidget(BaseSimWidget):
    R_MAX = 0.4  # overridden from config lors de l'init

    def __init__(self, cfg: dict, parent=None):
        super().__init__(cfg, parent)
        self.R_MAX = cfg["physics"]["R"]
        self._traj: np.ndarray | None = None

        # ── Widgets pyqtgraph ──
        self._pw: pg.PlotWidget = pg.PlotWidget()
        self._pw.setAspectLocked(True)
        self._pw.setBackground(cfg.get("plot_bg", "#FFFFFF"))
        self._pw.showGrid(x=True, y=True, alpha=0.3)
        lim = self.R_MAX * 1.1
        self._pw.setXRange(-lim, lim)
        self._pw.setYRange(-lim, lim)

        pen_orbit = pg.mkPen(color=CLR_PLOT_PARTICLE, width=2)
        self._orbit_curve   = self._pw.plot(pen=pen_orbit)
        self._particle_item = self._pw.plot(
            pen=None, symbol="o", symbolSize=10,
            symbolBrush=CLR_PLOT_PARTICLE, symbolPen="w",
        )
        self._markers_items: list[pg.PlotDataItem] = []
        self._init_plot(self._pw)

    # ── Simulation ────────────────────────────────────────────────────────────

    def _compute(self) -> None:
        p = self._params
        phys = self._cfg["physics"]
        self._traj = compute_mcu(
            r=p["r"], theta0=p["theta0"], omega=p["omega"],
            n_steps=phys["n_steps"], dt=phys["dt"],
        )
        self._n_frames = len(self._traj)

    def _draw_initial(self) -> None:
        if self._traj is None:
            return
        self._draw(0)

    def _draw(self, frame: int) -> None:
        if self._traj is None:
            return
        self._orbit_curve.setData(self._traj[:frame + 1, 0], self._traj[:frame + 1, 1])
        x, y = self._traj[frame]
        self._particle_item.setData([x], [y])

    # ── Marqueurs ─────────────────────────────────────────────────────────────

    def _add_marker(self, r: float, theta: float) -> None:
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        item = self._pw.plot(
            [x], [y], pen=None, symbol="x", symbolSize=12,
            symbolBrush=pg.mkBrush(*[int(c * 255) for c in RGB_MARKER[:3]], 255),
            symbolPen=pg.mkPen(CLR_PRIMARY),
        )
        self._markers_items.append(item)
