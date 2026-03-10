"""2D orbital simulation plot."""

import pyqtgraph as pg
from PySide6.QtGui import QKeySequence, QShortcut
from simulations.Plot import Plot
from simulations.sim2d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import disk_xy
from utils.params import Simulation2dParams
from utils.stylesheet import (
    CLR_PLOT_BG,
    CLR_PLOT_CENTER,
    CLR_PLOT_PARTICLE,
)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


_BG = _hex_to_rgb(CLR_PLOT_BG)
_CENTER = _hex_to_rgb(CLR_PLOT_CENTER)
_PARTICLE = _hex_to_rgb(CLR_PLOT_PARTICLE)


class Plot2d(Plot):
    """2D orbital simulation plot backed by a pyqtgraph PlotWidget."""

    def __init__(self, sim_params: Simulation2dParams = Simulation2dParams()) -> None:
        super().__init__(sim_params, frame_ms=sim_params.frame_ms)
        self.sim_params = sim_params

        self.widget = pg.PlotWidget()
        self.widget.setAspectLocked(True)
        self.widget.setMenuEnabled(False)
        self.widget.setBackground(CLR_PLOT_BG)
        self.widget.hideAxis("bottom")
        self.widget.hideAxis("left")

        self.center_ball = None

        self.moving_ball = pg.ScatterPlotItem(
            size=self.sim_params.particle_radius * 2,
            pen=pg.mkPen(width=1, color=(*_PARTICLE, 255)),
            brush=pg.mkBrush(color=(*_PARTICLE, 220)),
            symbol="o",
            pxMode=False,
        )
        self.widget.addItem(self.moving_ball)

        self.trajectory_xs: list[float] = []
        self.trajectory_ys: list[float] = []
        
        self.trajectory_line = pg.PlotCurveItem(
            pen=pg.mkPen(width=1.5, color=(1, 1, 1, 120))
        )
        self.widget.addItem(self.trajectory_line)
        self.show_trajectory_trail = False

        self.shortcut_traj = QShortcut(QKeySequence("Ctrl+T"), self.widget)
        self.shortcut_traj.activated.connect(self.toggle_trajectory)

    def toggle_trajectory(self) -> None:
        self.show_trajectory_trail = not self.show_trajectory_trail
        if not self.show_trajectory_trail:
            self.trajectory_line.setData([], [])
        else:
            if self.trajectory_xs:
                # Up to current frame
                self.trajectory_line.setData(
                    self.trajectory_xs[:self.current_frame+1],
                    self.trajectory_ys[:self.current_frame+1]
                )

    def _prepare_simulation(self) -> None:
        results = simulate_trajectory(self.sim_params)
        self.trajectory_xs = results.get("xs", [])
        self.trajectory_ys = results.get("ys", [])
        self._n_frames = len(self.trajectory_xs) if self.trajectory_xs else 0

    def _update_frame(self, frame_index: int) -> None:
        if not self.trajectory_xs or frame_index >= len(self.trajectory_xs):
            return
        
        self.moving_ball.setData(
            [self.trajectory_xs[frame_index]],
            [self.trajectory_ys[frame_index]],
        )
        
        if self.show_trajectory_trail:
            self.trajectory_line.setData(
                self.trajectory_xs[:frame_index+1],
                self.trajectory_ys[:frame_index+1]
            )

    def _draw_initial_frame(self) -> None:
        if self.center_ball is not None:
            try:
                self.widget.removeItem(self.center_ball)
            except Exception:
                pass

        cx0, cy0 = disk_xy(0.0, 0.0, self.sim_params.center_radius, n=80)
        self.center_ball = pg.PlotCurveItem(
            x=cx0,
            y=cy0,
            pen=pg.mkPen(width=1, color=(*_CENTER, 255)),
            fillLevel=0,
            brush=pg.mkBrush(color=(*_CENTER, 180)),
        )
        self.widget.addItem(self.center_ball)

        self.moving_ball.setSize(self.sim_params.particle_radius * 2)
        self.trajectory_line.setData([], [])

        if self._n_frames > 0:
            self._update_frame(0)
        else:
            self.moving_ball.setData([], [])

    def update_params(self, **kwargs) -> None:
        super().update_params(**kwargs)
