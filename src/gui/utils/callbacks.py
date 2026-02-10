"""
callbacks.py

Centralized callbacks for the Dash app.

This module registers:
- URL-based routing for pages
- Color mode clientside toggle (light/dark)
- Simulation parameter-change callback using the refactored components.simulation API:
  - Builds SimulationParams from UI inputs
  - Derives initial velocity from angle (degrees) and speed
  - Runs the simulation via run_simulation and constructs a 2D figure via build_figure
  - Shows an alert when a collision with the central body occurs
"""

import dash
from components.plot_3D import build_figure_3d
from components.plot_3d.simulation_params import (
    SimulationParams as Plot3DSimulationParams,
)
from dash import Input, Output, State
from pages import activities, home, plots, simulations


def register_all(app: dash.Dash):
    """
    Register callbacks on the provided Dash app instance.

    Includes:
    - URL-based routing (single-page style).
    - Page content rendering based on the selected URL path.
    - Color mode clientside toggle (light/dark).
    - Simulation parameter-change callback to update the figure and show collision alerts.
    """

    # 1) Render content based on the current URL pathname (multipage routing).
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def render_page(pathname):
        """
        Render the content area based on the current URL pathname.

        Args:
            pathname (str | None): Current path (e.g., "/", "/activities", "/plots").

        Returns:
            Dash component: The layout for the selected section (defaults to Home).
        """
        page = pathname or "/"
        if page == "/activities":
            return activities.layout()
        elif page == "/simulations":
            return simulations.layout()
        elif page == "/plots":
            return plots.layout()
        elif page == "/":
            return home.layout()
        else:
            from utils.ui import friendly_404

            return friendly_404(pathname)

    # 2) Clientside callback for color mode switch (light/dark).
    # Uses a harmless no-op Output to avoid changing component props.
    app.clientside_callback(
        """
        function (switchOn) {
            document.documentElement.setAttribute(
              "data-bs-theme",
              switchOn ? "light" : "dark"
            );
            return window.dash_clientside.no_update;
        }
        """,
        Output("color-mode-switch", "children"),
        Input("switch", "value"),
    )

    # 3) Update 3D simulation figure only when the confirm button is clicked.
    @app.callback(
        Output("simulation-graph", "figure"),
        Input("apply-simulation-inputs", "n_clicks"),
        State("input-initial-speed", "value"),
        State("input-theta-degrees", "value"),
        State("input-initial-x0", "value"),
        State("input-initial-y0", "value"),
        prevent_initial_call=True,
    )
    def update_simulation_figure(n_clicks, v_i, theta_deg, x0, y0):
        """
        Update 3D simulation figure when user clicks the 'Apply inputs' button.
        Inputs:
          - v_i: Initial speed magnitude (m/s)
          - theta_deg: Angle (degrees) between inward radial unit vector and initial velocity
          - x0, y0: Initial position (m)
        """
        v_i_val = 0.0 if v_i is None else float(v_i)
        theta_val = 0.0 if theta_deg is None else float(theta_deg)
        x0_val = 0.0 if x0 is None else float(x0)
        y0_val = 0.0 if y0 is None else float(y0)
        params = Plot3DSimulationParams(
            v_i=v_i_val, theta=theta_val, x0=x0_val, y0=y0_val
        )
        return build_figure_3d(params)
