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
    
    # --- Left panel ---
    control_panel = html.Div(
        [
            html.H5("Paramètres", className="mb-3"),
            
            # Group 1: Initial Conditions
            dbc.Card(
                [
                    dbc.CardHeader("Conditions Initiales"),
                    dbc.CardBody(
                        [
                            dbc.Label("Vitesse initiale (m/s)"),
                            dcc.Slider(
                                id="input-initial-speed",
                                min=0.1, max=5.0, step=0.1, value=0.6,
                                marks={0: '0', 1: '1', 2: '2', 3: '3', 5: '5'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Br(),
                            dbc.Label("Angle de tir θ (degrés)"),
                            dcc.Slider(
                                id="input-theta-degrees",
                                min=0, max=360, step=5, value=45,
                                marks={0: '0°', 90: '90°', 180: '180°', 270: '270°', 360: '360°'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Br(),
                            dbc.Label("Position de départ (X, Y)"),
                            dbc.Row(
                                [
                                    dbc.Col(dbc.Input(id="input-initial-x0", type="number", placeholder="X", value=0.490, step=0.01), width=6),
                                    dbc.Col(dbc.Input(id="input-initial-y0", type="number", placeholder="Y", value=0.00, step=0.01), width=6),
                                ]
                            ),
                        ]
                    ),
                ],
                class_name="mb-3",
            ),

            # Group 2: Environment Parameters
            dbc.Card(
                [
                    dbc.CardHeader("Environnement"),
                    dbc.CardBody(
                        [
                            dbc.Label("Frottements"),
                            dcc.Slider(
                                id="input-friction-coef",
                                min=0.0, max=1.0, step=0.05, value=0.3,
                                marks={0: 'Nul', 0.5: 'Moyen', 1: 'Fort'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Br(),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [dbc.Label("Gravité (m/s²)"), dbc.Input(id="input-gravity-g", type="number", value=9.81)], 
                                        width=6
                                    ),
                                    dbc.Col(
                                        [dbc.Label("Masse centrale (kg)"), dbc.Input(id="input-center-mass", type="number", value=0.5)], 
                                        width=6
                                    ),
                                ]
                            )
                        ]
                    ),
                ],
                class_name="mb-3",
            ),

            # Group 3: Advanced Parameters (Hidden by default for simplicity)
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            dbc.Row([
                                dbc.Col([dbc.Label("Tension surface"), dbc.Input(id="input-surface-tension", type="number", value=10.0)], width=6),
                                dbc.Col([dbc.Label("Rayon Centre"), dbc.Input(id="input-center-radius", type="number", value=0.05)], width=6),
                            ], class_name="mb-2"),
                            dbc.Row([
                                dbc.Col([dbc.Label("Rayon Surface"), dbc.Input(id="input-surface-radius", type="number", value=0.5)], width=6),
                                dbc.Col([dbc.Label("Pas de temps (dt)"), dbc.Input(id="input-time-step", type="number", value=0.01)], width=6),
                            ], class_name="mb-2"),
                            dbc.Label("Nombre de steps max"),
                            dbc.Input(id="input-num-steps", type="number", value=800),
                        ],
                        title="Paramètres Avancés (Drap & Calcul)"
                    ),
                ],
                start_collapsed=True,
                class_name="mb-3",
            ),

            dbc.Row(
                [
                    dbc.Col(dbc.Button("Lancer Simulation", id="apply-simulation-inputs", color="primary", class_name="w-100"), width=8),
                    dbc.Col(dbc.Button("Reset", id="reset-simulation-inputs", color="outline-secondary", class_name="w-100"), width=4),
                ],
                class_name="mb-4"
            ),
        ]
    )

    # --- Visualization Zone (Right) ---
    visualization_panel = dbc.Card(
        dbc.CardBody(
            dbc.Tabs(
                [
                    dbc.Tab(
                        dcc.Graph(
                            id="simulation-graph",
                            figure=plot_sim_3d(),
                            config={"responsive": True, "displayModeBar": True},
                            style={"height": "75vh"},
                        ),
                        label="Trajectoire 3D Dynamique",
                    ),
                    dbc.Tab(
                        dcc.Graph(
                            id="simulation-graph-static",
                            figure=_default_simulation_figure(),
                            config={"responsive": True},
                            style={"height": "75vh"},
                        ),
                        label="Vue Statique (Drap)",
                    ),
                ]
            )
        )
    )

    # Page container
    pc = page_container(
        title="Simulateur de Trajectoire",
        body_children=[
            dbc.Row(
                [
                    dbc.Col(control_panel, md=4, lg=3, style={"maxHeight": "calc(100vh - 100px)", "overflowY": "auto"}),
                    dbc.Col(visualization_panel, md=8, lg=9),
                ]
            )
        ],
    )
    return pc["body"]