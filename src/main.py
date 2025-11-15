import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from constantes import *
from soleil import Soleil
from drap import Drap
from bille import Bille


sun = Soleil(sun_radius, M_sun)
drap = Drap(k_depth, k_sigma, M_sun, sun_radius, mu)
bille = Bille(x, y, vx, vy)

for i in range(steps):
    r = np.sqrt(bille.get_x**2 + bille.get_y**2) # distance bille-Soleil
    if r < sun.get_radius:  # contact avec le Soleil
        break
    bille.set_ax = -G * sun.get_mass * bille.get_x / r**3 - drap.get_mu * bille.get_velocity[0] # accélération en x
    bille.set_ay = -G * sun.get_mass * bille.get_y / r**3 - drap.get_mu * bille.get_velocity[1] # accélération en y
    bille.update_velocity(bille.get_acceleration[0], bille.get_acceleration[1], dt) # mise à jour de la vitesse
    bille.update_position(dt) # mise à jour de la position
    bille._xs.append(bille.get_x)
    bille._ys.append(bille.get_y)
    bille._zs.append(drap.h(bille.get_x, bille.get_y))

# Affichage 3D du drap, du Soleil et de la bille
fig = plt.figure(figsize=(9,6))
ax = fig.add_subplot(111, projection='3d')
grid = np.linspace(-3, 3, 150)
X, Y = np.meshgrid(grid, grid)
Z = drap.h(X, Y)
ax.plot_surface(X, Y, Z, cmap='plasma', alpha=0.8)

# Plot le Soleil
ax.plot_surface(sun.get_X_sun, sun.get_Y_sun, sun.get_Z_sun, color='gold', shade=True)

# Bille animée
animated_bille, = ax.plot([bille.get_positions_history[0][0]], [bille.get_positions_history[1][0]], [bille.get_positions_history[2][0]+0.05], 'o', color='blue')

def set_axes_equal(ax):
    x_limits, y_limits, z_limits = ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()
    x_range, y_range, z_range = [abs(l[1]-l[0]) for l in (x_limits, y_limits, z_limits)]
    max_range = max(x_range, y_range, z_range)
    centers = [np.mean(l) for l in (x_limits, y_limits, z_limits)]
    ax.set_xlim3d([centers[0]-max_range/2, centers[0]+max_range/2])
    ax.set_ylim3d([centers[1]-max_range/2, centers[1]+max_range/2])
    ax.set_zlim3d([centers[2]-max_range/2, centers[2]+max_range/2])

def update(i):
    animated_bille.set_data([bille.get_positions_history[0][i]], [bille.get_positions_history[1][i]])
    animated_bille.set_3d_properties([bille.get_positions_history[2][i] + 0.05])
    return animated_bille,

ani = animation.FuncAnimation(fig, update, frames=len(bille.get_positions_history[0]), interval=10, blit=True)
ax.set_xlabel('x'); ax.set_ylabel('y'); ax.set_zlabel('z')
ax.set_title("Bille orbitant et tombant vers le Soleil")
set_axes_equal(ax)
plt.show()
