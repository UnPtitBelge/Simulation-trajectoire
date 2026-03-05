import pyqtgraph as pg
from simulations.Plot import Plot
from simulations.sim2d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import disk_xy
from utils.params import Simulation2dParams


class Plot2d(Plot):
    """2D plot wrapper for the planar simulation."""

    def __init__(self, sim_params: Simulation2dParams = Simulation2dParams()) -> None:
        super().__init__(sim_params, frame_ms=getattr(sim_params, "frame_ms", 100))

        self.sim_params = sim_params
        self.widget = pg.PlotWidget()
        self.widget.setAspectLocked(True)
        self.widget.setMenuEnabled(False)

        # Static geometry item (center ball) — recreated on reset only
        self.center_ball = None

        # Moving ball: pxMode=False → size is in plot units (same as r0, center_radius, etc.)
        # diameter = particle_radius * 2 in plot-space units, scales correctly with zoom.
        self.moving_ball = pg.ScatterPlotItem(
            size=self.sim_params.particle_radius * 2,
            pen=pg.mkPen(width=1, color=(200, 50, 50, 255)),
            brush=pg.mkBrush(color=(200, 50, 50, 255)),
            symbol="o",
            pxMode=False,
        )
        self.widget.addItem(self.moving_ball)

        # Trajectory data (populated by _prepare_simulation)
        self.trajectory_xs = []
        self.trajectory_ys = []

    def _prepare_simulation(self) -> None:
        """Compute the trajectory arrays and set the number of frames."""
        results = simulate_trajectory(self.sim_params)
        self.trajectory_xs = results.get("xs", [])
        self.trajectory_ys = results.get("ys", [])
        self._n_frames = len(self.trajectory_xs) if self.trajectory_xs else 0

    def _update_frame(self, frame_index: int) -> None:
        """Move the ball to the position for this frame via setData() — no alloc."""
        if not self.trajectory_xs or frame_index >= len(self.trajectory_xs):
            return
        x = self.trajectory_xs[frame_index]
        y = self.trajectory_ys[frame_index]
        # setData() repositions the existing item: no removeItem/addItem needed
        self.moving_ball.setData([x], [y])

    def _draw_initial_frame(self) -> None:
        """Draw static elements and place the ball at frame 0."""
        # Recreate center ball only (static geometry, only redrawn on param change)
        if self.center_ball is not None:
            try:
                self.widget.removeItem(self.center_ball)
            except Exception:
                pass

        cx0, cy0 = disk_xy(0.0, 0.0, self.sim_params.center_radius, n=80)
        self.center_ball = pg.PlotCurveItem(
            x=cx0,
            y=cy0,
            pen=pg.mkPen(width=1, color=(42, 151, 8, 255)),
            fillLevel=0,
            brush=pg.mkBrush(color=(42, 151, 8, 255)),
        )
        self.widget.addItem(self.center_ball)

        # Refresh moving ball size in case particle_radius changed
        self.moving_ball.setSize(self.sim_params.particle_radius * 2)

        if self._n_frames > 0:
            self._update_frame(0)
        else:
            self.moving_ball.setData([], [])

    def update_params(self, **kwargs) -> None:
        super().update_params(**kwargs)
