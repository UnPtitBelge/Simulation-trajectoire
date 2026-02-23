import dash_bootstrap_components as dbc
from dash import html
from utils.ui import NAVBAR_PADDING_CLASS, color_mode_control, nav_group


class Navbar:
    @staticmethod
    def render():
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
