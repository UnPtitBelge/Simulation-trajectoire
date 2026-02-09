"""
callbacks.py

Centralized non-plot callbacks for the Dash app.

This module registers:
- Navbar-driven page switching (updates `page-store`)
- Page content rendering based on `page-store`
- Color mode clientside toggle (light/dark)
- Example server-side no-op callback (demonstration only)

All plot-related callbacks have been intentionally removed to keep the UI simple.
"""

import dash
from dash import Input, Output, no_update
from pages import activities, home, plots, simulations


def register_all(app: dash.Dash):
    """
    Register non-plot callbacks on the provided Dash app instance.

    Includes:
    - Navbar-driven page switching (single-page style).
    - Page content rendering based on the selected page.
    - Color mode clientside toggle (light/dark).
    - Example server-side no-op callback.
    """

    # 1) Compute which section to render based on navbar button clicks.
    @app.callback(
        Output("page-store", "data"),
        [
            Input("btn-home", "n_clicks"),
            Input("btn-activities", "n_clicks"),
            Input("btn-simulations", "n_clicks"),
            Input("btn-plots", "n_clicks"),
        ],
    )
    def compute_page_store(n_home, n_activities, n_simulations, n_plots):
        """
        Determine which section should render based on the most recent navbar button click.

        Returns:
            dict: {"page": str} where str is one of "/", "/activities", "/simulations", "/plots".
                  Defaults to "/" (home) if nothing has triggered yet.
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            page = "/"
        else:
            trig_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if trig_id == "btn-home":
                page = "/"
            elif trig_id == "btn-activities":
                page = "/activities"
            elif trig_id == "btn-simulations":
                page = "/simulations"
            elif trig_id == "btn-plots":
                page = "/plots"
            else:
                page = "/"
        return {"page": page}

    # 2) Render content based on the selected page.
    @app.callback(Output("page-content", "children"), Input("page-store", "data"))
    def render_page(data):
        """
        Render the content area based on `page-store`.

        Args:
            data (dict | None): A dict with key "page" indicating which section to render.

        Returns:
            Dash component: The layout for the selected section.
                            Defaults to Home when absent or unknown.
        """
        page = (data or {}).get("page", "/")
        if page == "/activities":
            return activities.layout()
        elif page == "/simulations":
            return simulations.layout()
        elif page == "/plots":
            return plots.layout()
        else:
            return home.layout()

    # 3) Clientside callback for color mode switch (light/dark).
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

    # 4) Example server-side no-op callback (demonstration only).
    @app.callback(
        Output("simulation-graph", "figure"),
        Input("start-activity-1", "n_clicks"),
        prevent_initial_call=True,
    )
    def no_op_simulation(n_clicks):
        """
        Example server-side callback for the simulations page.

        Parameters:
        - n_clicks: int or None
          Number of times the "Start Activity" button was clicked.

        Returns:
        - dash.no_update to keep the current figure unchanged.
        """
        return no_update
