from typing import Any, Optional

import numpy as np
import pyqtgraph.opengl as gl
from simulations.Plot import Plot
from simulations.sim3d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import deformation
from utils.params import PlotParams, Simulation3dParams


class Plot3d(Plot):
    """3D plot wrapper for the surface + particle simulation."""

    def __init__(
        self,
        params: PlotParams = PlotParams(),
        sim_params: Simulation3dParams = Simulation3dParams(),
    ) -> None:
        super().__init__(sim_params, params, frame_ms=30)

        self.params = params
        self.sim_params = sim_params

        self.widget = gl.GLViewWidget()
        self.widget.setCameraPosition(distance=5, elevation=5, azimuth=5)

        self.surface: Optional[Any] = None
        self.center_sphere: Optional[Any] = None

        # Particle created lazily in _draw_initial_frame so it is always added
        # AFTER the surface — this guarantees correct GL depth ordering.
        self.particle_trace: Optional[Any] = None

        self._sphere_faces = self._generate_sphere_faces(32, 32)

        self.trajectory_xs = []
        self.trajectory_ys = []
        self.trajectory_zs = []

    # ------------------------------------------------------------------ #
    # Abstract hooks                                                       #
    # ------------------------------------------------------------------ #

    def _prepare_simulation(self) -> None:
        """Run the simulation — data only, no GL calls here."""
        results = simulate_trajectory(self.sim_params, self.params)
        self.trajectory_xs = results.get("xs", [])
        self.trajectory_ys = results.get("ys", [])
        self.trajectory_zs = results.get("zs", [])
        self._n_frames = len(self.trajectory_xs) if self.trajectory_xs else 0

    def _draw_initial_frame(self) -> None:
        """Rebuild static geometry, then add particle on top (GL order matters)."""
        self._draw_center_sphere()
        self._draw_surface()
        # (Re)create particle AFTER surface so it is rendered on top in the GL pipeline
        if self.particle_trace is not None:
            try:
                self.widget.removeItem(self.particle_trace)
            except Exception:
                pass
        self.particle_trace = gl.GLScatterPlotItem(
            pos=np.array([[0.0, 0.0, 0.0]]),
            color=(1, 0.2, 0.2, 1.0),
            size=8,  # pixels — pxMode=True (default) is reliable across drivers
            pxMode=True,  # screen-space size: always visible regardless of zoom/depth
        )
        self.widget.addItem(self.particle_trace)
        if self._n_frames > 0:
            self._update_frame(0)

    def _update_frame(self, frame_index: int) -> None:
        """Move the particle via setData() — no removeItem/addItem."""
        if self.particle_trace is None:
            return
        if frame_index < 0 or frame_index >= len(self.trajectory_xs):
            return
        x = self.trajectory_xs[frame_index]
        y = self.trajectory_ys[frame_index]
        # z is now the surface height at (x,y) after integration — only a small
        # visual clearance offset (half radius) to sit on top of the mesh surface.
        z = self.trajectory_zs[frame_index]
        self.particle_trace.setData(pos=np.array([[x, y, z]]))

    # ------------------------------------------------------------------ #
    # Animation lifecycle                                                  #
    # ------------------------------------------------------------------ #

    def start_animation(self, frame_interval_ms: int | None = None) -> None:
        if frame_interval_ms is not None:
            self.set_frame_interval(frame_interval_ms)
        super().start_animation()

    def reset_animation(self) -> None:
        """Reset to frame 0 — static geometry does NOT need to be rebuilt."""
        super().reset_animation()

    # ------------------------------------------------------------------ #
    # Static geometry (expensive — called only when params change)        #
    # ------------------------------------------------------------------ #

    def _draw_surface(self) -> None:
        """Rebuild the surface mesh. Called once per param change, not per frame."""
        if self.surface is not None:
            try:
                self.widget.removeItem(self.surface)
            except Exception:
                pass

        R = float(self.params.surface_radius)
        T = float(self.params.surface_tension)
        F = float(self.params.center_weight)
        center_radius = float(self.params.center_radius)

        samples = 140
        xs = np.linspace(-R, R, samples)
        ys = np.linspace(-R, R, samples)
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

    def _draw_center_sphere(self) -> None:
        """Rebuild the central sphere. Called once per param change, not per frame."""
        if self.center_sphere is not None:
            try:
                self.widget.removeItem(self.center_sphere)
            except Exception:
                pass

        R = self.params.surface_radius
        T = self.params.surface_tension
        F = self.params.center_weight
        center_radius = self.params.center_radius

        z_offset = (
            float(
                deformation(center_radius, R=R, T=T, F=F, center_radius=center_radius)
            )
            + center_radius / 2
        )

        samples_theta, samples_phi = 32, 32
        thetas = np.linspace(0, np.pi, samples_theta)
        phis = np.linspace(0, 2 * np.pi, samples_phi)
        Theta, Phi = np.meshgrid(thetas, phis, indexing="ij")

        X = center_radius * np.sin(Theta) * np.cos(Phi)
        Y = center_radius * np.sin(Theta) * np.sin(Phi)
        Z = z_offset + center_radius * np.cos(Theta)

        self.center_sphere = gl.GLMeshItem(
            vertexes=np.column_stack((X.ravel(), Y.ravel(), Z.ravel())),
            faces=self._sphere_faces,  # reuse precomputed faces
            color=(0, 0, 0, 1),
            shader="balloon",
            smooth=True,
        )
        self.widget.addItem(self.center_sphere)

    def _generate_sphere_faces(
        self, samples_theta: int, samples_phi: int
    ) -> np.ndarray:
        """Generate triangle faces avoiding degenerate pole faces that cause
        'invalid value encountered in divide' in pyqtgraph's MeshData normalizer.

        The north (theta=0) and south (theta=pi) poles are single vertices,
        connected to the first/last ring with fan triangles instead of quads.
        """
        faces = []
        # Body quads (skip first and last ring — those connect to the poles)
        for i in range(1, samples_theta - 2):
            for j in range(samples_phi - 1):
                idx0 = i * samples_phi + j
                idx1 = i * samples_phi + (j + 1)
                idx2 = (i + 1) * samples_phi + j
                idx3 = (i + 1) * samples_phi + (j + 1)
                faces.append([idx0, idx1, idx2])
                faces.append([idx1, idx3, idx2])

        # North-pole fan (ring i=0 → all map to the same vertex, skip them;
        # connect ring i=1 to the first vertex of ring i=0 as a proxy)
        for j in range(samples_phi - 1):
            pole = 0 * samples_phi  # all pole verts are the same point
            ring_a = 1 * samples_phi + j
            ring_b = 1 * samples_phi + (j + 1)
            faces.append([pole, ring_b, ring_a])

        # South-pole fan
        last_ring = (samples_theta - 2) * samples_phi
        for j in range(samples_phi - 1):
            pole = (samples_theta - 1) * samples_phi
            ring_a = last_ring + j
            ring_b = last_ring + (j + 1)
            faces.append([pole, ring_a, ring_b])

        return np.array(faces, dtype=np.uint32)

    def update_params(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self.sim_params, key):
                setattr(self.sim_params, key, value)
            if hasattr(self.params, key):
                setattr(self.params, key, value)
        self.setup_animation()
