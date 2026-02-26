from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html


def location_component(component_id: str = "url") -> dcc.Location:
    return dcc.Location(id=component_id)


def loading_container(
    child_id: str = "page-content",
    loader_type: Literal["graph", "cube", "circle", "dot", "default"] | None = "circle",
) -> dcc.Loading:
    return dcc.Loading(children=html.Div(id=child_id), type=loader_type)


def page_shell(
    navbar_component,
    *,
    url_id: str = "url",
    content_id: str = "page-content",
    loader_type: Literal["graph", "cube", "circle", "dot", "default"] | None = "circle",
    fluid: bool = True,
):
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
