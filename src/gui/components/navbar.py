"""
Navbar components and utilities.

This module defines `Navbar`, a Bootstrap-themed navigation bar using dash_bootstrap_components (dbc).
It exposes a static `render()` method so it can be used directly in layouts without instantiation.
"""

import dash_bootstrap_components as dbc
from utils.ui import NAVBAR_PADDING_CLASS, color_mode_control, nav_group


class Navbar:
    """
    Bootstrap-based navbar for a multipage Dash app.

    - Uses dbc.Navbar for proper Bootstrap semantics.
    - Navigation uses dbc.NavLink (or dcc.Link) entries pointing to URL paths to enable multipage routing.
    - Includes a color mode switch (dbc.Switch) that toggles Bootstrap’s `data-bs-theme` (light/dark).
    """

    @staticmethod
    def render():
        """
        Return the navbar layout as a Dash component tree (dbc.Navbar + dbc.Nav).

        Contents:
        - Navigation items (Home highlighted via active="exact")
        - Color mode switch (moon/sun labels + dbc.Switch)
        """
        return dbc.Navbar(
            dbc.Container(
                [
                    # Navigation group
                    nav_group(
                        [
                            ("Home", "/"),
                            ("Activities", "/activities"),
                            ("Simulations", "/simulations"),
                            ("Plots", "/plots"),
                        ],
                        pills=True,
                    ),
                    # Color mode switch (moon / sun) using dbc.Switch
                    color_mode_control(),
                ],
                fluid=True,
            ),
            color="primary",
            dark=True,
            id="main-navbar",
            class_name=NAVBAR_PADDING_CLASS,
        )


# Keep backward compatibility with `from components import navbar` then `navbar.render()`
navbar = Navbar
