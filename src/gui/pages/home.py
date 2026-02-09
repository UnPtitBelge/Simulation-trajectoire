"""Home page layout.

This module defines the Home page content for the single-page Dash app.
The layout uses dash_bootstrap_components (dbc) so it inherits the active
Bootstrap theme (e.g., FLATLY). Keep this page light and fast to render.
"""

import dash_bootstrap_components as dbc
from dash import html


def layout() -> dbc.Container:
    """
    Build and return the Home page layout.

    Returns:
        dbc.Container: A fluid Bootstrap container containing a simple
        welcome card. This function avoids heavy computations to ensure
        snappy page transitions.
    """
    return dbc.Container(
        [
            dbc.Card(
                id="welcome-card",
                class_name="my-3",
                children=[
                    dbc.CardHeader("Welcome"),
                    dbc.CardBody(
                        [
                            html.P(
                                "This is the home page of your Dash app.",
                                className="card-text",
                            ),
                        ]
                    ),
                ],
            ),
        ],
        fluid=True,
        id="home-page",
    )
