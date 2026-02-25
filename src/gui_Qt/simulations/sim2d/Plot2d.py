import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer

from utils.math_helpers import disk_xy
from utils.params import Simulation2dParams


class Plot2d:
    def __init__(self, sim_params: Simulation2dParams = Simulation2dParams()) -> None:
        self.sim_params = sim_params
        self.widget = pg.PlotWidget()
        self.widget.setXRange(-60, 60)
        self.widget.setYRange(-60, 60)
        self.widget.setAspectLocked(True)
        self.widget.setMenuEnabled(False)

        # Plot items
        self.center_ball = None
        self.orbit_path = None
        self.moving_ball = None
        self.partial_trajectory = None

        # Animation state
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation_frame)
        self.current_frame = 0
        self.frames = []
        self.trajectory_xs = []
        self.trajectory_ys = []

    def setup_animation(
        self,
        frame_interval_ms: int = 30,
    ) -> None:
        """Set up and start the animation."""
        self._run_simulation()

        # Generate frames for animation
        self.frames = list(range(0, len(self.trajectory_xs), 10))  # Use stride of 10

        # Start animation
        self.current_frame = 0
        self._update_animation_frame()  # Draw the first frame
        self.animation_timer.start(frame_interval_ms)

    def _run_simulation(self) -> None:
        """Run the physics simulation to generate the trajectory."""
        mu = self.sim_params.G * self.sim_params.M
        dt = 0.02

        # Initial conditions
        r = np.array([self.sim_params.r0, 0.0], dtype=float)

        # Initial velocity with angle
        theta = np.deg2rad(self.sim_params.theta_deg)
        v = np.array(
            [self.sim_params.v0 * np.cos(theta), self.sim_params.v0 * np.sin(theta)],
            dtype=float,
        )

        def accel(r_vec: np.ndarray, v_vec: np.ndarray) -> np.ndarray:
            r_norm = np.linalg.norm(r_vec)
            r_norm = max(float(r_norm), 1e-12)
            r_hat = r_vec / r_norm
            a_mag = mu / (r_norm**2)
            a_grav = -a_mag * r_hat
            a_drag = -self.sim_params.gamma * v_vec
            return a_grav + a_drag

        # Velocity-Verlet integration
        a = accel(r, v)
        self.trajectory_xs = []
        self.trajectory_ys = []

        for _ in range(self.sim_params.n_frames):
            self.trajectory_xs.append(r[0])
            self.trajectory_ys.append(r[1])

            if np.linalg.norm(r) <= (
                self.sim_params.center_radius + self.sim_params.particle_radius
            ):
                break

            r_next = r + v * dt + 0.5 * a * dt**2
            v_half = v + 0.5 * a * dt
            a_next = accel(r_next, v_half)
            v_next = v_half + 0.5 * a_next * dt

            r, v, a = r_next, v_next, a_next

        self.trajectory_xs = np.array(self.trajectory_xs)
        self.trajectory_ys = np.array(self.trajectory_ys)

    def _draw_static_elements(self) -> None:
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

        # Orbit path (initially hidden)
        self.orbit_path = self.widget.plot(
            pen=pg.mkPen(color=(18, 59, 207, 255), width=1)
        )
        self.orbit_path.hide()  # Initially hidden

        # Partial trajectory
        self.partial_trajectory = self.widget.plot(
            pen=pg.mkPen(color=(18, 59, 207, 128), width=2)
        )

        # Moving ball (initially at starting position)
        if len(self.trajectory_xs) > 0 and len(self.trajectory_ys) > 0:
            mx0, my0 = disk_xy(
                self.trajectory_xs[0],
                self.trajectory_ys[0],
                self.sim_params.particle_radius,
            )
            self.moving_ball = pg.PlotCurveItem(
                x=mx0,
                y=my0,
                pen=pg.mkPen(width=1, color=(200, 50, 50, 255)),
                fillLevel=0,
                brush=pg.mkBrush(color=(200, 50, 50, 255)),
            )
            self.widget.addItem(self.moving_ball)

    def _update_animation_frame(self) -> None:
        """Update the animation frame."""
        if self.current_frame == 0:
            self._draw_static_elements()
        if self.current_frame < len(self.frames):
            frame_idx = self.frames[self.current_frame]

            # Update moving ball position
            mx, my = disk_xy(
                self.trajectory_xs[frame_idx],
                self.trajectory_ys[frame_idx],
                self.sim_params.particle_radius,
            )
            self.moving_ball.setData(x=mx, y=my)

            # Update partial trajectory (trail)
            i0 = max(0, frame_idx - self.sim_params.trail)
            self.partial_trajectory.setData(
                x=self.trajectory_xs[i0 : frame_idx + 1],
                y=self.trajectory_ys[i0 : frame_idx + 1],
            )

            self.current_frame += 1
        else:
            self.stop_animation()

    def stop_animation(self) -> None:
        """Stop the animation."""
        self.animation_timer.stop()

    def toggle_pause_animation(self) -> None:
        """Toggle between pausing and resuming the animation."""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
        else:
            self.animation_timer.start()

    def reset_animation(self) -> None:
        """Reset the animation to the start."""
        self.stop_animation()
        self.current_frame = 0
        if len(self.trajectory_xs) > 0 and len(self.trajectory_ys) > 0:
            mx0, my0 = disk_xy(
                self.trajectory_xs[0],
                self.trajectory_ys[0],
                self.sim_params.particle_radius,
            )
            self.moving_ball.setData(x=mx0, y=my0)
            self.partial_trajectory.setData(x=[], y=[])

    def redraw(self) -> None:
        """Redraw the plot."""
        self.widget.clear()
        self._draw_static_elements()
