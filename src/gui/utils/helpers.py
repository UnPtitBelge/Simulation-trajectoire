"""
helpers.py

Centralized callback registration for the single-page Dash app.

This module wires:
- A clientside callback for the color mode switch (light/dark), which sets the
  Bootstrap theme via the 'data-bs-theme' attribute on the document element.
- An example server-side callback that demonstrates callback structure without
  modifying the current figure.
"""

from dash import Input, Output, no_update


def register_all(app):
    """
    Register all callbacks for the application.

    Color mode clientside toggle:
    - Triggered by the `dbc.Switch` with id "switch"
    - Side-effect: sets document.documentElement 'data-bs-theme' to "light" or "dark"
    - Output is a no-op (`color-mode-switch.children`) to avoid mutating component props

    Example simulation figure update:
    - Triggered when the "Start Activity" button is clicked
    - Returns `no_update` to keep the current figure unchanged
    """

    # Clientside callback for color mode switch (light/dark).
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

    # Example server-side callback (keeps figure unchanged)
    @app.callback(
        Output("simulation-graph", "figure"),
        Input("start-activity-1", "n_clicks"),
        prevent_initial_call=True,
    )
    def update_simulation(n_clicks):
        """
        Example server-side callback for the simulations page.

        Parameters:
        - n_clicks: int or None
          Number of times the "Start Activity" button was clicked.

        Returns:
        - dash.no_update to keep the current figure unchanged.
        """
        # No-op: leave the existing figure as-is.
        return no_update
