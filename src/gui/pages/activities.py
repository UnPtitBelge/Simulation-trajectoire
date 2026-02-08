"""Activities page layout.

This module defines the Activities page content for the single-page Dash app.
The layout uses dash_bootstrap_components (dbc) to leverage the active Bootstrap
theme (e.g., FLATLY) and keep styling consistent.
"""

import dash_bootstrap_components as dbc
from dash import html


def layout() -> dbc.Container:
    """Build and return the Activities page layout.

    Returns:
        dbc.Container: A fluid Bootstrap container with a card describing an activity
        and a themed button to start it.
    """
    return dbc.Container(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Activity 1"),
                    dbc.CardBody(
                        [
                            html.P("Description of Activity 1..."),
                            dbc.Button(
                                "Start Activity",
                                id="start-activity-1",
                                color="primary",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
                id="activity-1",
            ),
        ],
        id="activities-page",
        fluid=True,
    )
