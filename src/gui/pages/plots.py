from dash import html
from utils.ui import page_container


def layout():
    pc = page_container(
        title="Plots",
        body_children=[
            html.H4("Plots"),
            html.P("This page is a placeholder for future plotting demonstrations."),
        ],
    )
    return pc["body"]
