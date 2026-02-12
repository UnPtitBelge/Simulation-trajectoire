"""
utils.ui.containers

Containers and routing helpers for the Dash app:
- location_component: dcc.Location for URL-based routing
- loading_container: dcc.Loading wrapper for content
- page_shell: standardized top-level app container (Location + Navbar + Loading-wrapped content)
- page_container: standardized page body wrapper and a plot layout dict builder

These helpers favor component built-in props and return plain Dash component trees
and dicts, making them easy to wire into Dash layouts and callbacks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


def location_component(component_id: str = "url") -> dcc.Location:
    """
    Return a dcc.Location used for multipage routing.

    Args:
        component_id: The id attribute to assign to the Location component.

    Returns:
        A dcc.Location component.
    """
    return dcc.Location(id=component_id)


def loading_container(
    child_id: str = "page-content",
    loader_type: Literal["graph", "cube", "circle", "dot", "default"] | None = "circle",
) -> dcc.Loading:
    """
    Wrap the page content in a Loading spinner.

    Args:
        child_id: The id of the Div where page content is rendered.
        loader_type: Loading indicator type. One of: "graph", "cube", "circle", "dot", "default" or None.

    Returns:
        A dcc.Loading component wrapping an html.Div.
    """
    return dcc.Loading(children=html.Div(id=child_id), type=loader_type)


def page_shell(
    navbar_component,
    *,
    url_id: str = "url",
    content_id: str = "page-content",
    loader_type: Literal["graph", "cube", "circle", "dot", "default"] | None = "circle",
    fluid: bool = True,
):
    """
    Build a standardized top-level app container with:
      - dcc.Location for URL-based routing
      - Provided navbar component
      - A loading wrapper around the page content div

    Args:
        navbar_component: A Dash component tree (e.g., your Navbar.render()).
        url_id: The id for the dcc.Location component.
        content_id: The id for the content div inside the loading wrapper.
        loader_type: The dcc.Loading indicator type.
        fluid: If True, use a fluid dbc.Container.

    Returns:
        A dbc.Container suitable to assign as your app.layout.
    """
    return dbc.Container(
        [
            dcc.Location(id=url_id),
            navbar_component,
            dcc.Loading(children=html.Div(id=content_id), type=loader_type),
        ],
        fluid=fluid,
        style={"paddingTop": "4rem"},
    )


def page_container(
    *,
    title: str = "Page",
    width: Optional[int] = None,
    height: Optional[int] = None,
    showlegend: Optional[bool] = None,
    xaxis: Optional[Dict[str, Any]] = None,
    yaxis: Optional[Dict[str, Any]] = None,
    template: Optional[str] = None,
    margin: Optional[Dict[str, int]] = None,
    body_children: Optional[List[Any]] = None,
    body_class_name: str = "p-3",
):
    """
    Build a standardized page container useful for individual pages.

    - Provides a consistent default figure layout via build_layout when needed.
    - Wraps body_children in a padded container div.

    Args:
        title: Page title (used where appropriate by the caller).
        width, height, showlegend, xaxis, yaxis, template, margin:
            Standard Plotly layout knobs forwarded to build_layout.
        body_children: Optional list of components for the page body.
        body_class_name: Utility classes for the body container.

    Returns:
        A dict containing:
          {
            "layout": <plot layout dict from build_layout(...)>,
            "body": <html.Div>  // the page body wrapper
          }
    """
    # Prefer the shared builder; fallback to a minimal layout if unavailable.
    try:
        from .plots import build_layout as _build_layout  # type: ignore
    except Exception:

        def _build_layout(
            title: str = "Figure",
            width: Optional[int] = None,
            height: Optional[int] = None,
            showlegend: Optional[bool] = None,
            xaxis: Optional[Dict[str, Any]] = None,
            yaxis: Optional[Dict[str, Any]] = None,
            template: Optional[str] = None,
            margin: Optional[Dict[str, int]] = None,
        ) -> Dict[str, Any]:
            layout: Dict[str, Any] = {"title": {"text": title}}
            if width is not None:
                layout["width"] = int(width)
            if height is not None:
                layout["height"] = int(height)
            if showlegend is not None:
                layout["showlegend"] = bool(showlegend)
            if xaxis is not None:
                layout["xaxis"] = xaxis
            if yaxis is not None:
                layout["yaxis"] = yaxis
            if template is not None:
                layout["template"] = template
            if margin is not None:
                layout["margin"] = margin
            return layout

    layout = _build_layout(
        title=title,
        width=width,
        height=height,
        showlegend=showlegend,
        xaxis=xaxis,
        yaxis=yaxis,
        template=template,
        margin=margin,
    )
    body = html.Div(children=body_children or [], className=body_class_name)
    return {"layout": layout, "body": body}


__all__ = [
    "location_component",
    "loading_container",
    "page_shell",
    "page_container",
]
