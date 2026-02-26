import matplotlib.pyplot as plt
import numpy as np
from central_body import CentralBody
from config import (
    central_body_mass,
    central_body_radius,
    deformation_depth_scale,
    deformation_sigma_scale,
    friction_coefficient,
    gravity_constant,
    initial_position_x,
    initial_position_y,
    initial_velocity_x,
    initial_velocity_y,
    num_steps,
    time_step,
)
from matplotlib import animation
from moving_object import MovingObject
from surface_field import SurfaceField


class Simulation:
    def __init__(
        self,
        x: float = initial_position_x,
        y: float = initial_position_y,
        vx: float = initial_velocity_x,
        vy: float = initial_velocity_y,
        k_depth: float = deformation_depth_scale,
        k_sigma: float = deformation_sigma_scale,
        friction: float = friction_coefficient,
        body_radius: float = central_body_radius,
        body_mass: float = central_body_mass,
    ):
        # Central body and surface field use generic naming
        self._central_body = CentralBody(body_radius, body_mass)
        self._surface = SurfaceField(k_depth, k_sigma, body_mass, body_radius, friction)
        self._object = MovingObject(x, y, vx, vy)
        self._run()

    def _run(self):
        for i in range(num_steps):
            # Distance between moving object and central body
            r = np.sqrt(self._object.x**2 + self._object.y**2)
            if r < self._central_body.radius:  # contact with central body
                break
            # Acceleration with gravitational term and linear friction
            if r <= 1e-12:
                ax_g = 0.0
                ay_g = 0.0
            else:
                r3 = r**3
                ax_g = -gravity_constant * self._central_body.mass * self._object.x / r3
                ay_g = -gravity_constant * self._central_body.mass * self._object.y / r3
            self._object.ax = ax_g - self._surface.friction * self._object.velocity[0]
            self._object.ay = ay_g - self._surface.friction * self._object.velocity[1]
            # Update velocity and position using current acceleration
            self._object.update_velocity(
                self._object.acceleration[0], self._object.acceleration[1], time_step
            )
            self._object.update_position(time_step)
            # Record history (x, y, z=surface height at (x, y))
            self._object._xs.append(self._object.x)
            self._object._ys.append(self._object.y)
            self._object._zs.append(
                float(self._surface.h(self._object.x, self._object.y))
            )
        self._plot()

    def _plot(self):
        fig = plt.figure(figsize=(9, 6))
        ax = fig.add_subplot(111, projection="3d")
        grid = np.linspace(-3, 3, 150)
        X, Y = np.meshgrid(grid, grid)
        Z = self._surface.h(X, Y)  # supports numpy arrays element-wise
        ax.plot_surface(X, Y, Z, cmap="plasma", alpha=0.8)
        ax.plot_surface(
            self._central_body.X,
            self._central_body.Y,
            self._central_body.Z,
            color="gold",
            shade=True,
        )
        (animated_object,) = ax.plot(
            [self._object.positions_history[0][0]],
            [self._object.positions_history[1][0]],
            [self._object.positions_history[2][0] + 0.05],
            marker="o",
            linestyle="None",
            color="blue",
        )

        def update(i):
            x_i = self._object.positions_history[0][i]
            y_i = self._object.positions_history[1][i]
            z_i = self._object.positions_history[2][i] + 0.05
            animated_object.set_data([x_i], [y_i])
            animated_object.set_3d_properties([z_i])  # type: ignore
            return (animated_object,)

        _ani = animation.FuncAnimation(
            fig,
            update,
            frames=len(self._object.positions_history[0]),
            interval=10,
            blit=True,
        )
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.set_title("Object moving on a curved surface around a central mass")
        self._set_axes_equal(ax)
        plt.show()

    def _set_axes_equal(self, ax):
        x_limits = ax.get_xlim3d()
        y_limits = ax.get_ylim3d()
        z_limits = ax.get_zlim3d()
        x_range = abs(x_limits[1] - x_limits[0])
        y_range = abs(y_limits[1] - y_limits[0])
        z_range = abs(z_limits[1] - z_limits[0])
        max_range = max(x_range, y_range, z_range)
        centers = (np.mean(x_limits), np.mean(y_limits), np.mean(z_limits))
        ax.set_xlim3d([centers[0] - max_range / 2, centers[0] + max_range / 2])
        ax.set_ylim3d([centers[1] - max_range / 2, centers[1] + max_range / 2])
        ax.set_zlim3d([centers[2] - max_range / 2, centers[2] + max_range / 2])
