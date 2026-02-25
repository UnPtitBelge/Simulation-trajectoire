from typing import List, Optional

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import QTimer

from simulations.sim3d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import deformation
from utils.params import PlotParams, Simulation3dParams


class Plot3d:
    def __init__(self, params: PlotParams = PlotParams()) -> None:
        self.params = params
        self.widget = gl.GLViewWidget()
        self.widget.setCameraPosition(distance=2, elevation=2, azimuth=2)

        # Animation state
        self.particle_trace = None
        self.trajectory_xs: List[float] = []
        self.trajectory_ys: List[float] = []
        self.trajectory_zs: List[float] = []
        self.current_frame = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation_frame)

    def setup_animation(
        self,
        sim_params: Optional[Simulation3dParams] = None,
        *,
        frame_interval_ms: int = 30,
    ) -> None:
        """Set up and start the animation."""
        self.sim_params = sim_params or Simulation3dParams()
        results = simulate_trajectory(self.sim_params, self.params)

        self.trajectory_xs = results["xs"]
        self.trajectory_ys = results["ys"]
        self.trajectory_zs = results["zs"]

        if not self.trajectory_xs:
            return

        # Start the animation
        self.current_frame = 0
        self._update_animation_frame()  # Draw the first frame immediately
        self.animation_timer.start(frame_interval_ms)

    def _update_animation_frame(self) -> None:
        """Update the particle position for the current frame."""
        if self.current_frame < len(self.trajectory_xs):
            x = self.trajectory_xs[self.current_frame]
            y = self.trajectory_ys[self.current_frame]
            z = self.trajectory_zs[self.current_frame]

            # Calculate the particle's Z position on top of the surface
            particle_z = z + self.sim_params.particle_radius / 2

            self._draw_particle(x, y, particle_z)
            self.current_frame += 1
        else:
            self.animation_timer.stop()

    def _draw_particle(self, x: float, y: float, z: float) -> None:
        """Draw or update the particle at the given position."""
        if self.particle_trace is not None:
            self.widget.removeItem(self.particle_trace)

        self.particle_trace = gl.GLScatterPlotItem(
            pos=np.array([[x, y, z]]),
            color=(1, 0.6, 0.6, 1.0),
            size=0.05,
            pxMode=False,
        )
        self.widget.addItem(self.particle_trace)

    def stop_animation(self) -> None:
        """Stop the animation."""
        self.animation_timer.stop()

    def reset_animation(self) -> None:
        """Reset the animation to the start."""
        self.stop_animation()
        self.current_frame = 0
        if self.trajectory_xs:
            self._draw_particle(
                self.trajectory_xs[0],
                self.trajectory_ys[0],
                self.trajectory_zs[0],
            )

    def redraw(self) -> None:
        """Redraw the surface and sphere."""
        for item in self.widget.items:
            if not isinstance(item, gl.GLGridItem):
                self.widget.removeItem(item)

        self._draw_surface()
        self._draw_center_sphere()

    def _draw_surface(self) -> None:
        """Draw the 3D surface."""
        R = float(self.params.surface_radius)
        T = float(self.params.surface_tension)
        F = float(self.params.center_weight)
        center_radius = float(self.params.center_radius)

        samples = 140
        extent = R
        xs = np.linspace(-extent, extent, samples)
        ys = np.linspace(-extent, extent, samples)
        X, Y = np.meshgrid(xs, ys)

        r = np.sqrt(X**2 + Y**2)
        Z = np.where(
            r <= R, deformation(r, R=R, T=T, F=F, center_radius=center_radius), np.nan
        )

        surface = gl.GLSurfacePlotItem(
            x=xs,
            y=ys,
            z=Z,
            color=(0.9, 0.9, 0.9, 1),
            shader="shaded",
            smooth=True,
        )
        self.widget.addItem(surface)

        self._add_surface_grid(X, Y, Z, 10)

    def _add_surface_grid(
        self, X: np.ndarray, Y: np.ndarray, Z: np.ndarray, step: int = 5
    ) -> None:
        """Add a grid to the surface."""
        rows, cols = X.shape
        for i in range(0, rows, step):
            line = gl.GLLinePlotItem(
                pos=np.column_stack((X[i, :], Y[i, :], Z[i, :])),
                color=(0, 0, 0, 0.3),
                width=0.5,
                antialias=True,
            )
            self.widget.addItem(line)
        for j in range(0, cols, step):
            line = gl.GLLinePlotItem(
                pos=np.column_stack((X[:, j], Y[:, j], Z[:, j])),
                color=(0, 0, 0, 0.3),
                width=0.5,
                antialias=True,
            )
            self.widget.addItem(line)

    def _draw_center_sphere(self) -> None:
        """Draw the center sphere."""
        R = self.params.surface_radius
        T = self.params.surface_tension
        F = self.params.center_weight
        center_radius = self.params.center_radius

        z_offset = (
            deformation(center_radius, R=R, T=T, F=F, center_radius=center_radius)
            + center_radius / 2
        )

        samples_theta = 32
        samples_phi = 32
        thetas = np.linspace(0, np.pi, samples_theta)
        phis = np.linspace(0, 2 * np.pi, samples_phi)
        Theta, Phi = np.meshgrid(thetas, phis, indexing="ij")

        X = center_radius * np.sin(Theta) * np.cos(Phi)
        Y = center_radius * np.sin(Theta) * np.sin(Phi)
        Z = z_offset + center_radius * np.cos(Theta)

        sphere = gl.GLMeshItem(
            vertexes=np.column_stack((X.ravel(), Y.ravel(), Z.ravel())),
            faces=self._generate_sphere_faces(samples_theta, samples_phi),
            color=(0, 0, 0, 1),
            shader="balloon",
            smooth=True,
        )
        self.widget.addItem(sphere)

    def _generate_sphere_faces(
        self, samples_theta: int, samples_phi: int
    ) -> np.ndarray:
        """Generate faces for the sphere mesh."""
        faces = []
        for i in range(samples_theta - 1):
            for j in range(samples_phi - 1):
                idx0 = i * samples_phi + j
                idx1 = i * samples_phi + (j + 1)
                idx2 = (i + 1) * samples_phi + j
                idx3 = (i + 1) * samples_phi + (j + 1)
                faces.append([idx0, idx1, idx2])
                faces.append([idx1, idx3, idx2])
        return np.array(faces)
