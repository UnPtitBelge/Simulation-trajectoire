"""3-D conical surface simulation renderer (Newton model).

Uses the constant-slope cone surface and semi-implicit Euler integrator.
Inherits all OpenGL rendering from Plot3dBase and only overrides the
surface-specific methods.
"""
from __future__ import annotations

import pyqtgraph.opengl as gl

from simulations.sim3d.Plot3dBase import Plot3dBase, _hex_to_qcolor
from simulations.sim3d.simulate_cone import simulate_cone
from utils.math_helpers import cone_z, _cone_z_scalar
from utils.params import SimulationConeParams
from utils.stylesheet import CLR_PLOT_DRAP


class PlotCone(Plot3dBase):
    """3-D cone simulation — constant-slope surface, Newton mechanics.

    Attributes
    ----------
    sim_params  SimulationConeParams controlling the simulation.
    """

    SIM_TYPE = "3d_cone"

    def __init__(self, sim_params: SimulationConeParams | None = None) -> None:
        if sim_params is None:
            sim_params = SimulationConeParams()
        super().__init__(sim_params, frame_ms=sim_params.frame_ms)

    # -----------------------------------------------------------------------
    # Plot3dBase abstract method implementations
    # -----------------------------------------------------------------------

    def _surface_z(self, r: float) -> float:
        return _cone_z_scalar(
            r,
            R=self.sim_params.surface_radius,
            cone_slope=self.sim_params.cone_slope,
            center_radius=self.sim_params.center_radius,
        )

    def _prepare_simulation(self) -> None:
        results = simulate_cone(self.sim_params)
        self.trajectory_xs  = results["xs"]
        self.trajectory_ys  = results["ys"]
        self.trajectory_zs  = results["zs"]
        self.trajectory_vxs = results["vxs"]
        self.trajectory_vys = results["vys"]
        self._n_frames = len(self.trajectory_xs)

    def _draw_surface(self) -> None:
        """Rebuild the cone surface mesh (maillage polaire, bord circulaire lisse)."""
        if self.surface is not None:
            try:
                self.widget.removeItem(self.surface)
            except Exception:
                pass

        R          = float(self.sim_params.surface_radius)
        cone_slope = float(self.sim_params.cone_slope)
        center_r   = float(self.sim_params.center_radius)

        verts, faces = self._polar_surface_mesh(
            lambda r: cone_z(r, R=R, cone_slope=cone_slope, center_radius=center_r),
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
