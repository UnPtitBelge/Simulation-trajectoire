import dash_bootstrap_components as dbc
from dash import dcc, html

def control_panel_3D():
    return html.Div(
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
                        title="Paramètres Avancés (Surface)"
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

def control_panel_2D_newton():
    return html.Div(
        [
            html.H5("Paramètres", className="mb-3"),

            # Group 1: Initial Conditions
            dbc.Card(
                [
                    dbc.CardHeader("Conditions Initiales"),
                    dbc.CardBody(
                        [
                            dbc.Label("Vitesse initiale"),
                            dcc.Slider(
                                id="input-initial-speed-newton",
                                min=0.1, max=10, step=0.1, value=4,
                                marks={0: '0', 1: '1', 2: '2', 3: '3', 5: '5', '6': '6', 8: '8', 10: '10'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Br(),
                            dbc.Label("Angle de tir θ (degrés)"),
                            dcc.Slider(
                                id="input-theta-degrees-newton",
                                min=0, max=360, step=5, value=90,
                                marks={0: '0°', 90: '90°', 180: '180°', 270: '270°', 360: '360°'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Br(),
                            dbc.Label("Distance entre boule"),
                            dcc.Slider(
                                id="input-distance-boule-newton",
                                min=0, max=95, step=5, value=45,
                                marks={0: '0', 15: '15', 30: '30', 45: '45', 60: '60', 75: '75', 90: '90'},
                                tooltip={"placement": "bottom", "always_visible": True}
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
                                id="input-friction-coef-newton",
                                min=0.0, max=1.0, step=0.05, value=0.05,
                                marks={0: 'Nul', 0.5: 'Moyen', 1: 'Fort'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            html.Br(),
                            html.Div(
                                [
                                    dbc.Label("Trajectoire complète"),
                                    dbc.Switch(
                                    id="input-show-full-trajectory-newton",
                                    value=True,
                                ),
                                ]
                            )
                        ]
                    ),
                ],
                class_name="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Button("Lancer Simulation", id="apply-simulation-newton-inputs", color="primary", class_name="w-100"), width=8),
                    dbc.Col(dbc.Button("Reset", id="reset-simulation-newton-inputs", color="outline-secondary", class_name="w-100"), width=4),
                ],
                class_name="mb-4"
            ),
        ]
    )
