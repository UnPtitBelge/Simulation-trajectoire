"""2-D uniform circular motion (MCU) simulation renderer.

Renders the analytical circular orbit on a pyqtgraph PlotWidget.  The
central body is drawn as a static filled circle; the orbit path is
shown as a dashed ring; the particle moves around it frame by frame.
"""
from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtGui import QKeySequence, QShortcut
from simulations.Plot import Plot
from simulations.sim2d.simulate_mcu import simulate_mcu
from utils.math_helpers import disk_xy
from utils.params import SimulationMCUParams
from utils.stylesheet import CLR_PLOT_BG, CLR_PLOT_CENTER, CLR_PLOT_PARTICLE


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


_BG       = _hex_to_rgb(CLR_PLOT_BG)
_CENTER   = _hex_to_rgb(CLR_PLOT_CENTER)
_PARTICLE = _hex_to_rgb(CLR_PLOT_PARTICLE)


class PlotMCU(Plot):
    """2-D uniform circular motion renderer.

    Attributes
    ----------
    sim_params     SimulationMCUParams controlling the orbit.
    widget         pyqtgraph PlotWidget.
    center_ball    PlotCurveItem — the filled central body circle.
    orbit_circle   PlotCurveItem — the dashed orbit path.
    moving_ball    ScatterPlotItem — the animated particle.
    trajectory_xs/ys/vxs/vys  Per-frame trajectory data (lists of float).
    """

    SIM_TYPE = "2d_mcu"

    def __init__(self, sim_params: SimulationMCUParams | None = None) -> None:
        if sim_params is None:
            sim_params = SimulationMCUParams()
        super().__init__(sim_params, frame_ms=sim_params.frame_ms)
        self.sim_params = sim_params

        self.widget = pg.PlotWidget()
        self.widget.setBackground(CLR_PLOT_BG)
        self.widget.setMenuEnabled(False)
        self.widget.getViewBox().setAspectLocked(lock=True, ratio=1.0)
        self.widget.hideAxis("bottom")
        self.widget.hideAxis("left")

        # Static curves — populated in _draw_initial_frame
        self.center_ball  = self.widget.plot([], [], fillLevel=0)
        self.orbit_circle = self.widget.plot(
            [], [],
            pen=pg.mkPen(color=(*_PARTICLE, 80), width=1,
                         style=pg.QtCore.Qt.PenStyle.DashLine),
        )
        self.moving_ball = pg.ScatterPlotItem(
            size=10,
            brush=pg.mkBrush(*_PARTICLE, 230),
            pen=pg.mkPen(color=(*_PARTICLE, 255), width=1),
        )
        self.widget.addItem(self.moving_ball)

        self.trajectory_xs:  list[float] = []
        self.trajectory_ys:  list[float] = []
        self.trajectory_vxs: list[float] = []
        self.trajectory_vys: list[float] = []

        self.shortcut_traj = QShortcut(QKeySequence("Ctrl+T"), self.widget)
        self.shortcut_traj.activated.connect(self.toggle_orbit_circle)

    # -----------------------------------------------------------------------
    # Plot abstract hook implementations
    # -----------------------------------------------------------------------

    def _prepare_simulation(self) -> None:
        results = simulate_mcu(self.sim_params)
        self.trajectory_xs  = results["xs"]
        self.trajectory_ys  = results["ys"]
        self.trajectory_vxs = results["vxs"]
        self.trajectory_vys = results["vys"]
        self._n_frames      = results["n_frames"]

    def _draw_initial_frame(self) -> None:
        """Draw the central body, orbit ring and initial particle position."""
        cr = float(self.sim_params.center_radius)
        R  = float(self.sim_params.R)
        margin = R * 1.25

        # Central body
        cx, cy = disk_xy(0.0, 0.0, cr, n=64)
        self.center_ball.setData(
            cx, cy,
            pen=pg.mkPen(color=(*_CENTER, 200), width=1),
            fillLevel=0.0,
            brush=pg.mkBrush(*_CENTER, 180),
        )

        # Orbit circle (dashed ring at orbital radius R)
        ox, oy = disk_xy(0.0, 0.0, R, n=200)
        self.orbit_circle.setData(ox, oy)

        # Set view range with margin
        self.widget.setRange(
            xRange=(-margin, margin),
            yRange=(-margin, margin),
            padding=0,
        )

        if self.trajectory_xs:
            self.moving_ball.setData(
                [self.trajectory_xs[0]],
                [self.trajectory_ys[0]],
            )
            self.frame_updated.emit(0)

    def _update_frame(self, frame_index: int) -> None:
        if not (0 <= frame_index < len(self.trajectory_xs)):
            return
        self.moving_ball.setData(
            [self.trajectory_xs[frame_index]],
            [self.trajectory_ys[frame_index]],
        )

    # -----------------------------------------------------------------------
    # Orbit circle toggle (Ctrl+T)
    # -----------------------------------------------------------------------

    def toggle_orbit_circle(self) -> None:
        """Show or hide the dashed orbit ring."""
        visible = self.orbit_circle.isVisible()
        self.orbit_circle.setVisible(not visible)
