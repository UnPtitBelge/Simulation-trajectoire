"""
utils.ui.theme

Theme and external CSS constants for the Dash app.

Exports:
- THEME: The Dash Bootstrap Components theme to use application-wide.
- ICONS_CDN: CDN URL for Font Awesome icons.
- EXTERNAL_STYLESHEETS: Convenience list combining THEME and ICONS_CDN for Dash app config.

Usage:
    from utils.ui.theme import THEME, ICONS_CDN, EXTERNAL_STYLESHEETS

    app = dash.Dash(
        __name__,
        external_stylesheets=EXTERNAL_STYLESHEETS,
        suppress_callback_exceptions=True,
    )
"""

from __future__ import annotations

import dash_bootstrap_components as dbc

# Primary Bootstrap theme for the app (can be changed centrally here)
THEME = dbc.themes.FLATLY

# Icon set (Font Awesome via CDN)
ICONS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"

# Convenience bundle for Dash app initialization
EXTERNAL_STYLESHEETS = [THEME, ICONS_CDN]

__all__ = ["THEME", "ICONS_CDN", "EXTERNAL_STYLESHEETS"]
