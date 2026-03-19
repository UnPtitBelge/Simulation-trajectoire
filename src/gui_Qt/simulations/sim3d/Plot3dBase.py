"""Shared OpenGL rendering base for 3-D surface simulations.

Both the cone (Newton) and membrane (Laplace) plots inherit from this
class and override only their surface-specific methods.

Subclass contract
-----------------
A concrete subclass must implement:

* ``_prepare_simulation()``  — run the integrator, populate trajectory lists
  and set ``self._n_frames``.
* ``_surface_z(r)``          — return the surface height z [m] at radius r [m].
  Used to position the central sphere equator flush with the surface.
* ``_draw_surface()``        — build and register the ``GLSurfacePlotItem``
  with ``self.widget``.  Must store it in ``self.surface`` so the base
  class can remove the old mesh before rebuilding.

Everything else — particle mesh, trajectory line, playback, shortcuts —
is handled here.
"""
from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, Optional

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from simulations.Plot import Plot
from utils.stylesheet import CLR_PLOT_CENTER, CLR_PLOT_PARTICLE, CLR_PLOT_BG
from utils.ui_constants import (
    SIM3D_TRAIL_CAP, SIM3D_TRAIL_SKIP, SIM3D_SPHERE_RES,
    SIM3D_TRAIL_W, SIM3D_TRAIL_ALPHA,
    SIM3D_POLAR_NR, SIM3D_POLAR_NPHI,
    SIM3D_CAM_DIST, SIM3D_CAM_ELEV, SIM3D_CAM_AZ,
)

log = logging.getLogger(__name__)


def _hex_to_qcolor(h: str) -> QColor:
    h = h.lstrip("#")
    return QColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


class Plot3dBase(Plot):
    """Abstract OpenGL base for 3-D surface simulations.

    Attributes
    ----------
    widget           GLViewWidget used for all rendering.
    surface          GLSurfacePlotItem for the deformed surface mesh.
    center_sphere    GLMeshItem for the central body sphere.
    particle_trace   GLMeshItem for the animated moving particle.
    trajectory_line  Optional GLLinePlotItem for the particle trail.
    trajectory_xs/ys/zs/vxs/vys  Per-frame trajectory data (lists of float).
    show_trajectory_trail  Toggle for the particle trail overlay.
    """

    def __init__(self, sim_params, frame_ms: int = 10) -> None:
        super().__init__(sim_params, frame_ms=frame_ms)
        self.sim_params = sim_params

        self.widget = gl.GLViewWidget()
        self.widget.setCameraPosition(distance=SIM3D_CAM_DIST, elevation=SIM3D_CAM_ELEV, azimuth=SIM3D_CAM_AZ)
        self.widget.setBackgroundColor(_hex_to_qcolor(CLR_PLOT_BG))

        # Face indices are constant regardless of sphere radius or position;
        # pre-computing them avoids repeating the triangulation on every rebuild.
        self._sphere_faces = self._generate_sphere_faces(SIM3D_SPHERE_RES, SIM3D_SPHERE_RES)

        self.surface:         Optional[Any] = None
        self.center_sphere:   Optional[Any] = None
        self.particle_trace:  Optional[Any] = None
        self.trajectory_line: Optional[Any] = None
        self.show_trajectory_trail = True

        self.trajectory_xs:  list[float] = []
        self.trajectory_ys:  list[float] = []
        self.trajectory_zs:  list[float] = []
        self.trajectory_vxs: list[float] = []
        self.trajectory_vys: list[float] = []

        self.shortcut_traj = QShortcut(QKeySequence("Ctrl+T"), self.widget)
        self.shortcut_traj.activated.connect(self.toggle_trajectory)

    # -----------------------------------------------------------------------
    # Abstract interface for subclasses
    # -----------------------------------------------------------------------

    @abstractmethod
    def _surface_z(self, r: float) -> float:
        """Surface height z [m] at radial distance r [m]."""
        ...

    @abstractmethod
    def _draw_surface(self) -> None:
        """Rebuild the surface mesh and register it with ``self.widget``."""
        ...

    # -----------------------------------------------------------------------
    # Plot abstract hook implementations (shared logic)
    # -----------------------------------------------------------------------

    def _draw_initial_frame(self) -> None:
        """Rebuild static geometry and place the particle at frame 0.

        Rendering order:
        1. center_sphere — added first so it appears behind the surface.
        2. surface       — the funnel-shaped mesh.
        3. particle      — must be last so it renders on top.
        """
        self._draw_center_sphere()
        self._draw_surface()

        for item in (self.particle_trace, self.trajectory_line):
            if item is not None:
                try:
                    self.widget.removeItem(item)
                except Exception:
                    pass
        self.trajectory_line = None

        self._build_particle_mesh()
        self.widget.addItem(self.particle_trace)

        if self._n_frames > 0:
            self._update_frame(0)
            self.frame_updated.emit(0)

    def _update_frame(self, frame_index: int) -> None:
        if self.particle_trace is None:
            return
        if not (0 <= frame_index < len(self.trajectory_xs)):
            return

        x = self.trajectory_xs[frame_index]
        y = self.trajectory_ys[frame_index]
        z = self.trajectory_zs[frame_index]
        r = float(self.sim_params.particle_radius)

        # Déplacer la bille via la matrice de transformation — pas de recalcul
        # des vertices à chaque frame (remplace l'ancien setMeshData).
        self.particle_trace.resetTransform()
        self.particle_trace.translate(x, y, z + r)

        # Trait de trajectoire : cappé à SIM3D_TRAIL_CAP points, mis à jour tous les
        # SIM3D_TRAIL_SKIP frames pour éviter un setData croissant à chaque tick.
        if self.show_trajectory_trail and frame_index % SIM3D_TRAIL_SKIP == 0:
            start = max(0, frame_index + 1 - SIM3D_TRAIL_CAP)
            pts = np.column_stack((
                self.trajectory_xs[start:frame_index + 1],
                self.trajectory_ys[start:frame_index + 1],
                self.trajectory_zs[start:frame_index + 1],
            ))
            if self.trajectory_line is None:
                self.trajectory_line = gl.GLLinePlotItem(
                    pos=pts, color=(1.0, 1.0, 1.0, SIM3D_TRAIL_ALPHA),
                    width=SIM3D_TRAIL_W, antialias=True,
                )
                self.widget.addItem(self.trajectory_line)
            else:
                self.trajectory_line.setData(pos=pts)

    # -----------------------------------------------------------------------
    # Trajectory trail toggle
    # -----------------------------------------------------------------------

    def toggle_trajectory(self) -> None:
        """Toggle the particle trail visibility (Ctrl+T shortcut).

        When re-enabled the trail is rebuilt from the already-computed
        trajectory data up to the current frame.
        """
        self.show_trajectory_trail = not self.show_trajectory_trail
        if not self.show_trajectory_trail:
            if self.trajectory_line is not None:
                try:
                    self.widget.removeItem(self.trajectory_line)
                except Exception:
                    pass
                self.trajectory_line = None
        elif self.trajectory_xs:
            start = max(0, self.current_frame - SIM3D_TRAIL_CAP)
            pts = np.column_stack((
                self.trajectory_xs[start:self.current_frame],
                self.trajectory_ys[start:self.current_frame],
                self.trajectory_zs[start:self.current_frame],
            ))
            self.trajectory_line = gl.GLLinePlotItem(
                pos=pts, color=(1.0, 1.0, 1.0, SIM3D_TRAIL_ALPHA),
                width=SIM3D_TRAIL_W, antialias=True,
            )
            self.widget.addItem(self.trajectory_line)

    # -----------------------------------------------------------------------
    # Shared static geometry builders
    # -----------------------------------------------------------------------

    def _draw_center_sphere(self) -> None:
        """Rebuild the central sphere, positioning its equator flush with the surface.

        Removes the old ``center_sphere`` item (if any) and creates a new
        ``GLMeshItem`` centred so that the sphere's equator sits at the
        surface height ``_surface_z(center_radius)``.
        """
        if self.center_sphere is not None:
            try:
                self.widget.removeItem(self.center_sphere)
            except Exception:
                pass

        cr = self.sim_params.center_radius
        # Sphere centre = surface z at contact radius + one sphere radius,
        # so the equator (centre − radius) sits flush with the surface.
        z_offset = self._surface_z(cr) + cr

        self.center_sphere = gl.GLMeshItem(
            vertexes=self._sphere_verts_at(0.0, 0.0, z_offset, cr),
            faces=self._sphere_faces,
            color=_hex_to_qcolor(CLR_PLOT_CENTER),
            shader="balloon",
            smooth=True,
        )
        self.widget.addItem(self.center_sphere)

    def _build_particle_mesh(self) -> None:
        """Create the moving-particle GLMeshItem placed at the world origin.

        The mesh is not added to the widget here — ``_draw_initial_frame``
        calls ``widget.addItem`` after calling this method.
        """
        r = float(self.sim_params.particle_radius)
        self.particle_trace = gl.GLMeshItem(
            vertexes=self._sphere_verts_at(0.0, 0.0, 0.0, r),
            faces=self._sphere_faces,
            color=_hex_to_qcolor(CLR_PLOT_PARTICLE),
            shader="balloon",
            smooth=True,
            drawEdges=False,
        )

    # -----------------------------------------------------------------------
    # Polar surface mesh helper (pure geometry, no Qt side-effects)
    # -----------------------------------------------------------------------

    @staticmethod
    def _polar_surface_mesh(
        z_func,
        R: float,
        center_r: float,
        n_r: int = SIM3D_POLAR_NR,
        n_phi: int = SIM3D_POLAR_NPHI,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Construit un maillage circulaire en coordonnées polaires.

        Contrairement à un grille cartésienne avec masque NaN, ce maillage
        a un bord extérieur parfaitement circulaire — plus d'effet d'escalier.

        Parameters
        ----------
        z_func   Callable r → z, vectorisé NumPy.
        R        Rayon extérieur du disque [m].
        center_r Rayon intérieur (sphère centrale) [m].
        n_r      Nombre d'anneaux radiaux.
        n_phi    Nombre de segments angulaires.

        Returns
        -------
        verts  (n_r*n_phi, 3) float32
        faces  (2*(n_r-1)*n_phi, 3) uint32
        """
        r_arr   = np.linspace(center_r, R, n_r)
        phi_arr = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)

        R_g   = np.tile(r_arr[:, np.newaxis],   (1, n_phi))
        Phi_g = np.tile(phi_arr[np.newaxis, :], (n_r, 1))

        X = (R_g * np.cos(Phi_g)).ravel()
        Y = (R_g * np.sin(Phi_g)).ravel()
        Z = z_func(R_g.ravel())
        verts = np.column_stack((X, Y, Z)).astype(np.float32)

        faces = []
        for i in range(n_r - 1):
            for j in range(n_phi):
                j1 = (j + 1) % n_phi
                a = i       * n_phi + j
                b = i       * n_phi + j1
                c = (i + 1) * n_phi + j
                d = (i + 1) * n_phi + j1
                faces.append([a, c, b])
                faces.append([b, c, d])

        return verts, np.array(faces, dtype=np.uint32)

    # -----------------------------------------------------------------------
    # Sphere mesh helpers (pure geometry, no Qt side-effects)
    # -----------------------------------------------------------------------

    @staticmethod
    def _sphere_verts_at(
        cx: float,
        cy: float,
        cz: float,
        radius: float,
        samples_theta: int = 32,
        samples_phi: int = 32,
    ) -> np.ndarray:
        """Return UV-sphere vertex array centred at (cx, cy, cz)."""
        thetas = np.linspace(0, np.pi, samples_theta)
        phis   = np.linspace(0, 2 * np.pi, samples_phi)
        Theta, Phi = np.meshgrid(thetas, phis, indexing="ij")
        X = cx + radius * np.sin(Theta) * np.cos(Phi)
        Y = cy + radius * np.sin(Theta) * np.sin(Phi)
        Z = cz + radius * np.cos(Theta)
        return np.column_stack((X.ravel(), Y.ravel(), Z.ravel()))

    @staticmethod
    def _generate_sphere_faces(
        samples_theta: int,
        samples_phi: int,
    ) -> np.ndarray:
        """Build triangle face indices for a UV sphere.

        Uses fan triangles at the poles to avoid degenerate quads.
        """
        faces = []

        # Body quads (rows between the two pole rings)
        for i in range(1, samples_theta - 1):
            for j in range(samples_phi - 1):
                i0 = i       * samples_phi + j
                i1 = i       * samples_phi + (j + 1)
                i2 = (i + 1) * samples_phi + j
                i3 = (i + 1) * samples_phi + (j + 1)
                faces.append([i0, i1, i2])
                faces.append([i1, i3, i2])

        # North-pole fan
        for j in range(samples_phi - 1):
            faces.append([0, 1 * samples_phi + (j + 1), 1 * samples_phi + j])

        # South-pole fan
        last_ring = (samples_theta - 2) * samples_phi
        south     = (samples_theta - 1) * samples_phi
        for j in range(samples_phi - 1):
            faces.append([south, last_ring + j, last_ring + (j + 1)])

        return np.array(faces, dtype=np.uint32)

    def update_params(self, **kwargs) -> None:
        """Update simulation parameters and recompute.

        Delegates to ``Plot.update_params`` which applies the changes to
        ``sim_params`` and re-runs ``setup_animation``.
        """
        super().update_params(**kwargs)
