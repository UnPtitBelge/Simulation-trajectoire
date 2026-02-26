from simulations.Plot import Plot
from simulations.sim2d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import disk_xy
from utils.params import Simulation2dParams

import pyqtgraph as pg


class Plot2d(Plot):
    """2D plot wrapper for the planar simulation.

    This class now inherits common animation and parameter handling from the
    shared `Plot` base class and implements the simulation-specific hooks:
      - _prepare_simulation: run simulate_trajectory and populate frame count
      - _update_frame: render the particle for a given frame index
      - _draw_initial_frame: draw static items and the first frame
    """

    def __init__(self, sim_params: Simulation2dParams = Simulation2dParams()) -> None:
        # Initialize base Plot with default frame interval taken from sim_params
        super().__init__(sim_params, frame_ms=getattr(sim_params, "frame_ms", 100))

        # Simulation parameters and plot widget
        self.sim_params = sim_params
        self.widget = pg.PlotWidget()
        self.widget.setAspectLocked(True)
        self.widget.setMenuEnabled(False)

        # Visual handles
        self.moving_ball = None
        self.center_ball = None

        # Storage for trajectory frames (populated by _prepare_simulation)
        self.trajectory_xs = []
        self.trajectory_ys = []

    # ---- Implementation of abstract hooks required by the base Plot ----
    def _prepare_simulation(self) -> None:
        """Compute the trajectory arrays and set the number of frames."""
        results = simulate_trajectory(self.sim_params)
        self.trajectory_xs = results.get("xs", [])
        self.trajectory_ys = results.get("ys", [])
        # number of frames used by the base class animation loop
        self._n_frames = (
            len(self.trajectory_xs) if self.trajectory_xs is not None else 0
        )

    def _update_frame(self, frame_index: int) -> None:
        """Render a single animation frame (draw/update the moving disk)."""
        if not self.trajectory_xs or frame_index >= len(self.trajectory_xs):
            # Nothing to draw or out of range
            return
        x = self.trajectory_xs[frame_index]
        y = self.trajectory_ys[frame_index]
        self._draw_moving_ball(x, y)

    def _draw_initial_frame(self) -> None:
        """Draw static elements (center ball) and place the first moving ball frame."""
        # clear previous static items if any
        try:
            if self.center_ball is not None:
                self.widget.removeItem(self.center_ball)
        except Exception:
            pass

        # Draw center disk
        cx0, cy0 = disk_xy(0.0, 0.0, self.sim_params.center_radius, n=80)
        self.center_ball = pg.PlotCurveItem(
            x=cx0,
            y=cy0,
            pen=pg.mkPen(width=1, color=(42, 151, 8, 255)),
            fillLevel=0,
            brush=pg.mkBrush(color=(42, 151, 8, 255)),
        )
        self.widget.addItem(self.center_ball)

        # Draw the first moving ball if available
        if getattr(self, "_n_frames", 0) > 0:
            try:
                self._update_frame(0)
            except Exception:
                pass

    # ---- Helper drawing method reused by the frame updater ----
    def _draw_moving_ball(self, x, y) -> None:
        """Draw or update the disk at the given position."""
        # Remove existing moving ball if present
        try:
            if self.moving_ball is not None:
                self.widget.removeItem(self.moving_ball)
        except Exception:
            pass

        px, py = disk_xy(x, y, self.sim_params.particle_radius)

        self.moving_ball = pg.ScatterPlotItem(
            x=px,
            y=py,
            size=self.sim_params.particle_radius * 2,  # Diameter
            pen=pg.mkPen(width=1, color=(200, 50, 50, 255)),
            brush=pg.mkBrush(color=(200, 50, 50, 255)),
            symbol="o",  # 'o' for circle
        )
        self.widget.addItem(self.moving_ball)

    # ---- Parameter update: delegate to base class (which calls setup_animation) ----
    def update_params(self, **kwargs) -> None:
        """Update simulation parameters and trigger recomputation via base class."""
        # Let the base class apply changes to self.sim_params and call setup_animation()
        super().update_params(**kwargs)
