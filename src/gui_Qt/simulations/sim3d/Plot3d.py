from typing import Any, Optional

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtGui import QColor
from simulations.Plot import Plot
from simulations.sim3d.simulate_trajectory import simulate_trajectory
from utils.math_helpers import _deformation_scalar, deformation
from utils.params import Simulation3dParams
from utils.stylesheet import CLR_PLOT_BG


def _hex_to_qcolor(h: str) -> QColor:
    h = h.lstrip("#")
    return QColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


class Plot3d(Plot):
    """3-D surface simulation plot backed by a GLViewWidget.

    Attributes:
        sim_params:      Simulation3dParams controlling physics, initial
                         conditions, and surface geometry.
        widget:          The GLViewWidget used for all 3-D rendering.
        surface:         GLSurfacePlotItem for the deformable membrane.
        center_sphere:   GLMeshItem for the central heavy sphere.
        particle_trace:  GLMeshItem sphere for the moving particle, sized
                         by sim_params.particle_radius in world units.
        trajectory_xs:   x-coordinates of each trajectory frame [m].
        trajectory_ys:   y-coordinates of each trajectory frame [m].
        trajectory_zs:   Surface height at each trajectory frame [m].
    """

    def __init__(self, sim_params: Simulation3dParams = Simulation3dParams()) -> None:
        super().__init__(sim_params, frame_ms=10)

        self.sim_params = sim_params

        self.widget = gl.GLViewWidget()
        self.widget.setCameraPosition(distance=5, elevation=5, azimuth=5)
        self.widget.setBackgroundColor(_hex_to_qcolor(CLR_PLOT_BG))

        self.surface: Optional[Any] = None
        self.center_sphere: Optional[Any] = None
        self.particle_trace: Optional[Any] = None

        # Face indices are constant regardless of sphere radius or position;
        # pre-computing them avoids repeating the triangulation on every rebuild.
        self._sphere_faces = self._generate_sphere_faces(32, 32)

        self.trajectory_xs: list[float] = []
        self.trajectory_ys: list[float] = []
        self.trajectory_zs: list[float] = []

    # -----------------------------------------------------------------------
    # Abstract hook implementations
    # -----------------------------------------------------------------------

    def _prepare_simulation(self) -> None:
        results = simulate_trajectory(self.sim_params)
        self.trajectory_xs = results.get("xs", [])
        self.trajectory_ys = results.get("ys", [])
        self.trajectory_zs = results.get("zs", [])
        self._n_frames = len(self.trajectory_xs) if self.trajectory_xs else 0

    def _draw_initial_frame(self) -> None:
        """Rebuild static geometry and place the particle at frame 0.

        The particle must be added after the surface so it renders on top.
        It is removed and recreated on every call to enforce that order.
        """
        self._draw_center_sphere()
        self._draw_surface()

        if self.particle_trace is not None:
            try:
                self.widget.removeItem(self.particle_trace)
            except Exception:
                pass

        self._build_particle_mesh()
        self.widget.addItem(self.particle_trace)

        if self._n_frames > 0:
            self._update_frame(0)

    def _update_frame(self, frame_index: int) -> None:
        if self.particle_trace is None:
            return
        if frame_index < 0 or frame_index >= len(self.trajectory_xs):
            return

        x = self.trajectory_xs[frame_index]
        y = self.trajectory_ys[frame_index]
        z = self.trajectory_zs[frame_index]

        r = float(self.sim_params.particle_radius)
        verts = self._sphere_verts_at(x, y, z + r, r)
        self.particle_trace.setMeshData(vertexes=verts, faces=self._sphere_faces)

    # -----------------------------------------------------------------------
    # Particle mesh helpers
    # -----------------------------------------------------------------------

    def _build_particle_mesh(self) -> None:
        r = float(self.sim_params.particle_radius)
        self.particle_trace = gl.GLMeshItem(
            vertexes=self._sphere_verts_at(0.0, 0.0, 0.0, r),
            faces=self._sphere_faces,
            color=(0.88, 0.11, 0.27, 1.0),
            shader="balloon",
            smooth=True,
            drawEdges=False,
        )

    @staticmethod
    def _sphere_verts_at(
        cx: float,
        cy: float,
        cz: float,
        radius: float,
        samples_theta: int = 32,
        samples_phi: int = 32,
    ) -> np.ndarray:
        thetas = np.linspace(0, np.pi, samples_theta)
        phis = np.linspace(0, 2 * np.pi, samples_phi)
        Theta, Phi = np.meshgrid(thetas, phis, indexing="ij")
        X = cx + radius * np.sin(Theta) * np.cos(Phi)
        Y = cy + radius * np.sin(Theta) * np.sin(Phi)
        Z = cz + radius * np.cos(Theta)
        return np.column_stack((X.ravel(), Y.ravel(), Z.ravel()))

    # -----------------------------------------------------------------------
    # Static geometry builders
    # -----------------------------------------------------------------------

    def _draw_surface(self) -> None:
        """Rebuild the deformable membrane mesh.

        Samples the deformation function on a 140x140 grid. Points outside
        radius R are set to NaN so GLSurfacePlotItem clips them cleanly.
        """
        if self.surface is not None:
            try:
                self.widget.removeItem(self.surface)
            except Exception:
                pass

        R = float(self.sim_params.surface_radius)
        T = float(self.sim_params.surface_tension)
        F = float(self.sim_params.center_mass) * float(self.sim_params.g)
        center_radius = float(self.sim_params.center_radius)

        samples = 140
        xs = np.linspace(-R, R, samples)
        ys = np.linspace(-R, R, samples)
        X, Y = np.meshgrid(xs, ys)
        r = np.sqrt(X**2 + Y**2)
        Z = np.where(
            r <= R,
            deformation(r, R=R, T=T, F=F, center_radius=center_radius),
            np.nan,
        )

        self.surface = gl.GLSurfacePlotItem(
            x=xs,
            y=ys,
            z=Z,
            color=(0.31, 0.27, 0.90, 0.82),
            shader="shaded",
            smooth=True,
        )
        self.widget.addItem(self.surface)

    def _draw_center_sphere(self) -> None:
        """Rebuild the central heavy sphere mesh.

        The sphere is positioned so its equator sits at the membrane level
        at r = center_radius.
        """
        if self.center_sphere is not None:
            try:
                self.widget.removeItem(self.center_sphere)
            except Exception:
                pass

        R = self.sim_params.surface_radius
        T = self.sim_params.surface_tension
        F = self.sim_params.center_mass * self.sim_params.g
        center_radius = self.sim_params.center_radius

        z_offset = (
            _deformation_scalar(
                center_radius, R=R, T=T, F=F, center_radius=center_radius
            )
            + center_radius / 2
        )

        self.center_sphere = gl.GLMeshItem(
            vertexes=self._sphere_verts_at(0.0, 0.0, z_offset, center_radius),
            faces=self._sphere_faces,
            color=(0.09, 0.64, 0.29, 1.0),
            shader="balloon",
            smooth=True,
        )
        self.widget.addItem(self.center_sphere)

    def _generate_sphere_faces(
        self, samples_theta: int, samples_phi: int
    ) -> np.ndarray:
        """Build a triangle face index array for a UV sphere.

        Uses fan triangles at the poles to avoid degenerate quads that cause
        pyqtgraph's MeshData normaliser to emit divide warnings.
        """
        faces = []

        for i in range(1, samples_theta - 1):
            for j in range(samples_phi - 1):
                idx0 = i * samples_phi + j
                idx1 = i * samples_phi + (j + 1)
                idx2 = (i + 1) * samples_phi + j
                idx3 = (i + 1) * samples_phi + (j + 1)
                faces.append([idx0, idx1, idx2])
                faces.append([idx1, idx3, idx2])

        for j in range(samples_phi - 1):
            pole = 0
            ring_a = 1 * samples_phi + j
            ring_b = 1 * samples_phi + (j + 1)
            faces.append([pole, ring_b, ring_a])

        last_ring = (samples_theta - 2) * samples_phi
        for j in range(samples_phi - 1):
            pole = (samples_theta - 1) * samples_phi
            ring_a = last_ring + j
            ring_b = last_ring + (j + 1)
            faces.append([pole, ring_a, ring_b])

        return np.array(faces, dtype=np.uint32)

    # -----------------------------------------------------------------------
    # Parameter update
    # -----------------------------------------------------------------------

    def update_params(self, **kwargs) -> None:
        super().update_params(**kwargs)
