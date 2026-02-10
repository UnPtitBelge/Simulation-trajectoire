"""
Simulations page

This module provides a simple simulations view for the single-page Dash app.
It renders a Bootstrap card containing a Plotly graph with a default figure.
All figures are defined using native Python types (dict/list) for Dash props compatibility.
"""

import dash_bootstrap_components as dbc
from components.simulation import plot as simulation_plot
from dash import dcc, html
from utils.ui import page_container


def _default_simulation_figure():
    """
    Build the simulation figure using the components simulation module.

    Returns:
        dict: A Plotly figure represented as a plain dict with data/layout keys.
              Uses native Python types (lists/dicts) to remain compatible with Dash props.
    """
    return simulation_plot()


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
                                        "Configure the simulation parameters and run to update the trajectory."
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Big sphere mass (kg)"),
                                                    dbc.Input(
                                                        id="mass-input",
                                                        type="number",
                                                        step=0.1,
                                                        min=0.0,
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        "Angle of launch (degrees)"
                                                    ),
                                                    dbc.Input(
                                                        id="angle-input",
                                                        type="number",
                                                        step=1.0,
                                                        min=0.0,
                                                        max=90.0,
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Initial speed (m/s)"),
                                                    dbc.Input(
                                                        id="speed-input",
                                                        type="number",
                                                        step=0.1,
                                                        min=0.0,
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Big sphere radius (m)"),
                                                    dbc.Input(
                                                        id="radius-input",
                                                        type="number",
                                                        step=0.1,
                                                        min=0.0,
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Surface depth (m)"),
                                                    dbc.Input(
                                                        id="depth-input",
                                                        type="number",
                                                        step=0.001,
                                                        min=0.0,
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Surface sigma (m)"),
                                                    dbc.Input(
                                                        id="sigma-input",
                                                        type="number",
                                                        step=0.001,
                                                        min=0.0,
                                                    ),
                                                ],
                                                md=2,
                                            ),
                                        ],
                                        class_name="mb-3",
                                    ),
                                    dbc.Button(
                                        "Run simulation",
                                        id="run-simulation-btn",
                                        color="primary",
                                        class_name="mb-3",
                                        n_clicks=0,
                                    ),
                                    dbc.Alert(
                                        id="simulation-warning",
                                        children="",
                                        color="warning",
                                        is_open=False,
                                        dismissable=True,
                                        class_name="mb-2",
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
