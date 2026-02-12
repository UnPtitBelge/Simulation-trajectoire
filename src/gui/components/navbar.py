"""
Navbar components and utilities.

Mobile-friendly Bootstrap Navbar using dash_bootstrap_components (dbc):
- Includes a brand/title.
- Adds a NavbarToggler and Collapse for small screens.
- Keeps the color mode control aligned to the right.
- Exposes a static `render()` method for easy use in layouts.

Note:
- The toggling behavior (open/close of the Collapse) should be wired via a callback.
  A simple clientside callback can toggle `navbar-collapse.is_open` when `navbar-toggler` is clicked.
"""

import dash_bootstrap_components as dbc
from dash import html
from utils.ui import NAVBAR_PADDING_CLASS, color_mode_control, nav_group


class Navbar:
    """
    Bootstrap-based navbar for a multipage Dash app.

    Features:
    - Proper Bootstrap semantics via dbc.Navbar and dbc.Container.
    - Collapsible navigation links on mobile via NavbarToggler + Collapse.
    - Color mode switch (light/dark) aligned to the right.
    """

    @staticmethod
    def render():
        """
        Return the navbar layout as a Dash component tree (dbc.Navbar + dbc.Container).

        Structure:
        - NavbarBrand (optional)
        - NavbarToggler (mobile menu trigger)
        - Collapse containing navigation links (mobile-friendly)
        - Right-aligned color mode control
        """
        return dbc.Navbar(
            dbc.Container(
                [
                    # Brand/title (optional, adjust text as desired)
                    dbc.NavbarBrand("Simulation", class_name="me-2"),
                    # Navbar toggler (shows/hides the collapse on mobile)
                    dbc.NavbarToggler(
                        id="navbar-toggler", n_clicks=0, class_name="me-2"
                    ),
                    # Collapsible navigation group (links to pages)
                    dbc.Collapse(
                        nav_group(
                            [
                                ("Home", "/"),
                                ("Activities", "/activities"),
                                ("Simulations", "/simulations"),
                                ("Plots", "/plots"),
                            ],
                            pills=True,
                        ),
                        id="navbar-collapse",
                        is_open=False,
                        navbar=True,
                    ),
                    # Right-side utilities: color mode switch
                    html.Div(color_mode_control(), className="ms-auto"),
                ],
                fluid=True,
            ),
            color="primary",
            dark=True,
            id="main-navbar",
            class_name=NAVBAR_PADDING_CLASS,
            fixed="top",
        )


# Backward compatibility: `from components import navbar` then `navbar.render()`
navbar = Navbar
