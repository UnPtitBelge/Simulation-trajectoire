"""
Simulations page

Minimal simulations view: render only the 3D simulation graph.
"""

import dash_bootstrap_components as dbc
from components.plot_2d.sim_newton import plot as plot_newton
from components.plot_3d.sim_membrane import plot as plot_sim_3d
from dash import dcc, html
from utils.ui import page_container


def layout():
    """
    Return a standardized layout containing only the simulation graph,
    using utils.ui.page_container for consistent styling.
    """

    # Note: plot_sim_3d() is a thin convenience wrapper around build_animated_figure_3d(...).
    # It now accepts optional rendering/animation args via the function signature, but calling
    # it without arguments remains valid.
    default_dynamic_3d_figure = plot_sim_3d()

    # --- Visualization Zone (Right) ---
    visualization_panel = dbc.Card(
        dbc.CardBody(
            dbc.Tabs(
                id="simulation-tabs",
                active_tab="dynamic-3d-tab",
                children=[
                    dbc.Tab(
                        tab_id="dynamic-3d-tab",
                        children=dcc.Graph(
                            id="simulation-graph",
                            figure=default_dynamic_3d_figure,
                            config={"responsive": True, "displayModeBar": False},
                            className="sim-graph",
                        ),
                        label="Dynamique (3D)",
                        label_class_name="small-tab-label",
                    ),
                    dbc.Tab(
                        tab_id="newton-2d-tab",
                        label="Newton (2D)",
                        label_class_name="small-tab-label",
                        children=html.Div(
                            dcc.Graph(
                                id="simulation-newton-2d",
                                figure=plot_newton(),
                                config={"responsive": True, "displayModeBar": False},
                                className="sim-graph",
                            ),
                        ),
                        style={
                            "width": "100%",
                        },
                    ),
                ],
                className="nav-fill",  # Ensures tabs take all of the free width
            )
        )
    )

    # Page container
    # Responsive: Graph first on mobile (order=1), Controls second (order=2).
    # On Desktop: Controls first (order=1), Graph second (order=2).
    pc = page_container(
        title="Simulateur de Trajectoire",
        body_children=[
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            id="control-panel-wrapper",
                        ),
                        xs={"size": 12, "order": 2},
                        md={"size": 4, "order": 1},
                        lg={"size": 3, "order": 1},
                        className="control-panel-scroll",
                    ),
                    dbc.Col(
                        visualization_panel,
                        xs={"size": 12, "order": 1},
                        md={"size": 8, "order": 2},
                        lg={"size": 9, "order": 2},
                    ),
                ]
            )
        ],
    )
    return pc["body"]
