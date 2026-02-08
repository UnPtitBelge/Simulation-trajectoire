"""
Navbar components and utilities.

This module defines `Navbar`, a Bootstrap-themed navigation bar using dash_bootstrap_components (dbc).
It exposes a static `render()` method so it can be used directly in layouts without instantiation.
"""

import dash_bootstrap_components as dbc
from dash import html


class Navbar:
    """
    Bootstrap-based navbar for a single-page Dash app.

    - Uses dbc.Navbar for proper Bootstrap semantics.
    - Navigation is implemented via dbc.Nav with dbc.NavItem entries; each item contains a dbc.Button
      to trigger content changes via callbacks (single-page behavior, no URL changes).
    - Includes a color mode switch (dbc.Switch) that toggles Bootstrap’s `data-bs-theme` (light/dark).
    """

    @staticmethod
    def render():
        """
        Return the navbar layout as a Dash component tree (dbc.Navbar + dbc.Nav).

        Contents:
        - Navigation items (Home highlighted, others outline style)
        - Color mode switch (moon/sun labels + dbc.Switch)
        """
        return dbc.Navbar(
            dbc.Container(
                [
                    # Navigation group
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.Button(
                                    "Home",
                                    id="btn-home",
                                    n_clicks=0,
                                    color="primary",
                                    size="sm",
                                )
                            ),
                            dbc.NavItem(
                                dbc.Button(
                                    "Activities",
                                    id="btn-activities",
                                    n_clicks=0,
                                    color="secondary",
                                    outline=True,
                                    size="sm",
                                )
                            ),
                            dbc.NavItem(
                                dbc.Button(
                                    "Simulations",
                                    id="btn-simulations",
                                    n_clicks=0,
                                    color="secondary",
                                    outline=True,
                                    size="sm",
                                )
                            ),
                            dbc.NavItem(
                                dbc.Button(
                                    "Plots",
                                    id="btn-plots",
                                    n_clicks=0,
                                    color="secondary",
                                    outline=True,
                                    size="sm",
                                )
                            ),
                        ],
                        navbar=True,
                        className="gap-2",
                    ),
                    # Color mode switch (moon / sun) using dbc.Switch
                    html.Span(
                        id="color-mode-switch",
                        className="ms-auto d-flex align-items-center gap-2",
                        children=[
                            dbc.Label(className="fa fa-moon", html_for="switch"),
                            dbc.Switch(
                                id="switch",
                                value=True,
                                className="d-inline-block",
                                persistence=True,
                            ),
                            dbc.Label(className="fa fa-sun", html_for="switch"),
                        ],
                    ),
                ],
                fluid=True,
            ),
            color="primary",
            dark=True,
            id="main-navbar",
            className="px-3",
        )


# Keep backward compatibility with `from components import navbar` then `navbar.render()`
navbar = Navbar
