from __future__ import annotations

from typing import Optional

from dash import dcc, html


def friendly_404(pathname: Optional[str]) -> html.Div:
    p = pathname or "(unknown)"
    return html.Div(
        className="p-4",
        children=[
            html.H3("Page not found", className="text-danger"),
            html.P(
                f"The path '{p}' does not exist. Please use the navigation links above.",
                className="mb-3",
            ),
            html.Div(
                [
                    dcc.Link("Go to Home", href="/", className="btn btn-primary me-2"),
                    dcc.Link(
                        "Activities",
                        href="/activities",
                        className="btn btn-outline-secondary me-2",
                    ),
                    dcc.Link(
                        "Simulations",
                        href="/simulations",
                        className="btn btn-outline-secondary me-2",
                    ),
                    dcc.Link(
                        "Plots",
                        href="/plots",
                        className="btn btn-outline-secondary",
                    ),
                ],
                className="d-flex flex-wrap gap-2",
            ),
        ],
    )


__all__ = ["friendly_404"]
