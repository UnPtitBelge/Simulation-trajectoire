"""
Plots page: displays a simple example graph inside a Bootstrap card.

This module uses only native Python types (dicts/lists) for figures to keep
compatibility with Dash properties, and wraps content with dash_bootstrap_components
for consistent theming with the selected Bootstrap theme.
"""

import dash_bootstrap_components as dbc
from components.plot import plot as build_plot
from dash import dcc, html
from utils.ui import page_container


def layout():
    """
    Build the plots page content.

    Returns a Bootstrap container with a single card containing a Plotly graph.
    All props are native Python types (dict/list) to ensure they work seamlessly
    with Dash component properties and callbacks.
    """
    fig = build_plot()
    pc = page_container(
        title="Plots",
        body_children=[
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Plots"),
                            dbc.CardBody(
                                [
                                    html.P("A 2D representation of the physical model"),
                                    dcc.Graph(
                                        id="curved-surface-graph",
                                        figure=fig,
                                    ),
                                ]
                            ),
                        ],
                        class_name="mb-3",
                    ),
                    width=12,
                )
            )
        ],
    )
    return dbc.Container(
        [pc["body"]],
        fluid=True,
        class_name="p-3",
        id="plots-page",
    )
