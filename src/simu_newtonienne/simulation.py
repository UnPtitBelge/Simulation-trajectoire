import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from constantes import *
from soleil import Soleil
from drap import Drap
from bille import Bille


class Simulation:
    def __init__(self, x: float = x, y: float = y, vx: float = vx, vy: float = vy, k_depth: float = k_depth, k_sigma: float = k_sigma, mu: float = mu, sun_radius: float = sun_radius, M_sun: float = M_sun):
        self._sun = Soleil(sun_radius, M_sun)
        self._drap = Drap(k_depth, k_sigma, M_sun, sun_radius, mu)
        self._bille = Bille(x, y, vx, vy)
        self._run()
        
    def _run(self):
        for i in range(steps):
            r = np.sqrt(self._bille.get_x ** 2 + self._bille.get_y ** 2) # distance bille-Soleil
            if r < self._sun.get_radius:  # contact avec le Soleil
                break
            self._bille.set_ax = -G * self._sun.get_mass * self._bille.get_x / r ** 2 - self._drap.get_mu * self._bille.get_velocity[0] # accélération en x
            self._bille.set_ay = -G * self._sun.get_mass * self._bille.get_y / r ** 2 - self._drap.get_mu * self._bille.get_velocity[1] # accélération en y
            self._bille.update_velocity(self._bille.get_acceleration[0], self._bille.get_acceleration[1], dt) # mise à jour de la vitesse
            self._bille.update_position(dt) # mise à jour de la position
            self._bille._xs.append(self._bille.get_x)
            self._bille._ys.append(self._bille.get_y)
            self._bille._zs.append(self._drap.h(self._bille.get_x, self._bille.get_y))
        self._plot()

    def _plot(self):
        fig = plt.figure(figsize=(9,6))
        ax = fig.add_subplot(111, projection='3d')
        grid = np.linspace(-3, 3, 150)
        X, Y = np.meshgrid(grid, grid)
        Z = self._drap.h(X, Y)
        ax.plot_surface(X, Y, Z, cmap='plasma', alpha=0.8)
        ax.plot_surface(self._sun.get_X_sun, self._sun.get_Y_sun, self._sun.get_Z_sun, color='gold', shade=True)
        animated_bille, = ax.plot([self._bille.get_positions_history[0][0]], [self._bille.get_positions_history[1][0]], [self._bille.get_positions_history[2][0] + 0.05], 'o', color='blue')
        
        def update(i):
            animated_bille.set_data([self._bille.get_positions_history[0][i]], [self._bille.get_positions_history[1][i]])
            animated_bille.set_3d_properties([self._bille.get_positions_history[2][i] + 0.05])
            return animated_bille,

        ani = animation.FuncAnimation(fig, update, frames=len(self._bille.get_positions_history[0]), interval=10, blit=True)
        ax.set_xlabel('x'); ax.set_ylabel('y'); ax.set_zlabel('z')
        ax.set_title("Bille orbitant et tombant vers le Soleil")
        self._set_axes_equal(ax)
        plt.show()

        
    def _set_axes_equal(self, ax):
        x_limits, y_limits, z_limits = ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()
        x_range, y_range, z_range = [abs(l[1] - l[0]) for l in (x_limits, y_limits, z_limits)]
        max_range = max(x_range, y_range, z_range)
        centers = [np.mean(l) for l in (x_limits, y_limits, z_limits)]
        ax.set_xlim3d([centers[0] - max_range / 2, centers[0] + max_range / 2])
        ax.set_ylim3d([centers[1] - max_range / 2, centers[1] + max_range / 2])
        ax.set_zlim3d([centers[2] - max_range / 2, centers[2] + max_range / 2])