import dash_bootstrap_components as dbc
from components.plot_2d.sim_newton import plot as plot_newton
from components.plot_3d.sim_membrane import plot as plot_sim_3d
from dash import dcc, html
from utils.ui import page_container


def layout():
    # --- 1. 3D Simulation View ---
    card_3d = dbc.Card(
        [
            dbc.CardHeader("Simulation 3D (Dynamique)"),
            dbc.CardBody(
                dcc.Graph(
                    id="simulation-graph",
                    figure=plot_sim_3d(),
                    config={"responsive": True, "displayModeBar": False},
                    className="sim-graph",
                    style={"height": "400px"},
                ),
                class_name="p-0",
            ),
        ],
        class_name="h-100 mb-3",
    )

    # --- 2. 2D Newton View ---
    card_2d = dbc.Card(
        [
            dbc.CardHeader("Simulation 2D (Newton)"),
            dbc.CardBody(
                dcc.Graph(
                    id="simulation-newton-2d",
                    figure=plot_newton(),
                    config={"responsive": True, "displayModeBar": False},
                    className="sim-graph",
                    style={"height": "400px"},
                ),
                class_name="p-0",
            ),
        ],
        class_name="h-100 mb-3",
    )

    # --- 3. Video View (Placeholder) ---
    card_video = dbc.Card(
        [
            dbc.CardHeader("Vidéo Tracking (Réel)"),
            dbc.CardBody(
                html.Div(
                    [
                        html.I(className="bi bi-play-circle display-4 text-muted"),
                        html.P(
                            "Vidéo de l'expérience ici", className="mt-2 text-muted"
                        ),
                    ],
                    className="d-flex flex-column align-items-center justify-content-center h-100 bg-light",
                    style={"minHeight": "400px"},
                ),
                class_name="p-0",
            ),
        ],
        class_name="h-100 mb-3",
    )

    # Page container
    pc = page_container(
        title="Simulateur: Comparaison Multi-Vues",
        body_children=[
            dbc.Row(
                [
                    # --- Control Panel ---
                    # Mobile (xs): Order 2 (Bottom)
                    # Desktop (lg): Order 1 (Top)
                    dbc.Col(
                        html.Div(id="control-panel-wrapper"),
                        xs={"size": 12, "order": 2},
                        lg={"size": 12, "order": 1},
                        className="mb-4 control-panel-scroll",
                    ),
                    # --- Visualization Area ---
                    # Left Column: Tabs with 3D/2D Simulation
                    # Mobile (xs): Order 1 (Top)
                    # Desktop (lg): Order 2 (Bottom Left)
                    dbc.Col(
                        dbc.Tabs(
                            id="simulation-tabs",
                            active_tab="dynamic-3d-tab",
                            children=[
                                dbc.Tab(
                                    card_3d,
                                    label="Simulation 3D",
                                    tab_id="dynamic-3d-tab",
                                ),
                                dbc.Tab(
                                    card_2d,
                                    label="Simulation 2D",
                                    tab_id="newton-2d-tab",
                                ),
                            ],
                            class_name="mb-3",
                        ),
                        xs={"size": 12, "order": 1},
                        lg={"size": 6, "order": 2},
                    ),
                    # Right Column: Video
                    # Mobile (xs): Order 1 (Top - after tabs since both are order 1 within the flex container)
                    # Desktop (lg): Order 2 (Bottom Right)
                    dbc.Col(
                        card_video,
                        xs={"size": 12, "order": 1},
                        lg={"size": 6, "order": 2},
                    ),
                ],
                className="g-3",
            ),
        ],
    )
    return pc["body"]
