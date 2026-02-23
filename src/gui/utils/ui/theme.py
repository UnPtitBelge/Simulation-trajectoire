from __future__ import annotations

import dash_bootstrap_components as dbc

# Primary Bootstrap theme for the app (can be changed centrally here)
THEME = dbc.themes.FLATLY

# Icon set (Font Awesome via CDN)
ICONS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"

# Convenience bundle for Dash app initialization
EXTERNAL_STYLESHEETS = [THEME, ICONS_CDN]

__all__ = ["THEME", "ICONS_CDN", "EXTERNAL_STYLESHEETS"]
