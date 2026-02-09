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

    # 1) URL-based routing: render content from the current pathname.

    # 2) Render content based on the current URL pathname (multipage routing).
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def render_page(pathname):
        """
        Render the content area based on the current URL pathname.

        Args:
            pathname (str | None): The current path (e.g., "/", "/activities", "/simulations", "/plots").

        Returns:
            Dash component: The layout for the selected section.
                            Defaults to Home when absent or unknown.
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
