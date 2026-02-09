"""
Plots page: displays a simple example graph inside a Bootstrap card.

This module uses only native Python types (dicts/lists) for figures to keep
compatibility with Dash properties, and wraps content with dash_bootstrap_components
for consistent theming with the selected Bootstrap theme.
"""

import dash_bootstrap_components as dbc
from dash import dcc

# Pure-Python default figure (only native dict/list types)
DEFAULT_FIGURE = {
    "data": [
        {
            "type": "scatter",
            "mode": "lines+markers",
            "x": list(range(0, 11)),
            "y": [i * i for i in range(0, 11)],
            "name": "y = x^2",
            "marker": {"size": 6},
            "line": {"width": 2},
        }
    ],
    "layout": {
        "title": {"text": "Simple Quadratic", "x": 0.5},
        "xaxis": {"title": {"text": "x"}},
        "yaxis": {"title": {"text": "y = x^2"}},
        "margin": {"l": 50, "r": 20, "t": 50, "b": 50},
        "template": "plotly_white",
        "height": 420,
    },
}


def layout():
    """
    Build the plots page content.

    Returns a Bootstrap container with a single card containing a Plotly graph.
    All props are native Python types (dict/list) to ensure they work seamlessly
    with Dash component properties and callbacks.
    """
    # Wrap content in Bootstrap components and use a Card around the Graph
    return dbc.Container(
        id="plots-page",
        fluid=True,
        children=[
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Plot 1"),
                            dbc.CardBody(
                                dcc.Graph(id="plot-graph", figure=DEFAULT_FIGURE)
                            ),
                        ],
                        class_name="my-3",
                    ),
                    width=12,
                )
            )
        ],
        class_name="p-3",
    )
