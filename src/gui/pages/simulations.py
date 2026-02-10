"""
Simulations page

Minimal simulations view: render only the 3D simulation graph.
"""

import dash_bootstrap_components as dbc
from components import plot_3d as plot_3d
from components import plot_sim_3d as plot_sim_3d
from dash import dcc, html
from utils.ui import page_container


def _default_simulation_figure():
    """
    Build the simulation figure (3D) using the components plot_3D module.
    """
    return plot_3d()


def layout():
    """
    Return a standardized layout containing only the simulation graph,
    using utils.ui.page_container for consistent styling.
    """
    pc = page_container(
        title="Simulations",
        body_children=[
            html.H4("Simulations"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Initial speed v_i (m/s)"),
                            dbc.Input(
                                id="input-initial-speed",
                                type="number",
                                step=0.001,
                                min=0.0,
                                value=0.6,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Angle θ (degrees)"),
                            dbc.Input(
                                id="input-theta-degrees",
                                type="number",
                                step=1.0,
                                min=0.0,
                                max=360.0,
                                value=45,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Initial x position x0 (m)"),
                            dbc.Input(
                                id="input-initial-x0",
                                type="number",
                                step=0.001,
                                value=0.490,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Initial y position y0 (m)"),
                            dbc.Input(
                                id="input-initial-y0",
                                type="number",
                                step=0.001,
                                value=0.00,
                            ),
                        ],
                        md=3,
                    ),
                ],
                class_name="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "Apply inputs",
                            id="apply-simulation-inputs",
                            color="primary",
                            n_clicks=0,
                        ),
                        md=3,
                    ),
                ],
                class_name="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id="simulation-graph",
                            figure=_default_simulation_figure(),
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id="simulation-graph-animated",
                            figure=plot_sim_3d(),
                        ),
                        md=6,
                    ),
                ],
                class_name="mb-3",
            ),
        ],
    )
    return pc["body"]
