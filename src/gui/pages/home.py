import dash_bootstrap_components as dbc
from dash import html
from utils.ui import page_container


def layout() -> dbc.Container:
    pc = page_container(
        title="Home",
        body_children=[
            dbc.Card(
                id="welcome-card",
                class_name="my-3",
                children=[
                    dbc.CardHeader("Welcome"),
                    dbc.CardBody(
                        [
                            html.P(
                                "This is the home page of your Dash app.",
                                className="card-text",
                            ),
                        ]
                    ),
                ],
            )
        ],
    )
    return dbc.Container(
        [pc["body"]],
        fluid=True,
        id="home-page",
    )
