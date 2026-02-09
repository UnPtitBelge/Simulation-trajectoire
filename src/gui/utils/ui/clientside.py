"""
utils.ui.clientside

Client-side utilities for the Dash app.

This submodule provides a small helper to register a clientside callback that
toggles Bootstrap's color mode (light/dark) by setting the HTML document
attribute "data-bs-theme". It relies on a dbc.Switch component whose 'value'
determines the active theme.

Exports:
- register_theme_clientside(app, switch_id="switch", target_span_id="color-mode-switch")

Usage:
    import dash
    from utils.ui.clientside import register_theme_clientside

    app = dash.Dash(__name__)
    register_theme_clientside(app, switch_id="switch", target_span_id="color-mode-switch")
"""

from __future__ import annotations

import dash


def register_theme_clientside(
    app: dash.Dash,
    switch_id: str = "switch",
    target_span_id: str = "color-mode-switch",
) -> None:
    """
    Register a clientside callback to toggle light/dark mode via the HTML
    document attribute 'data-bs-theme'.

    Args:
        app: Dash app instance.
        switch_id: The id of the dbc.Switch controlling the theme.
                   True -> light, False -> dark.
        target_span_id: The id of an existing component used as a harmless
                        Output target; its value is not actually used, but
                        Dash requires an Output for each callback.

    Behavior:
        When the switch is turned on, sets data-bs-theme="light".
        When the switch is turned off, sets data-bs-theme="dark".
    """
    app.clientside_callback(
        """
        function (switchOn) {
            var root = document.documentElement;
            var mode = switchOn ? "light" : "dark";
            try {
                root.setAttribute("data-bs-theme", mode);
            } catch (e) {
                console && console.warn && console.warn("Theme toggle failed:", e);
            }
            return window.dash_clientside.no_update;
        }
        """,
        dash.Output(target_span_id, "children"),
        dash.Input(switch_id, "value"),
    )


__all__ = ["register_theme_clientside"]
