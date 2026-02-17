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
from components.sim_3d import build_animated_figure_3d
from components.control_panel import control_panel_3D, control_panel_2D_newton
from dash import Input, Output, State, html
from components.plot_2d.sim_mcu import plot as plot_mcu
from components.plot_2d.sim_newton import plot as plot_newton
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

    # Navbar mobile toggler: collapse/expand the nav links on small screens
    app.clientside_callback(
        """
        function(nClicks, isOpen) {
            if (!nClicks) return isOpen;
            return !isOpen;
        }
        """,
        Output("navbar-collapse", "is_open"),
        Input("navbar-toggler", "n_clicks"),
        State("navbar-collapse", "is_open"),
    )

    # 3) Update both static and animated 3D simulation figures when the confirm button is clicked.
    @app.callback(
        [
            Output("simulation-graph-static", "figure"),
            Output("simulation-graph", "figure"),
            Output("simulation-graph-static", "config"),
            Output("simulation-graph", "config"),
        ],
        Input("apply-simulation-inputs", "n_clicks"),
        State("input-initial-speed", "value"),
        State("input-theta-degrees", "value"),
        State("input-initial-x0", "value"),
        State("input-initial-y0", "value"),
        State("input-surface-tension", "value"),
        State("input-friction-coef", "value"),
        State("input-center-radius", "value"),
        State("input-surface-radius", "value"),
        State("input-center-mass", "value"),
        State("input-gravity-g", "value"),
        State("input-time-step", "value"),
        State("input-num-steps", "value"),
        prevent_initial_call=True,
    )
    def update_simulation_figure(
        n_clicks,
        v_i,
        theta_deg,
        x0,
        y0,
        surface_tension,
        friction_coef,
        center_radius,
        surface_radius,
        center_mass,
        gravity_g,
        time_step,
        num_steps,
    ):
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
        T_val = 10.0 if surface_tension is None else float(surface_tension)
        fric_val = 0.3 if friction_coef is None else float(friction_coef)
        center_r_val = 0.05 if center_radius is None else float(center_radius)
        surface_r_val = 0.5 if surface_radius is None else float(surface_radius)
        g_val = 9.81 if gravity_g is None else float(gravity_g)
        m_val = 0.5 if center_mass is None else float(center_mass)
        F_val = m_val * g_val
        dt_val = 0.1 if time_step is None else float(time_step)
        steps_val = 800 if num_steps is None else int(num_steps)

        params = Plot3DSimulationParams(
            v_i=v_i_val,
            theta=theta_val,
            x0=x0_val,
            y0=y0_val,
            surface_tension=T_val,
            friction_coef=fric_val,
            center_radius=center_r_val,
            surface_radius=surface_r_val,
            center_weight=F_val,
            g=g_val,
            time_step=dt_val,
            num_steps=steps_val,
        )

        # Directly build figures without cache
        static_fig = build_figure_3d(params)
        animated_fig = build_animated_figure_3d(params, step_interval_ms=33)
        static_config = {"responsive": True, "displayModeBar": False}
        animated_config = {"responsive": True, "displayModeBar": False}
        return (static_fig, animated_fig, static_config, animated_config)

    # 4) Reset inputs to defaults and refresh both figures.
    @app.callback(
        [
            Output("input-initial-speed", "value"),
            Output("input-theta-degrees", "value"),
            Output("input-initial-x0", "value"),
            Output("input-initial-y0", "value"),
            Output("input-surface-tension", "value"),
            Output("input-friction-coef", "value"),
            Output("input-center-radius", "value"),
            Output("input-surface-radius", "value"),
            Output("input-center-mass", "value"),
            Output("input-gravity-g", "value"),
            Output("input-time-step", "value"),
            Output("input-num-steps", "value"),
            Output("simulation-graph-static", "figure", allow_duplicate=True),
            Output("simulation-graph", "figure", allow_duplicate=True),
            Output("simulation-graph-static", "config", allow_duplicate=True),
            Output("simulation-graph", "config", allow_duplicate=True),
        ],
        Input("reset-simulation-inputs", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_simulation_inputs(n_clicks):
        defaults = Plot3DSimulationParams()
        # Convert weight (N) back to mass (kg) for the input field
        default_mass = (
            float(defaults.center_weight) / float(defaults.g)
            if float(defaults.g) != 0.0
            else 0.0
        )
        return (
            float(defaults.v_i),
            float(defaults.theta),
            float(defaults.x0),
            float(defaults.y0),
            float(defaults.surface_tension),
            float(defaults.friction_coef),
            float(defaults.center_radius),
            float(defaults.surface_radius),
            float(default_mass),
            float(defaults.g),
            float(defaults.time_step),
            int(defaults.num_steps),
            build_figure_3d(defaults),
            build_animated_figure_3d(defaults, step_interval_ms=33),
            {"responsive": True, "displayModeBar": False},
            {"responsive": True, "displayModeBar": False},
        )

    # ------ control panel callbacks ------
    @app.callback(
        Output("control-panel-wrapper", "children"),
        Input("simulation-tabs", "active_tab"),
    )
    def switch_control_panel(active_tab):
        """
        Switch the control panel content based on the active simulation tab.

        Args:
            active_tab (str | None): The ID of the currently active tab.

        Returns:
            Dash component: The appropriate control panel for the selected tab.
        """
        if active_tab == "dynamic-3d-tab":
            return control_panel_3D()
        elif active_tab == "static-3d-tab":
            return control_panel_3D()  # Reuse same controls for static view
        elif active_tab == "newton-2d-tab":
            return control_panel_2D_newton()
        else:
            return html.Div("Sélectionnez un onglet pour afficher les contrôles.")


    # ------ NEWTON 2D callbacks ------
    @app.callback(
            Output("simulation-newton-2d", "figure"),
            Input("apply-simulation-newton-inputs", "n_clicks"),
            State("input-initial-speed-newton", "value"),
            State("input-theta-degrees-newton", "value"),
            State("input-distance-boule-newton", "value"),
            State("input-friction-coef-newton", "value"),
            State("input-show-full-trajectory-newton", "value"),
            prevent_initial_call=True,
        )
    def update_newton_2d(n_clicks, v0, theta_deg, radius, friction_coef, show_full_trajectory):
        n_frames = 10000
        trail = n_frames if show_full_trajectory else 50
        return plot_newton(
        G=1,
        M=1000,
        r0=radius,
        v0=v0,
        theta_deg=theta_deg,
        gamma=friction_coef/10,
        trail=trail,
        n_frames=n_frames,
        duration_ms=10,
    )

    @app.callback(
            Output("input-initial-speed-newton", "value"),
            Output("input-theta-degrees-newton", "value"),
            Output("input-distance-boule-newton", "value"),
            Output("input-friction-coef-newton", "value"),
            Output("input-show-full-trajectory-newton", "value"),
            Output("simulation-newton-2d", "figure", allow_duplicate=True),
        Input("reset-simulation-newton-inputs", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_newton_2d(n_clicks):
        default_v0 = 4.0
        default_theta = 90
        default_radius = 45.0
        default_friction = 0.05
        default_show_full_trajectory = True
        n_frames = 10000
        trail = n_frames if default_show_full_trajectory else 50
        return (
            default_v0,
            default_theta,
            default_radius,
            default_friction,
            default_show_full_trajectory,
            plot_newton(
                G=1,
                M=1000,
                r0=default_radius,
                v0=default_v0,
                theta_deg=default_theta,
                gamma=default_friction/10,
                trail=trail,
                n_frames=n_frames,
                duration_ms=10,
            ),
        )

