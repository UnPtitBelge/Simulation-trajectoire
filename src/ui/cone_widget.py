"""Vue Cône — simulation 3D sur surface conique (pyqtgraph OpenGL)."""

import math

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy

from utils.angle import v0_dir_to_vr_vtheta

from config.theme import (
    RGB_CENTER_BALL, RGB_MARKER,
    RGB_PLOT_GRAY, RGB_PLOT_ORANGE, RGB_PLOT_PARTICLE,
)
from physics.cone import compute_cone
from ui.base_sim_widget import BaseSimWidget


def _cone_surface_mesh(R: float, slope: float, n_r: int = 30, n_theta: int = 60) -> gl.GLMeshItem:
    r_vals = np.linspace(0.0, R, n_r)
    t_vals = np.linspace(0.0, 2 * math.pi, n_theta, endpoint=False)
    r_g, t_g = np.meshgrid(r_vals, t_vals, indexing="ij")

    xs = (r_g * np.cos(t_g)).flatten()
    ys = (r_g * np.sin(t_g)).flatten()
    zs = (-slope * (R - r_g)).flatten()
    verts = np.column_stack([xs, ys, zs])

    faces = []
    for ir in range(n_r - 1):
        for it in range(n_theta):
            it_next = (it + 1) % n_theta
            a = ir * n_theta + it
            b = ir * n_theta + it_next
            c = (ir + 1) * n_theta + it
            d = (ir + 1) * n_theta + it_next
            faces += [[a, b, c], [b, d, c]]

    mesh = gl.GLMeshItem(
        vertexes=verts.astype(np.float32),
        faces=np.array(faces, dtype=np.int32),
        color=(*RGB_PLOT_GRAY[:3], 0.4),
        smooth=True, drawEdges=False,
    )
    return mesh


class ConeWidget(BaseSimWidget):
    R_MAX = 0.4

    def __init__(self, cfg: dict, parent=None):
        super().__init__(cfg, parent)
        phys = cfg["physics"]
        self.R_MAX       = phys["R"]
        self._slope      = phys["depth"] / phys["R"]
        self._ball_r     = phys.get("ball_radius",   0.01)
        self._center_r   = phys.get("center_radius", 0.05)
        self._traj: np.ndarray | None = None

        # ── OpenGL ──
        self._gl: gl.GLViewWidget = gl.GLViewWidget()
        self._gl.setCameraPosition(distance=1.2, elevation=30, azimuth=45)
        self._gl.setBackgroundColor("k")
        self._gl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._gl.setMinimumSize(300, 300)
        self._gl.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        mesh = _cone_surface_mesh(self.R_MAX, self._slope)
        self._gl.addItem(mesh)

        grid = gl.GLGridItem()
        grid.setSize(self.R_MAX * 2.5, self.R_MAX * 2.5)
        grid.setSpacing(0.1, 0.1)
        self._gl.addItem(grid)

        self._particle = gl.GLScatterPlotItem(
            pos=np.zeros((1, 3)), size=self._ball_r * 2,
            color=RGB_PLOT_PARTICLE, pxMode=False,
        )
        self._gl.addItem(self._particle)

        self._trail = gl.GLLinePlotItem(
            pos=np.zeros((1, 3)), color=RGB_PLOT_ORANGE, width=2, antialias=True,
        )
        self._gl.addItem(self._trail)

        # Centre de la bille = surface au sommet + un rayon (bille posée sur la surface)
        center_z = -self._slope * self.R_MAX + self._center_r
        self._center = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, center_z]]), size=self._center_r * 2,
            color=RGB_CENTER_BALL, pxMode=False,
        )
        self._gl.addItem(self._center)

        self._marker_items: list[gl.GLScatterPlotItem] = []
        self._init_plot(self._gl)

    # ── Simulation ────────────────────────────────────────────────────────────

    def _compute(self) -> None:
        p    = self._params
        phys = self._cfg["physics"]
        vr0, vtheta0 = v0_dir_to_vr_vtheta(p["v0"], p["direction_deg"])
        self._traj = compute_cone(
            r0=p["r0"], theta0=p["theta0"], vr0=vr0, vtheta0=vtheta0,
            R=phys["R"], depth=phys["depth"], friction=phys["friction"],
            g=phys["g"], dt=phys["dt"], n_steps=phys["n_steps"],
        )
        self._n_frames = len(self._traj)

    def _xyz(self, r: float, theta: float) -> tuple[float, float, float]:
        return r * math.cos(theta), r * math.sin(theta), -self._slope * (self.R_MAX - r)

    def _draw_initial(self) -> None:
        if self._traj is None:
            return
        self._draw(0)

    def _draw(self, frame: int) -> None:
        if self._traj is None:
            return
        r0, th0 = self._traj[frame, 0], self._traj[frame, 1]
        xp, yp, zp = self._xyz(r0, th0)
        self._particle.setData(pos=np.array([[xp, yp, zp]]))
        if frame < 1:
            return  # GL_LINE_STRIP nécessite ≥ 2 points
        r, theta = self._traj[:frame + 1, 0], self._traj[:frame + 1, 1]
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = -self._slope * (self.R_MAX - r)
        self._trail.setData(pos=np.column_stack([x, y, z]).astype(np.float32))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._gl.update()

    # ── Marqueurs ─────────────────────────────────────────────────────────────

    def _add_marker(self, r: float, theta: float) -> None:
        x, y, z = self._xyz(r, theta)
        item = gl.GLScatterPlotItem(
            pos=np.array([[x, y, z]]),
            size=self._ball_r * 2.5,
            color=RGB_MARKER, pxMode=False,
        )
        self._marker_items.append(item)
        self._gl.addItem(item)
