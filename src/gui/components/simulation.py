"""
Simulation utilities: 2D motion on a curved surface driven by Earth gravity projected along the slope
(−g ∇h), en cohérence avec une modélisation de surface courbe, tout en conservant un tracé 2D.

Principes:
- Gravité terrestre: g = 9.81 m/s² (accélération verticale)
- Accélération tangentielle sur la surface: a_xy = −g · ∇h(x, y)
- Frottement linéaire: a_f = −c · v (avec c en s⁻¹)
- Surface gaussienne (pour calculer h et ∇h):
    h(x, y) = −D · exp(−(x² + y²) / (2 · S²))
  avec D = k_depth · center_mass, S = k_sigma · center_radius
- Pas de temps fixe et nombre d’itérations fixe
- Arrêt sur collision avec la sphère centrale ou sortie de la surface

Les figures sont des dicts Python compatibles Plotly (Dash).

Interfaces:
- SimulationParams: dataclass des paramètres physiques et de rendu
- SurfaceField: calcule la hauteur h(x, y) et son gradient ∇h(x, y)
- run_simulation(params): exécute la simulation et renvoie les résultats bruts
- build_figure(params, results): construit la figure 2D
- plot(): point d’entrée simplifié

Notes:
- z = h(x, y) est utilisé pour le calcul et l’analyse, le tracé reste en 2D (x, y).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass
class SimulationParams:
    # Constantes physiques (SI)
    earth_gravity: float = 9.81  # g (m/s²)
    friction_coefficient: float = 0.05  # Amortissement linéaire c (s⁻¹)

    # Time integration
    time_step: float = 0.01  # dt
    num_steps: int = 4000  # total steps

    # Corps central
    center_radius: float = 0.025  # R_center (m) -> diamètre 5 cm
    center_mass: float = 1.0  # M_center (kg)

    # Surface gaussienne (z pour les calculs seulement)
    # h(x, y) = −D · exp(−(x² + y²) / (2 · S²))
    surface_depth: float = 0.1  # Profondeur mesurée au centre (m)
    surface_sigma: float = 0.05  # Échelle (largeur) de la déformation (m)

    # Initial state of the moving object (must be within 0.5 m surface boundary)
    initial_position_x: float = 0.25
    initial_position_y: float = 0.0
    initial_velocity_x: float = 0.0
    initial_velocity_y: float = 1.0

    # 2D figure styling
    samples: int = 256
    outer_surface_radius: float = (
        0.5  # For drawing a simple outer boundary disc (meters)
    )
    outer_line_color: str = "rgba(100, 100, 255, 1.0)"
    outer_line_width: float = 1.5
    outer_fillcolor: str = "rgba(100, 100, 255, 0.15)"
    center_line_color: str = "rgba(255, 180, 80, 1.0)"
    center_line_width: float = 2.0
    center_fillcolor: str = "rgba(255, 180, 80, 0.35)"
    traj_color: str = "rgba(50, 50, 50, 1.0)"
    traj_width: float = 2.0
    traj_marker_size: float = 4.0
    showlegend: bool = False
    height: int = 480
    width: int | None = None
    title: str = "Curved Surface 2D Simulation (Newtonian + Friction)"


# ---------------------------------------------------------------------------
# Surface field (Gaussian deformation)
# ---------------------------------------------------------------------------


class SurfaceField:
    """
    Champ de surface gaussien (hauteur et gradient) pour calculer la pente locale.

    h(x, y) = −D · exp(−r² / (2 · S²)), avec:
      - D = k_depth · center_mass
      - S = k_sigma · center_radius

    Le coefficient de frottement est stocké pour cohérence avec la logique générale.
    """

    def __init__(
        self,
        depth: float,
        sigma: float,
        friction_coefficient: float,
    ):
        self._depth: float = float(depth)
        self._sigma: float = float(sigma)
        self._friction: float = float(friction_coefficient)

    def h(self, x: float, y: float) -> float:
        """Hauteur (z) à la position (x, y) via le champ gaussien."""
        r2 = float(x) * float(x) + float(y) * float(y)
        denom = 2.0 * (self._sigma**2) if self._sigma > 0.0 else 1e-12
        return -self._depth * exp(-r2 / denom)

    def gradient(self, x: float, y: float) -> Tuple[float, float]:
        """
        Gradient ∇h(x, y) = (∂h/∂x, ∂h/∂y) pour la surface gaussienne.
        Avec h(x, y) = −D · exp(−r² / (2 · S²)), on a:
          ∂h/∂x = D · exp(−r² / (2 · S²)) · (x / S²)
          ∂h/∂y = D · exp(−r² / (2 · S²)) · (y / S²)
        """
        r2 = float(x) * float(x) + float(y) * float(y)
        denom = 2.0 * (self._sigma**2) if self._sigma > 0.0 else 1e-12
        e = exp(-r2 / denom)
        inv_sigma2 = 1.0 / (self._sigma**2 if self._sigma > 0.0 else 1e-12)
        dh_dx = self._depth * e * float(x) * inv_sigma2
        dh_dy = self._depth * e * float(y) * inv_sigma2
        return (dh_dx, dh_dy)

    @property
    def sigma(self) -> float:
        return self._sigma

    @property
    def friction(self) -> float:
        return self._friction


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------


# (supprimé) Accélération centrale 1/r² — remplacée par l’accélération due à la pente (−g ∇h)


def run_simulation(params: SimulationParams) -> Dict[str, Any]:
    """
    Exécute la simulation 2D avec accélération tangentielle (−g ∇h) et frottement linéaire.
    Renvoie:
        dict avec clés:
            - xs, ys, zs: listes des positions et hauteurs de surface au cours du temps
            - collided: booléen de collision avec le corps central
            - steps_run: nombre d’itérations effectuées
            - final_state: dict avec x, y, vx, vy
    """
    # Raccourcis de lecture
    g = float(params.earth_gravity)
    c = float(params.friction_coefficient)
    dt = float(params.time_step)
    steps = int(params.num_steps)
    R_center = float(params.center_radius)
    M_center = float(params.center_mass)

    # Build surface field (z-height only)
    surface = SurfaceField(
        depth=params.surface_depth,
        sigma=params.surface_sigma,
        friction_coefficient=c,
    )

    # Initial state
    x = float(params.initial_position_x)
    y = float(params.initial_position_y)
    vx = float(params.initial_velocity_x)
    vy = float(params.initial_velocity_y)

    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []

    collided = False
    steps_run = 0

    for i in range(steps):
        # Collision with central body
        r = sqrt(x * x + y * y)
        if r < R_center:
            collided = True
            break

        # Accélération due à la pente (−g ∇h) + frottement (−c v)
        dh_dx, dh_dy = surface.gradient(x, y)
        ax = -g * dh_dx - c * vx
        ay = -g * dh_dy - c * vy

        # Integrate (explicit Euler as in simu_newtonienne)
        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt

        # Record history (z from surface height)
        xs.append(x)
        ys.append(y)
        zs.append(surface.h(x, y))

        steps_run += 1

    final_state = {"x": x, "y": y, "vx": vx, "vy": vy}
    return {
        "xs": xs,
        "ys": ys,
        "zs": zs,
        "collided": collided,
        "steps_run": steps_run,
        "final_state": final_state,
        "surface": surface,  # expose for downstream use if needed
        "params": params,
    }


# ---------------------------------------------------------------------------
# 2D figure construction (Plotly-compatible dicts)
# ---------------------------------------------------------------------------


def _build_disc_trace(
    cx: float,
    cy: float,
    radius: float,
    samples: int,
    name: str,
    line_color: str,
    line_width: float,
    fillcolor: str,
    showlegend: bool,
) -> Dict[str, Any]:
    """Return a filled circle boundary trace as a plain dict."""
    samples = max(16, int(samples))
    from math import cos, pi, sin

    step = 2.0 * pi / float(samples)
    pts = [
        (cx + radius * cos(i * step), cy + radius * sin(i * step))
        for i in range(samples)
    ]
    pts.append(pts[0])  # close

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    return {
        "type": "scatter",
        "mode": "lines",
        "name": name,
        "x": xs,
        "y": ys,
        "line": {"color": line_color, "width": float(line_width)},
        "fill": "toself",
        "fillcolor": fillcolor,
        "showlegend": bool(showlegend),
    }


def _build_trajectory_trace(
    xs: List[float],
    ys: List[float],
    name: str,
    line_color: str,
    line_width: float,
    marker_size: float,
    showlegend: bool,
) -> Dict[str, Any]:
    """Return a lines+markers trace for the trajectory."""
    return {
        "type": "scatter",
        "mode": "lines+markers",
        "name": name,
        "x": list(xs),
        "y": list(ys),
        "line": {"color": line_color, "width": float(line_width)},
        "marker": {"size": float(marker_size), "color": line_color},
        "showlegend": bool(showlegend),
    }


def build_figure(params: SimulationParams, results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a 2D figure dict with:
      - Outer boundary disc (for context)
      - Center body filled circle
      - Trajectory (lines + markers)
    """
    # Extract plotting inputs
    samples = int(params.samples)
    showlegend = bool(params.showlegend)
    width = params.width
    height = params.height
    title = params.title

    # Traces
    outer = _build_disc_trace(
        cx=0.0,
        cy=0.0,
        radius=float(params.outer_surface_radius),
        samples=samples,
        name="Surface Boundary",
        line_color=params.outer_line_color,
        line_width=params.outer_line_width,
        fillcolor=params.outer_fillcolor,
        showlegend=showlegend,
    )
    center = _build_disc_trace(
        cx=0.0,
        cy=0.0,
        radius=float(params.center_radius),
        samples=samples,
        name="Central Body",
        line_color=params.center_line_color,
        line_width=params.center_line_width,
        fillcolor=params.center_fillcolor,
        showlegend=showlegend,
    )
    traj = _build_trajectory_trace(
        xs=results["xs"],
        ys=results["ys"],
        name="Trajectory",
        line_color=params.traj_color,
        line_width=params.traj_width,
        marker_size=params.traj_marker_size,
        showlegend=showlegend,
    )

    # Layout
    layout: Dict[str, Any] = {
        "title": {"text": title + (" — collision" if results.get("collided") else "")},
        "xaxis": {"title": {"text": "x"}, "scaleanchor": "y", "scaleratio": 1},
        "yaxis": {"title": {"text": "y"}},
        "template": "plotly_white",
        "showlegend": showlegend,
        "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
    }
    if width is not None:
        layout["width"] = int(width)
    if height is not None:
        layout["height"] = int(height)

    return {"data": [outer, center, traj], "layout": layout}


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------


def plot() -> Dict[str, Any]:
    """
    Run the default simulation and return a 2D figure dict.
    Mirrors `src/simu_newtonienne` logic (gravity + friction + Gaussian surface height),
    plotting x vs y only.
    """
    params = SimulationParams()
    results = run_simulation(params)
    return build_figure(params, results)


__all__ = [
    "SimulationParams",
    "SurfaceField",
    "run_simulation",
    "build_figure",
    "plot",
]
