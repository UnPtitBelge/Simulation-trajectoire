"""
utils.ui.errors

Friendly error components for the Dash app.
Currently provides:
- friendly_404(pathname): a user-friendly 404 page for unknown routes.

Usage:
    from utils.ui.errors import friendly_404
    app.layout = friendly_404("/bad-path")
"""

from __future__ import annotations

from typing import Optional

from dash import dcc, html


def friendly_404(pathname: Optional[str]) -> html.Div:
    """
    Return a friendly 404 component for unknown routes.

    Args:
        pathname: The current URL pathname (e.g., "/unknown").

    Returns:
        A styled Div suggesting valid navigation paths.
    """
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
