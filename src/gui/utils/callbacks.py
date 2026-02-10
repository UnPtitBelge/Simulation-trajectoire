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

import math

import dash
from components.simulation import SimulationParams, build_figure, run_simulation
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
            pathname (str | None): Current path (e.g., "/", "/activities", "/simulations", "/plots").

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

    # 3) Simulations parameter-change callback: update figure and show collision alerts.
    @app.callback(
        Output("simulation-graph", "figure"),
        Output("simulation-warning", "children"),
        Output("simulation-warning", "is_open"),
        Input("run-simulation-btn", "n_clicks"),
        State("mass-input", "value"),
        State("angle-input", "value"),
        State("speed-input", "value"),
        State("radius-input", "value"),
        State("depth-input", "value"),
        State("sigma-input", "value"),
        prevent_initial_call=True,
    )
    def update_simulation_figure(
        n_clicks: int,
        mass: float,
        angle_deg: float,
        speed: float,
        radius: float,
        depth: float,
        sigma: float,
    ):
        """
        Update the simulation figure when the user clicks the 'Run simulation' button
        or changes input values. Shows a warning alert if a collision occurs.

        - Derives initial velocity components from angle (degrees) and speed:
            vx = speed * cos(theta)
            vy = speed * sin(theta)
          where theta is interpreted in radians.

        - Constructs SimulationParams using user-provided mass and radius along with
          the derived initial velocity. Other parameters use dataclass defaults.

        - Runs the simulation and builds the 2D figure from the results.
        """
        # Fallbacks if any input is None
        base_defaults = SimulationParams()
        mass = base_defaults.center_mass if mass is None else float(mass)
        # Clamp angle to [0, 360] just to be safe; UI already restricts to [0, 90]
        angle_deg = (
            math.degrees(
                math.atan2(
                    base_defaults.initial_velocity_y,
                    base_defaults.initial_velocity_x,
                )
            )
            if angle_deg is None
            else float(angle_deg)
        )
        angle_deg = max(0.0, min(360.0, angle_deg))
        speed = (
            math.hypot(
                base_defaults.initial_velocity_x,
                base_defaults.initial_velocity_y,
            )
            if speed is None
            else float(speed)
        )
        radius = base_defaults.center_radius if radius is None else float(radius)
        depth = base_defaults.surface_depth if depth is None else float(depth)
        sigma = base_defaults.surface_sigma if sigma is None else float(sigma)

        # Derive initial velocity relative to the line toward the center:
        # v0_hat = cos(theta) * r_hat + sin(theta) * t_hat
        # where r_hat points inward toward the center and t_hat is the ccw tangential unit vector.
        base_params = SimulationParams(center_mass=mass, center_radius=radius)
        x0 = float(base_params.initial_position_x)
        y0 = float(base_params.initial_position_y)
        r = math.hypot(x0, y0)
        if r > 1e-12:
            rx = -x0 / r  # inward radial unit vector x-component
            ry = -y0 / r  # inward radial unit vector y-component
            tx = -y0 / r  # tangential (ccw) unit vector x-component
            ty = x0 / r  # tangential (ccw) unit vector y-component
        else:
            # Fallback orientation if starting at the center (degenerate)
            rx, ry, tx, ty = -1.0, 0.0, 0.0, 1.0
        theta = math.radians(angle_deg)
        vx0 = speed * (math.cos(theta) * rx + math.sin(theta) * tx)
        vy0 = speed * (math.cos(theta) * ry + math.sin(theta) * ty)

        # Build parameters for the simulation
        params = SimulationParams(
            center_mass=mass,
            center_radius=radius,
            surface_depth=depth,
            surface_sigma=sigma,
            initial_velocity_x=vx0,
            initial_velocity_y=vy0,
        )

        # Run simulation and build figure
        results = run_simulation(params)
        fig = build_figure(params, results)

        # Collision alert: open when collision occurred, otherwise closed
        collided = bool(results.get("collided"))
        warning_msg = "Collision with the central body detected." if collided else ""

        return fig, warning_msg, collided
