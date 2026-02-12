"""
Plots page: minimal placeholder

This module provides a standardized minimal layout using utils.ui.page_container.
It renders a heading, short description, and a responsive graph placeholder.
"""

from dash import html
from utils.ui import page_container


def layout():
    """
    Return a standardized minimal placeholder layout for the plots page.
    """
    pc = page_container(
        title="Plots",
        body_children=[
            html.H4("Plots"),
            html.P("This page is a placeholder for future plotting demonstrations."),
        ],
    )
    return pc["body"]
