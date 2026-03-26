"""Cône 3D — Modéliser avec Newton.

Surface: z(r) = -slope*(R - r), constant slope.
Gravity along surface: a = g·sin(α), CONSTANT everywhere.
Coulomb friction opposing velocity: μ·g·cos(α).

Supports 3 integration methods: Euler semi-implicit, Verlet, RK4.
Produces rosette orbits with precession (~151°/orbit).
"""

import logging
import math

import numpy as np
import pyqtgraph.opengl as gl

from src.core.params.cone import ConeParams
from src.core.params.integrators import Integrator
from src.core.params.physics_constants import LARGE_BALL_RADIUS, SMALL_BALL_RADIUS
from src.simulations.base import Plot3dBase
from src.simulations.integrators import step_euler_semi_implicit, step_rk4, step_verlet

log = logging.getLogger(__name__)

_REST_SPEED_SQ = 1e-8
_REST_FRAMES = 10

_INTEGRATOR_FN = {
    Integrator.EULER_SEMI_IMPLICIT: step_euler_semi_implicit,
    Integrator.VERLET: step_verlet,
    Integrator.RK4: step_rk4,
}

# Colors for comparison mode trails
_COMPARE_COLORS = [
    (1.0, 0.3, 0.3, 0.8),   # Euler — red
    (0.3, 1.0, 0.3, 0.8),   # Verlet — green
    (0.3, 0.5, 1.0, 0.8),   # RK4 — blue
]


def _cone_center_z(slope: float, R: float) -> float:
    """z of the large ball's centre resting in the cone."""
    return -slope * R + LARGE_BALL_RADIUS * math.sqrt(1.0 + slope ** 2)


def _cone_accel(g: float, sin_a: float, cos_a: float, mu: float):
    """Return an acceleration closure for the cone surface."""
    a_grav = g * sin_a
    a_fric = mu * g * cos_a

    def accel(x: float, y: float, vx: float, vy: float) -> tuple[float, float]:
        r = math.sqrt(x * x + y * y)
        if r < 1e-6:
            r = 1e-6
        inv_r = 1.0 / r

        ax = -a_grav * x * inv_r
        ay = -a_grav * y * inv_r

        speed_sq = vx * vx + vy * vy
        if speed_sq > 1e-16:
            inv_speed = 1.0 / math.sqrt(speed_sq)
            ax -= a_fric * vx * inv_speed
            ay -= a_fric * vy * inv_speed
        return ax, ay

    return accel


def simulate_cone(p: ConeParams, integrator: Integrator | None = None) -> dict:
    """Compute trajectory on a cone with constant slope.

    If integrator is None, uses p.integrator.
    """
    n = int(p.n_frames)
    dt = p.dt
    slope = p.slope
    R = p.R_cone
    R_squared = R * R
    integ = integrator or p.integrator

    sin_a = slope / math.sqrt(1 + slope ** 2)
    cos_a = 1.0 / math.sqrt(1 + slope ** 2)

    accel = _cone_accel(p.gravity, sin_a, cos_a, p.friction)
    step_fn = _INTEGRATOR_FN[integ]

    phi_rad = math.radians(p.phi0)
    x, y = p.r0, 0.0
    vx = p.v0 * math.cos(phi_rad)
    vy = p.v0 * math.sin(phi_rad)

    z_center = _cone_center_z(slope, R)

    traj = []
    rest_count = 0

    for i in range(n):
        r_sq = x * x + y * y
        r = math.sqrt(r_sq)
        if r < 1e-6:
            r = 1e-6
            r_sq = 1e-12

        z = -slope * (R - r)
        traj.append((x, y, z))

        # Collision with center ball
        dz = z - z_center
        dist_3d = math.sqrt(r_sq + dz * dz)
        if dist_3d < LARGE_BALL_RADIUS + SMALL_BALL_RADIUS:
            return {"trajectory": traj, "n_frames": i + 1}

        # Integration step
        x_new, y_new, vx, vy = step_fn(x, y, vx, vy, accel, dt)

        # Rest detection
        if vx * vx + vy * vy < _REST_SPEED_SQ:
            rest_count += 1
            if rest_count >= _REST_FRAMES:
                return {"trajectory": traj, "n_frames": i + 1}
        else:
            rest_count = 0

        x, y = x_new, y_new

        # Boundary check: stop simulation if particle exits the cone
        r_new_sq = x * x + y * y
        if r_new_sq > R_squared:
            return {"trajectory": traj, "n_frames": i + 1}

    return {"trajectory": traj, "n_frames": n}


class PlotCone(Plot3dBase):
    SIM_KEY = "cone"

    def __init__(self, params: ConeParams | None = None):
        _p = params or ConeParams()
        super().__init__(_p)
        self.params: ConeParams = _p
        self.traj: list = []
        self._compare_trajs: list[list] = []
        self._mesh: gl.GLMeshItem | None = None
        self._particle: gl.GLScatterPlotItem | None = None
        self._trail: gl.GLLinePlotItem | None = None
        self._compare_trails: list[gl.GLLinePlotItem] = []

    def _build_cone_mesh(self):
        slope = self.params.slope
        R = self.params.R_cone
        nr, nth = 20, 60
        rs = np.linspace(0.01, R, nr)
        ths = np.linspace(0, 2 * np.pi, nth)

        verts = []
        for r_val in rs:
            z = -slope * (R - r_val)
            for th in ths:
                verts.append([r_val * np.cos(th), r_val * np.sin(th), z])
        verts = np.array(verts)

        faces = []
        for i in range(1, nr):
            for j in range(nth - 1):
                v0 = (i - 1) * nth + j
                v1 = v0 + 1
                v2 = i * nth + j + 1
                v3 = i * nth + j
                faces.append([v0, v1, v2])
                faces.append([v0, v2, v3])
        faces = np.array(faces)

        colors = np.tile([0.4, 0.6, 0.9, 0.12], (len(verts), 1))

        md = gl.MeshData(vertexes=verts, faces=faces)
        return gl.GLMeshItem(
            meshdata=md, vertexColors=colors, smooth=True,
            shader="shaded", glOptions="translucent",
        )

    def _get_cache_data(self) -> dict:
        return {
            "traj": self.traj[:],
            "_n_frames": self._n_frames,
            "compare_trajs": [t[:] for t in self._compare_trajs],
        }

    def _set_cache_data(self, data: dict) -> None:
        self.traj = data["traj"]
        self._n_frames = data["_n_frames"]
        self._compare_trajs = data.get("compare_trajs", [])

    def _compute(self):
        result = simulate_cone(self.params)
        self.traj = result["trajectory"]
        self._n_frames = result["n_frames"]

        # Comparison mode: run all 3 integrators with same IC
        self._compare_trajs = []
        if self.params.compare_integrators:
            for integ in Integrator:
                res = simulate_cone(self.params, integrator=integ)
                self._compare_trajs.append(res["trajectory"])

    def _draw_initial(self):
        self._mesh = self._build_cone_mesh()
        z_center = _cone_center_z(self.params.slope, self.params.R_cone)
        self._particle, self._trail = self._setup_3d_scene(
            self._mesh,
            particle_color=(0.12, 0.53, 0.90, 1.0),
            trail_color=(1.0, 0.6, 0.0, 0.8),
            center_z=z_center,
        )

        # Clear old comparison trails
        for trail in self._compare_trails:
            trail.setParentItem(None)
        self._compare_trails = []

        # Add comparison trails if in compare mode
        if self._compare_trajs:
            # Hide main trail in compare mode
            self._trail.setVisible(False)
            for idx, ctraj in enumerate(self._compare_trajs):
                color = _COMPARE_COLORS[idx % len(_COMPARE_COLORS)]
                ct = gl.GLLinePlotItem(
                    pos=np.array(ctraj), color=color, width=2, antialias=True,
                )
                self.widget.addItem(ct)
                self._compare_trails.append(ct)
        else:
            self._trail.setVisible(True)

        if self.traj:
            self._particle.setData(pos=np.array([self.traj[0]]))
            self.frame_updated.emit(0)

    def _draw(self, i):
        if not (0 <= i < len(self.traj)):
            return
        if self._particle is None or self._trail is None:
            return
        self._particle.setData(pos=np.array([self.traj[i]]))

        if not self._compare_trajs:
            trail = np.array(self.traj[: i + 1])
            self._trail.setData(pos=trail)
        else:
            # In compare mode, animate all trails up to frame i
            for idx, ctraj in enumerate(self._compare_trajs):
                if idx < len(self._compare_trails):
                    end = min(i + 1, len(ctraj))
                    self._compare_trails[idx].setData(pos=np.array(ctraj[:end]))

    def get_metrics_schema(self) -> list[dict]:
        from src.utils.theme import CLR_PRIMARY, CLR_TEXT_SECONDARY, CLR_WARNING
        return [
            {"key": "r",     "label": "Rayon",    "unit": "m",   "fmt": ".3f", "color": CLR_PRIMARY},
            {"key": "z",     "label": "Hauteur",  "unit": "m",   "fmt": ".3f", "color": "#6B48FF"},
            {"key": "speed", "label": "Vitesse",  "unit": "m/s", "fmt": ".3f", "color": CLR_WARNING},
            {"key": "t",     "label": "Temps",    "unit": "s",   "fmt": ".2f", "color": CLR_TEXT_SECONDARY},
        ]

    def get_frame_metrics(self, i: int) -> dict:
        if not (0 <= i < len(self.traj)):
            return {}
        x, y, z = self.traj[i]
        r = math.sqrt(x * x + y * y)
        if i > 0:
            px, py, pz = self.traj[i - 1]
            dt = self.params.dt
            speed = math.sqrt((x-px)**2 + (y-py)**2 + (z-pz)**2) / max(dt, 1e-9)
        else:
            speed = 0.0
        t_sec = i * self.params.dt
        return {"r": r, "z": z, "speed": speed, "t": t_sec}
