"""
utils.ui.nav

Navigation helpers for the Dash app:
- nav_link: standardized NavLink wrapped in a NavItem, using built-in props.
- nav_group: build a Nav container from (label, href) pairs with consistent spacing.
- color_mode_control: right-aligned light/dark mode toggle with icons.

These helpers prefer component built-in props (active, disabled, pills) for semantics,
while relying on Bootstrap utility classes only for layout (e.g., spacing and alignment).
"""

from __future__ import annotations

from typing import Iterable, Tuple

import dash_bootstrap_components as dbc
from dash import html

from .css import NAV_GAP_CLASS, NAV_RIGHT_UTILS_CLASS


def nav_link(
    label: str, href: str, exact: bool = True, disabled: bool = False
) -> dbc.NavItem:
    """
    Create a standardized NavLink wrapped in a NavItem.

    Built-in props used for clarity:
    - active="exact" allows Home ("/") to only match on exact "/".
    - disabled marks the link as inactive without custom classes.

    Args:
        label: Visible text.
        href: Target path (e.g., "/activities").
        exact: If True, uses active="exact"; otherwise uses default truthy active behavior.
        disabled: Disable navigation interaction while keeping layout.

    Returns:
        dbc.NavItem containing a dbc.NavLink.
    """
    return dbc.NavItem(
        dbc.NavLink(
            label,
            href=href,
            active="exact" if exact else True,
            disabled=disabled,
        )
    )


def nav_group(items: Iterable[Tuple[str, str]], pills: bool = False) -> dbc.Nav:
    """
    Build a navbar group from (label, href) pairs.

    Args:
        items: Iterable of (label, href) pairs.
        pills: If True, use Bootstrap 'pills' style for active indication.

    Returns:
        A dbc.Nav with standardized spacing and active styling.
    """
    links = [nav_link(lbl, url, exact=True) for (lbl, url) in items]
    return dbc.Nav(links, navbar=True, class_name=NAV_GAP_CLASS, pills=pills)


def color_mode_control(switch_id: str = "switch") -> html.Span:
    """
    Right-aligned color mode control with a Switch (light/dark).

    Uses built-in dbc.Switch 'value' prop to represent the current mode.
    No custom classes are required besides layout utilities.

    Args:
        switch_id: Component id for the switch.

    Returns:
        A span container with moon/sun icons and a dbc.Switch.
    """
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
