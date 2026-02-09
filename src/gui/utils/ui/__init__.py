"""
utils.ui package

Clean, explicit re-exports from the split UI standardization submodules.

Usage (recommended):
    from utils.ui import THEME, ICONS_CDN, nav_group, color_mode_control, page_shell, friendly_404
"""

from __future__ import annotations

# Clientside utilities
from .clientside import register_theme_clientside

# Containers, routing, and page shells
from .containers import (
    loading_container,
    location_component,
    page_container,
    page_shell,
)

# Bootstrap utility classes
from .css import NAV_GAP_CLASS, NAV_RIGHT_UTILS_CLASS, NAVBAR_PADDING_CLASS

# Friendly error components
from .errors import friendly_404

# Navigation helpers
from .nav import color_mode_control, nav_group, nav_link

# Plot defaults and layout builder
from .plots import PLOT_DEFAULTS, build_layout

# Theme and external CSS
from .theme import EXTERNAL_STYLESHEETS, ICONS_CDN, THEME

__all__ = [
    # Theme and external CSS
    "THEME",
    "ICONS_CDN",
    "EXTERNAL_STYLESHEETS",
    # Bootstrap utility classes
    "NAV_GAP_CLASS",
    "NAVBAR_PADDING_CLASS",
    "NAV_RIGHT_UTILS_CLASS",
    # Navigation helpers
    "nav_link",
    "nav_group",
    "color_mode_control",
    # Containers and routing
    "location_component",
    "loading_container",
    "page_shell",
    "page_container",
    # Plot helpers
    "PLOT_DEFAULTS",
    "build_layout",
    # Errors
    "friendly_404",
    # Clientside
    "register_theme_clientside",
]
