from typing import Any, Optional

from simulations.Plot import Plot
from simulations.sim3d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import deformation
from utils.params import PlotParams, Simulation3dParams

import numpy as np
import pyqtgraph.opengl as gl


class Plot3d(Plot):
    """3D plot wrapper for the surface + particle simulation.

    Inherits common animation and parameter handling from `Plot` and implements:
      - _prepare_simulation: runs simulate_trajectory and populates frame arrays
      - _update_frame: renders the particle position for a frame
      - _draw_surface/_draw_center_sphere: static geometry rendering
    """

    def __init__(
        self,
        params: PlotParams = PlotParams(),
        sim_params: Simulation3dParams = Simulation3dParams(),
    ) -> None:
        # set default frame interval similar to previous implementation (30 ms)
        super().__init__(sim_params, params, frame_ms=30)

        self.params = params
        self.sim_params = sim_params

        # Create GL view widget
        self.widget = gl.GLViewWidget()
        self.widget.setCameraPosition(distance=10, elevation=10, azimuth=10)

        # Visual handles
        self.particle_trace: Optional[Any] = None
        self.surface: Optional[Any] = None
        self.center_sphere: Optional[Any] = None

        # Trajectory storage filled by _prepare_simulation
        self.trajectory_xs = []
        self.trajectory_ys = []
        self.trajectory_zs = []

    def _prepare_simulation(self) -> None:
        """Run the simulation and populate trajectory arrays and frame count."""
        results = simulate_trajectory(self.sim_params, self.params)

        self.trajectory_xs = results.get("xs", [])
        self.trajectory_ys = results.get("ys", [])
        self.trajectory_zs = results.get("zs", [])
        self._n_frames = (
            len(self.trajectory_xs) if self.trajectory_xs is not None else 0
        )

        # Draw static geometry and place the first frame
        self._draw_center_sphere()
        self._draw_surface()

    def _update_frame(self, frame_index: int) -> None:
        """Render the particle for the given frame index."""
        if frame_index < 0 or frame_index >= len(self.trajectory_xs):
            return

        x = self.trajectory_xs[frame_index]
        y = self.trajectory_ys[frame_index]
        z = self.trajectory_zs[frame_index]

        # Particle sits slightly above surface
        particle_z = z + self.sim_params.particle_radius / 2.0
        self._draw_particle(x, y, particle_z)

    def _draw_particle(self, x: float, y: float, z: float) -> None:
        """Draw or update the particle marker in the GL scene."""
        try:
            if self.particle_trace is not None:
                self.widget.removeItem(self.particle_trace)
        except Exception:
            pass

        self.particle_trace = gl.GLScatterPlotItem(
            pos=np.array([[x, y, z]]),
            color=(1, 0.6, 0.6, 1.0),
            size=0.05,
            pxMode=False,
        )
        self.widget.addItem(self.particle_trace)

    def start_animation(self, frame_interval_ms: int = None) -> None:
        """Start the animation; accepts optional frame interval (ms)."""
        if frame_interval_ms is not None:
            self.set_frame_interval(frame_interval_ms)
        super().start_animation()

    def stop_animation(self) -> None:
        """Stop the animation."""
        super().stop_animation()

    def reset_animation(self) -> None:
        """Reset animation and redraw static geometry and first particle frame."""
        super().reset_animation()
        # ensure surface and center sphere are up-to-date
        try:
            self._draw_surface()
            self._draw_center_sphere()
        except Exception:
            pass

    def _draw_surface(self) -> None:
        """Draw or update the 3D surface mesh."""
        try:
            if self.surface is not None:
                self.widget.removeItem(self.surface)
        except Exception:
            pass

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

        self.surface = gl.GLSurfacePlotItem(
            x=xs,
            y=ys,
            z=Z,
            color=(0.9, 0.9, 0.9, 1),
            shader="shaded",
            smooth=True,
        )
        self.widget.addItem(self.surface)

    def _add_surface_grid(
        self, X: np.ndarray, Y: np.ndarray, Z: np.ndarray, step: int = 5
    ) -> None:
        """Add a grid to the surface (kept for compatibility)."""
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
        """Draw the center sphere mesh used to represent the central mass."""
        try:
            if self.center_sphere is not None:
                self.widget.removeItem(self.center_sphere)
        except Exception:
            pass

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

        self.center_sphere = gl.GLMeshItem(
            vertexes=np.column_stack((X.ravel(), Y.ravel(), Z.ravel())),
            faces=self._generate_sphere_faces(samples_theta, samples_phi),
            color=(0, 0, 0, 1),
            shader="balloon",
            smooth=True,
        )
        self.widget.addItem(self.center_sphere)

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

    def update_params(self, **kwargs) -> None:
        """Update simulation parameters and restart the animation."""
        for key, value in kwargs.items():
            if hasattr(self.sim_params, key):
                setattr(self.sim_params, key, value)
            if hasattr(self.params, key):
                setattr(self.params, key, value)

        # Re-run the simulation and reset the animation
        self.setup_animation()
