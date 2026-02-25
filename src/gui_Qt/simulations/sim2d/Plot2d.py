import pyqtgraph as pg
from PySide6.QtCore import QTimer
from simulations.sim2d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import disk_xy
from utils.params import Simulation2dParams


class Plot2d:
    def __init__(self, sim_params: Simulation2dParams = Simulation2dParams()) -> None:
        self.sim_params = sim_params
        self.widget = pg.PlotWidget()
        self.widget.setAspectLocked(True)
        self.widget.setMenuEnabled(False)

        # Animation state
        self.moving_ball = None
        self.current_frame = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation_frame)

    def setup_animation(self) -> None:
        """Set up and start the animation."""
        results = simulate_trajectory(self.sim_params)

        self.trajectory_xs = results["xs"]
        self.trajectory_ys = results["ys"]

        if not self.trajectory_xs:
            return

        self._draw_center_ball()

        # Start animation
        self.current_frame = 0
        self._update_animation_frame()  # Draw the first frame

    def _update_animation_frame(self) -> None:
        """Update the particle position for the current frame."""
        if self.current_frame < len(self.trajectory_xs):
            x = self.trajectory_xs[self.current_frame]
            y = self.trajectory_ys[self.current_frame]

            self._draw_moving_ball(x, y)
            self.current_frame += 1
        else:
            self.animation_timer.stop()

    def _draw_moving_ball(self, x, y) -> None:
        """Draw or update the disk at the given position"""
        if self.moving_ball is not None:
            self.widget.removeItem(self.moving_ball)

        x, y = disk_xy(
            x,
            y,
            self.sim_params.particle_radius,
        )

        self.moving_ball = pg.ScatterPlotItem(
            x=x,
            y=y,
            size=self.sim_params.particle_radius * 2,  # Diameter
            pen=pg.mkPen(width=1, color=(200, 50, 50, 255)),
            brush=pg.mkBrush(color=(200, 50, 50, 255)),
            symbol="o",  # 'o' for circle
        )
        self.widget.addItem(self.moving_ball)

    def start_animation(self) -> None:
        """Start the animation"""
        self.animation_timer.start(self.sim_params.frame_ms)

    def stop_animation(self) -> None:
        """Stop the animation."""
        self.animation_timer.stop()

    def reset_animation(self) -> None:
        """Reset the animation to the start."""
        self.stop_animation()
        self.current_frame = 0
        if self.trajectory_xs:
            self._draw_moving_ball(
                self.trajectory_xs[0],
                self.trajectory_ys[0],
            )

    def _draw_center_ball(self) -> None:
        """Draw the static elements: center ball."""
        # Center ball (big disk)
        cx0, cy0 = disk_xy(0.0, 0.0, self.sim_params.center_radius, n=80)
        self.center_ball = pg.PlotCurveItem(
            x=cx0,
            y=cy0,
            pen=pg.mkPen(width=1, color=(42, 151, 8, 255)),
            fillLevel=0,
            brush=pg.mkBrush(color=(42, 151, 8, 255)),
        )
        self.widget.addItem(self.center_ball)

    def update_params(self, **kwargs) -> None:
        """Update simulation parameters and restart the animation."""
        for key, value in kwargs.items():
            if hasattr(self.sim_params, key):
                setattr(self.sim_params, key, value)

        # Re-run the simulation and reset the animation
        self.setup_animation()
