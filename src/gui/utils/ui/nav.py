from __future__ import annotations

from typing import Iterable, Tuple

import dash_bootstrap_components as dbc
from dash import html

from .css import NAV_GAP_CLASS, NAV_RIGHT_UTILS_CLASS


def nav_link(
    label: str, href: str, exact: bool = True, disabled: bool = False
) -> dbc.NavItem:
    return dbc.NavItem(
        dbc.NavLink(
            label,
            href=href,
            active="exact" if exact else True,
            disabled=disabled,
        )
    )


def nav_group(items: Iterable[Tuple[str, str]], pills: bool = False) -> dbc.Nav:
    links = [nav_link(lbl, url, exact=True) for (lbl, url) in items]
    return dbc.Nav(links, navbar=True, class_name=NAV_GAP_CLASS, pills=pills)


def color_mode_control(switch_id: str = "switch") -> html.Span:
    return html.Span(
        id="color-mode-switch",
        className=NAV_RIGHT_UTILS_CLASS,
        children=[
            dbc.Label(class_name="fa fa-moon"),
            dbc.Switch(id=switch_id, value=True, class_name="d-inline-block"),
            dbc.Label(class_name="fa fa-sun"),
        ],
    )


__all__ = ["nav_link", "nav_group", "color_mode_control"]
