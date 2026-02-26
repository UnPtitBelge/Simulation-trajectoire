import dash_bootstrap_components as dbc
from dash import html
from utils.ui import page_container


def layout() -> dbc.Container:
    pc = page_container(
        title="Activities",
        body_children=[
            dbc.Card(
                [
                    dbc.CardHeader("Activity 1"),
                    dbc.CardBody(
                        [
                            html.P(
                                "Description of Activity 1...", className="card-text"
                            ),
                            dbc.Button(
                                "Start Activity",
                                id="start-activity-1",
                                color="secondary",
                                class_name="w-100 py-2",
                            ),
                        ]
                    ),
                ],
                color="primary",
                outline=True,
                class_name="mb-3",
                id="activity-1",
            ),
        ],
    )
    return dbc.Container(
        [pc["body"]],
        id="activities-page",
        fluid=True,
    )
