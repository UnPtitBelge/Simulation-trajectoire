"""3-D Laplace membrane simulation renderer.

Uses the logarithmic membrane surface (Laplace equation solution) and
velocity-Verlet integrator.  Inherits all OpenGL rendering from
Plot3dBase and only overrides the surface-specific methods.
"""
from __future__ import annotations

import pyqtgraph.opengl as gl

from simulations.sim3d.Plot3dBase import Plot3dBase, _hex_to_qcolor
from simulations.sim3d.simulate_membrane import simulate_membrane
from utils.math_helpers import membrane_z, _membrane_z_scalar
from utils.params import SimulationMembraneParams
from utils.stylesheet import CLR_PLOT_DRAP


class PlotMembrane(Plot3dBase):
    """3-D membrane simulation — logarithmic Laplace surface.

    Attributes
    ----------
    sim_params  SimulationMembraneParams controlling the simulation.
    """

    SIM_TYPE = "3d_membrane"

    def __init__(self, sim_params: SimulationMembraneParams | None = None) -> None:
        if sim_params is None:
            sim_params = SimulationMembraneParams()
        super().__init__(sim_params, frame_ms=sim_params.frame_ms)

    # -----------------------------------------------------------------------
    # Plot3dBase abstract method implementations
    # -----------------------------------------------------------------------

    def _surface_z(self, r: float) -> float:
        return _membrane_z_scalar(
            r,
            R=self.sim_params.surface_radius,
            T=self.sim_params.surface_tension,
            F=self.sim_params.center_weight,
            center_radius=self.sim_params.center_radius,
        )

    def _prepare_simulation(self) -> None:
        results = simulate_membrane(self.sim_params)
        self.trajectory_xs  = results["xs"]
        self.trajectory_ys  = results["ys"]
        self.trajectory_zs  = results["zs"]
        self.trajectory_vxs = results["vxs"]
        self.trajectory_vys = results["vys"]
        self._n_frames = len(self.trajectory_xs)

    def _draw_surface(self) -> None:
        """Rebuild the membrane surface mesh (maillage polaire, bord circulaire lisse)."""
        if self.surface is not None:
            try:
                self.widget.removeItem(self.surface)
            except Exception:
                pass

        R        = float(self.sim_params.surface_radius)
        T        = float(self.sim_params.surface_tension)
        F        = float(self.sim_params.center_weight)
        center_r = float(self.sim_params.center_radius)

        verts, faces = self._polar_surface_mesh(
            lambda r: membrane_z(r, R=R, T=T, F=F, center_radius=center_r),
            R=R,
            center_r=center_r,
        )

        self.surface = gl.GLMeshItem(
            vertexes=verts,
            faces=faces,
            color=_hex_to_qcolor(CLR_PLOT_DRAP),
            shader="shaded",
            smooth=True,
            drawEdges=False,
        )
        self.widget.addItem(self.surface)
