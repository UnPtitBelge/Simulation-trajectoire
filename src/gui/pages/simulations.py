"""
Simulations page

This module provides a simple simulations view for the single-page Dash app.
It renders a Bootstrap card containing a Plotly graph with a default figure.
All figures are defined using native Python types (dict/list) for Dash props compatibility.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from utils.ui import build_layout, page_container


def _default_simulation_figure():
    """
    Build a simple default figure for the simulations page.

    Returns:
        dict: A Plotly figure represented as a plain dict with data/layout keys.
              Uses native Python types (lists/dicts) to remain compatible with Dash props.
    """
    return {
        "data": [
            {
                "type": "scatter",
                "mode": "lines+markers",
                "x": list(range(0, 11)),
                "y": [i * i for i in range(0, 11)],
                "name": "y = x^2",
            }
        ],
        "layout": build_layout(
            title="Default Simulation",
            height=400,
        ),
    }


def layout():
    """
    Return the simulations page layout.

    The layout is a Bootstrap container with a single full-width card:
    - CardHeader: title of the section
    - CardBody: short description and a dcc.Graph using the default simulation figure

    Returns:
        dash.development.base_component.Component: The Dash component tree for the page.
    """
    pc = page_container(
        title="Simulations",
        body_children=[
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Simulations"),
                            dbc.CardBody(
                                [
                                    html.P(
                                        "A basic demo figure so the page renders without callbacks."
                                    ),
                                    dcc.Graph(
                                        id="simulation-graph",
                                        figure=_default_simulation_figure(),
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
    )
