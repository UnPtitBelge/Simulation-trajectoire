"""Membrane 3D — Plus d'équations, pas forcément meilleur.

Analytical Laplace solution for elastic membrane under central load:
  z(r) = -(F/2πT)·ln(R/r) = -A·ln(R/r)
  dz/dr = A/r  → slope varies as 1/r

Same initial conditions as the cone for direct comparison.
Supports 3 integration methods: Euler semi-implicit, Verlet, RK4.
"""

import logging
import math

import numpy as np
import pyqtgraph.opengl as gl

from src.core.params.integrators import Integrator
from src.core.params.membrane import MembraneParams
from src.core.params.physics_constants import LARGE_BALL_RADIUS, MEMBRANE_R_MIN, SMALL_BALL_RADIUS
from src.simulation.engines.base import Plot3dBase
from src.simulation.engines.integrators import step_euler_semi_implicit, step_rk4, step_verlet
from src.utils.theme import CLR_PRIMARY, CLR_TEXT_SECONDARY, CLR_WARNING

log = logging.getLogger(__name__)

_R_MIN = MEMBRANE_R_MIN
_REST_SPEED_SQ = 1e-8
_REST_FRAMES = 10

_INTEGRATOR_FN = {
    Integrator.EULER_SEMI_IMPLICIT: step_euler_semi_implicit,
    Integrator.VERLET: step_verlet,
    Integrator.RK4: step_rk4,
}

_COMPARE_COLORS = [
    (1.0, 0.3, 0.3, 0.8),   # Euler — red
    (0.3, 1.0, 0.3, 0.8),   # Verlet — green
    (0.3, 0.5, 1.0, 0.8),   # RK4 — blue
]


def _membrane_center_z(A: float, R: float) -> float:
    """z of the large ball's centre resting on the membrane z = -A·ln(R/r)."""
    lo, hi = 0.0, LARGE_BALL_RADIUS
    for _ in range(60):
        mid = (lo + hi) * 0.5
        if mid * math.sqrt(1.0 + (mid / A) ** 2) < LARGE_BALL_RADIUS:
            lo = mid
        else:
            hi = mid
    r_t = max((lo + hi) * 0.5, _R_MIN)
    return -A * math.log(R / r_t) + r_t ** 2 / A


def _membrane_accel(g: float, mu: float, A: float):
    """Return an acceleration closure for the Laplace membrane."""
    def accel(x: float, y: float, vx: float, vy: float) -> tuple[float, float]:
        r = math.sqrt(x * x + y * y)
        r = max(r, _R_MIN)
        slope = A / r

        denom = math.sqrt(1 + slope * slope)
        sin_a = slope / denom
        cos_a = 1.0 / denom
        inv_r = 1.0 / r

        ax = -g * sin_a * x * inv_r
        ay = -g * sin_a * y * inv_r

        speed_sq = vx * vx + vy * vy
        if speed_sq > 1e-16:
            inv_speed = 1.0 / math.sqrt(speed_sq)
            fric = mu * g * cos_a
            ax -= fric * vx * inv_speed
            ay -= fric * vy * inv_speed
        return ax, ay

    return accel


def simulate_membrane(p: MembraneParams, integrator: Integrator | None = None) -> dict:
    """Compute trajectory on a Laplace membrane z=-A·ln(R/r).

    If integrator is None, uses p.integrator.
    """
    n = int(p.n_frames)
    dt = p.dt
    A = p.A
    R = p.R_membrane
    R_squared = R * R
    integ = integrator or p.integrator

    accel = _membrane_accel(p.gravity, p.friction, A)
    step_fn = _INTEGRATOR_FN[integ]

    phi_rad = math.radians(p.phi0)
    x, y = p.r0, 0.0
    vx = p.v0 * math.cos(phi_rad)
    vy = p.v0 * math.sin(phi_rad)

    z_center = _membrane_center_z(A, R)

    traj = []
    rest_count = 0

    for i in range(n):
        r_sq = x * x + y * y
        r = math.sqrt(r_sq)
        r_clamped = max(r, _R_MIN)

        z = -A * math.log(R / r_clamped) if r_clamped < R else 0.0
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

        # Boundary check: stop simulation if particle exits the membrane
        r_new_sq = x * x + y * y
        if r_new_sq > R_squared:
            return {"trajectory": traj, "n_frames": i + 1}

    return {"trajectory": traj, "n_frames": n}


def _membrane_surface(A, R, nr=40, nth=80):
    """Generate mesh vertices and faces for the Laplace membrane."""
    rs = np.linspace(_R_MIN, R, nr)
    ths = np.linspace(0, 2 * np.pi, nth)

    verts = []
    for r_val in rs:
        z = -A * np.log(R / r_val)
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
    return verts, np.array(faces)


class PlotMembrane(Plot3dBase):
    SIM_KEY = "membrane"

    def __init__(self, params: MembraneParams | None = None):
        _p = params or MembraneParams()
        super().__init__(_p)
        self.params: MembraneParams = _p
        self.traj: list = []
        self._compare_trajs: list[list] = []
        self._mesh: gl.GLMeshItem | None = None
        self._particle: gl.GLScatterPlotItem | None = None
        self._trail: gl.GLLinePlotItem | None = None
        self._compare_trails: list[gl.GLLinePlotItem] = []

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
        result = simulate_membrane(self.params)
        self.traj = result["trajectory"]
        self._n_frames = result["n_frames"]

        # Comparison mode: run all 3 integrators with same IC
        self._compare_trajs = []
        if self.params.compare_integrators:
            for integ in Integrator:
                res = simulate_membrane(self.params, integrator=integ)
                self._compare_trajs.append(res["trajectory"])

    def _draw_initial(self):
        verts, faces = _membrane_surface(self.params.A, self.params.R_membrane)
        z_vals = verts[:, 2]
        z_min, z_max = z_vals.min(), z_vals.max()
        z_range = z_max - z_min if z_max != z_min else 1.0
        colors = np.zeros((len(verts), 4))
        for idx in range(len(verts)):
            t = (verts[idx, 2] - z_min) / z_range
            colors[idx] = [0.8 * t, 0.3 + 0.4 * (1 - t), 0.8 - 0.3 * t, 0.4]

        md = gl.MeshData(vertexes=verts, faces=faces)
        self._mesh = gl.GLMeshItem(
            meshdata=md, vertexColors=colors, smooth=True,
            shader="shaded", glOptions="translucent",
        )
        z_center = _membrane_center_z(self.params.A, self.params.R_membrane)
        self._particle, self._trail = self._setup_3d_scene(
            self._mesh,
            particle_color=(0.2, 0.7, 1.0, 1.0),
            trail_color=(1.0, 1.0, 0.0, 0.7),
            center_z=z_center,
        )

        # Clear old comparison trails
        for trail in self._compare_trails:
            trail.setParentItem(None)
        self._compare_trails = []

        # Add comparison trails if in compare mode
        if self._compare_trajs:
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
            for idx, ctraj in enumerate(self._compare_trajs):
                if idx < len(self._compare_trails):
                    end = min(i + 1, len(ctraj))
                    self._compare_trails[idx].setData(pos=np.array(ctraj[:end]))

    def get_metrics_schema(self) -> list[dict]:
        return [
            {"key": "r",     "label": "Rayon",   "unit": "m",   "fmt": ".3f", "color": CLR_PRIMARY},
            {"key": "z",     "label": "Hauteur", "unit": "m",   "fmt": ".3f", "color": "#6B48FF"},
            {"key": "speed", "label": "Vitesse", "unit": "m/s", "fmt": ".3f", "color": CLR_WARNING},
            {"key": "t",     "label": "Temps",   "unit": "s",   "fmt": ".2f", "color": CLR_TEXT_SECONDARY},
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
