"""
Simulations page

Minimal simulations view: render only the 3D simulation graph.
"""

import dash_bootstrap_components as dbc
from components.plot_3D import plot as plot_3d
from components.sim_3d import plot as plot_sim_3d
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
                            dbc.Label("Initial speed v (m/s)"),
                            dbc.Input(
                                id="input-initial-speed",
                                type="number",
                                step=0.001,
                                min=0.0,
                                value=0.6,
                                persistence=True,
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
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Initial x position (m)"),
                            dbc.Input(
                                id="input-initial-x0",
                                type="number",
                                step=0.001,
                                value=0.490,
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Initial y position (m)"),
                            dbc.Input(
                                id="input-initial-y0",
                                type="number",
                                step=0.001,
                                value=0.00,
                                persistence=True,
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
                        [
                            dbc.Label("Surface tension T"),
                            dbc.Input(
                                id="input-surface-tension",
                                type="number",
                                step=0.1,
                                value=10.0,
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Friction coefficient"),
                            dbc.Input(
                                id="input-friction-coef",
                                type="number",
                                step=0.01,
                                min=0.0,
                                value=0.3,
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Center sphere radius (m)"),
                            dbc.Input(
                                id="input-center-radius",
                                type="number",
                                step=0.001,
                                min=0.0,
                                value=0.05,
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Surface radius R (m)"),
                            dbc.Input(
                                id="input-surface-radius",
                                type="number",
                                step=0.001,
                                min=0.01,
                                value=0.5,
                                persistence=True,
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
                        [
                            dbc.Label("Center sphere mass m (kg)"),
                            dbc.Input(
                                id="input-center-mass",
                                type="number",
                                step=0.01,
                                min=0.0,
                                value=0.5,
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Gravity g (m/s²)"),
                            dbc.Input(
                                id="input-gravity-g",
                                type="number",
                                step=0.01,
                                min=0.0,
                                value=9.81,
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Integration dt (s)"),
                            dbc.Input(
                                id="input-time-step",
                                type="number",
                                step=0.001,
                                min=0.0001,
                                value=0.01,
                                persistence=True,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Max steps"),
                            dbc.Input(
                                id="input-num-steps",
                                type="number",
                                step=1,
                                min=1,
                                value=800,
                                persistence=True,
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
                            class_name="w-100 py-2",
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Reset",
                            id="reset-simulation-inputs",
                            color="secondary",
                            n_clicks=0,
                            class_name="w-100 py-2",
                        ),
                        md=3,
                    ),
                ],
                class_name="mb-3",
            ),
            html.Div(),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Graph(
                            id="simulation-graph-static",
                            figure=_default_simulation_figure(),
                            config={"responsive": True, "displayModeBar": False},
                            style={"height": "50vh"},
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id="simulation-graph",
                            figure=plot_sim_3d(),
                            config={"responsive": True, "displayModeBar": False},
                            style={"height": "50vh"},
                        ),
                        md=6,
                    ),
                ],
                class_name="mb-3",
            ),
        ],
    )
    return pc["body"]
