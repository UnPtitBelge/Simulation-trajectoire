# ===========================================================================
# stylesheet.py — single source of truth for all app styles
# ===========================================================================

# ---------------------------------------------------------------------------
# Colour tokens
# ---------------------------------------------------------------------------

# Backgrounds
CLR_BASE      = "#0e0f15"
CLR_MANTLE    = "#131520"
CLR_CRUST     = "#191c2a"
CLR_SURFACE0  = "#1f2235"
CLR_SURFACE1  = "#272b40"
CLR_SURFACE2  = "#363b58"

# Text
CLR_TEXT      = "#dde1f0"
CLR_SUBTEXT   = "#8890b0"
CLR_DIM       = "#4f5472"

# Structural
CLR_PANEL_BG      = "#131520"
CLR_TOPBAR_BG     = "#0e0f15"
CLR_BORDER        = "#232640"
CLR_BORDER_LIGHT  = "#1e2135"

# Accent — electric blue
CLR_ACCENT        = "#5b8ff9"
CLR_ACCENT2       = "#4a7bef"
CLR_ACCENT_LIGHT  = "#1a2350"
CLR_ACCENT_HOVER  = "#7aa3fb"

# Status
CLR_GREEN         = "#4ade80"
CLR_GREEN_BG      = "#0d2a1a"
CLR_GREEN_BORDER  = "#1a5c32"
CLR_GREEN_HOVER   = "#22c55e"
CLR_GREEN_PRESS   = "#15803d"

CLR_AMBER         = "#fbbf24"
CLR_AMBER_BG      = "#2a1d00"
CLR_AMBER_BORDER  = "#5c3d00"
CLR_AMBER_HOVER   = "#f59e0b"
CLR_AMBER_PRESS   = "#d97706"

CLR_SLATE         = "#8890b0"
CLR_SLATE_BG      = "#1f2235"
CLR_SLATE_BORDER  = "#363b58"
CLR_SLATE_HOVER   = "#272b40"
CLR_SLATE_PRESS   = "#363b58"

CLR_RED           = "#f87171"
CLR_RED_BG        = "#2a0d0d"
CLR_RED_BORDER    = "#5c1a1a"
CLR_RED_HOVER     = "#ef4444"

# ParamControlWidget / ParamsController internal palette
PC_BG             = "#131520"
PC_HEADER_BG      = "#0e0f15"
PC_HEADER_BG2     = "#131520"
PC_FOOTER_BG      = "#131520"
PC_GRID_BG        = "#1f2235"
PC_CELL_BG        = "#272b40"
PC_BORDER         = "#232640"
PC_BORDER_MID     = "#2a2d45"
PC_BORDER_FOCUS   = "#5b8ff9"
PC_LABEL          = "#dde1f0"
PC_LABEL_DIM      = "#4f5472"
PC_LABEL_MID      = "#8890b0"
PC_ACCENT         = "#5b8ff9"
PC_ACCENT2        = "#4a7bef"
PC_ACCENT2_HOVER  = "#6a9eff"
PC_SPINBOX_BG     = "#191c2a"
PC_BTN_BG         = "#1f2235"
PC_BTN_HOVER      = "#1a2350"
PC_BTN_PRESS      = "#363b58"
PC_RESET_BG       = "#1f2235"
PC_RESET_HOVER    = "#272b40"
PC_RESET_PRESS    = "#363b58"

# Plot colours
CLR_PLOT_BG       = "#070810"
CLR_PLOT_GRID     = "#1a1d2e"
CLR_PLOT_AXIS     = "#363b58"
CLR_PLOT_PARTICLE = "#f0f4ff"
CLR_PLOT_CENTER   = "#e07a10"
CLR_PLOT_DRAP     = "#7a5c30"
CLR_PLOT_TRUE     = "#4ade80"
CLR_PLOT_PRED     = "#f87171"
CLR_PLOT_MARKER   = "#60a5fa"

# Button palette aliases
CLR_START_BG    = CLR_GREEN_BG
CLR_START_HOVER = CLR_GREEN_HOVER
CLR_START_PRESS = CLR_GREEN_PRESS
CLR_PAUSE_BG    = CLR_AMBER_BG
CLR_PAUSE_HOVER = CLR_AMBER_HOVER
CLR_PAUSE_PRESS = CLR_AMBER_PRESS
CLR_RESET_BG    = CLR_SLATE_BG
CLR_RESET_HOVER = CLR_SLATE_HOVER
CLR_RESET_PRESS = CLR_SLATE_PRESS

# ---------------------------------------------------------------------------
# Shared button template
# ---------------------------------------------------------------------------

BTN_BASE = (
    "QPushButton {{"
    "    background-color: {bg};"
    "    color: {text};"
    "    border: 1.5px solid {border};"
    "    border-radius: 8px;"
    "    padding: 7px 22px;"
    "    font-size: 12px;"
    "    font-weight: 700;"
    "    letter-spacing: 0.3px;"
    "    min-width: 88px;"
    "}}"
    "QPushButton:hover   {{ background-color: {hover}; border-color: {hover_border}; color: {hover_text}; }}"
    "QPushButton:pressed {{ background-color: {press}; }}"
    "QPushButton:disabled {{ color: #363b58; background-color: #131520; border-color: #1e2135; }}"
)

START_STYLE = BTN_BASE.format(
    bg=CLR_GREEN_BG,
    text=CLR_GREEN,
    border=CLR_GREEN_BORDER,
    hover=CLR_GREEN,
    hover_border=CLR_GREEN,
    hover_text="#000000",
    press=CLR_GREEN_PRESS,
)
PAUSE_STYLE = BTN_BASE.format(
    bg=CLR_AMBER_BG,
    text=CLR_AMBER,
    border=CLR_AMBER_BORDER,
    hover=CLR_AMBER,
    hover_border=CLR_AMBER,
    hover_text="#000000",
    press=CLR_AMBER_PRESS,
)
RESET_STYLE = BTN_BASE.format(
    bg=CLR_SLATE_BG,
    text=CLR_SLATE,
    border=CLR_SLATE_BORDER,
    hover=CLR_SLATE_HOVER,
    hover_border=CLR_SURFACE2,
    hover_text=CLR_TEXT,
    press=CLR_SLATE_PRESS,
)

# ---------------------------------------------------------------------------
# Global application stylesheet
# ---------------------------------------------------------------------------

APP_STYLESHEET = f"""
/* ── Base ─────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {CLR_BASE};
    color: {CLR_TEXT};
    font-family: "Inter", "SF Pro Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

/* ── Top bar ─────────────────────────────────────────────────────── */
QWidget#topBar {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {CLR_MANTLE}, stop:1 {CLR_BASE});
    border-bottom: 1px solid {CLR_BORDER};
}}
QLabel#topBarTitle {{
    color: {CLR_ACCENT};
    background: transparent;
}}
QPushButton#closeBtn {{
    background-color: {CLR_RED_BG};
    color: {CLR_RED};
    border: 1.5px solid {CLR_RED_BORDER};
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.4px;
}}
QPushButton#closeBtn:hover   {{ background-color: {CLR_RED}; border-color: {CLR_RED}; color: #ffffff; }}
QPushButton#closeBtn:pressed {{ background-color: {CLR_RED_HOVER}; color: #ffffff; }}

/* ── Libre nav bar ───────────────────────────────────────────────── */
QWidget#libreNavBar {{
    background-color: {CLR_MANTLE};
    border-bottom: 1px solid {CLR_BORDER};
}}
QLabel#libreNavTitle {{
    color: {CLR_SUBTEXT};
    background: transparent;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}

/* ── Tab bar ─────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background-color: {CLR_BASE};
}}
QTabWidget::tab-bar {{ alignment: left; }}
QTabBar {{
    background-color: {CLR_MANTLE};
    border-bottom: 1px solid {CLR_BORDER};
}}
QTabBar::tab {{
    background-color: transparent;
    color: {CLR_DIM};
    padding: 10px 28px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.4px;
    min-width: 120px;
}}
QTabBar::tab:selected {{
    color: {CLR_ACCENT};
    border-bottom: 2px solid {CLR_ACCENT};
    background-color: {CLR_BASE};
}}
QTabBar::tab:hover:!selected {{
    color: {CLR_SUBTEXT};
    background-color: {CLR_SURFACE0};
}}

/* ── Scroll bars ─────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 2px 1px;
}}
QScrollBar::handle:vertical {{
    background: {CLR_SURFACE2};
    border-radius: 3px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover  {{ background: {CLR_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 1px 2px;
}}
QScrollBar::handle:horizontal {{
    background: {CLR_SURFACE2};
    border-radius: 3px;
    min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: {CLR_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}

/* ── Tooltip ─────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {CLR_CRUST};
    color: {CLR_TEXT};
    border: 1px solid {CLR_BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}}

/* ── Separator frames ────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {CLR_BORDER};
    border: none;
    background: {CLR_BORDER};
}}
"""

# ---------------------------------------------------------------------------
# SimWidget sub-component stylesheets
# ---------------------------------------------------------------------------

PANEL_STYLE = f"""
    QWidget#controlsWidget {{
        background-color: {CLR_PANEL_BG};
        border-top: 1px solid {CLR_BORDER};
    }}
    QScrollArea {{
        background-color: {CLR_PANEL_BG};
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: {CLR_PANEL_BG};
    }}
    QLabel#sectionLabel {{
        color: {CLR_DIM};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
        background: transparent;
        padding: 0 2px;
    }}
"""

HINT_BAR_STYLE = f"""
    QWidget#hintBar {{
        background: {CLR_MANTLE};
        border-top: 1px solid {CLR_BORDER};
    }}
    QLabel#hintLabel {{
        color: {CLR_DIM};
        font-size: 11px;
        font-style: italic;
        background: transparent;
        letter-spacing: 0.2px;
    }}
    QPushButton#hintToggleBtn {{
        background-color: {CLR_ACCENT_LIGHT};
        color: {CLR_ACCENT};
        border: 1px solid {CLR_ACCENT};
        border-radius: 6px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.2px;
        min-width: 0;
    }}
    QPushButton#hintToggleBtn:hover {{
        background-color: {CLR_ACCENT};
        color: #000000;
        border-color: {CLR_ACCENT};
    }}
    QPushButton#hintToggleBtn:pressed {{
        background-color: {CLR_ACCENT2};
        color: #ffffff;
    }}
"""

PLAYBACK_BAR_STYLE = f"""
    QWidget#playbackBar {{
        background-color: {CLR_MANTLE};
        border-bottom: 1px solid {CLR_BORDER};
    }}
    QLabel#playbackTitle {{
        color: {CLR_DIM};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
        background: transparent;
    }}
"""

SEPARATOR_STYLE = f"background: {CLR_BORDER}; border: none;"
SCROLL_AREA_STYLE = "border: none; background: transparent;"
VIDEO_SEP_STYLE = f"background: {CLR_BORDER}; border: none;"

# ---------------------------------------------------------------------------
# ParamControlWidget / ParamsController stylesheets
# ---------------------------------------------------------------------------

PARAM_CELL_STYLE = f"""
    ParamControlWidget {{
        background: transparent;
    }}
    QLabel#cellLabel {{
        color: {PC_LABEL_DIM};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.6px;
        background: transparent;
    }}
    _NoScrollSpinBox, QDoubleSpinBox {{
        background-color: {PC_SPINBOX_BG};
        color: {PC_LABEL};
        border: 1px solid {PC_BORDER_MID};
        border-radius: 5px;
        padding: 2px 6px;
        font-size: 12px;
        min-height: 24px;
        selection-background-color: {PC_ACCENT};
    }}
    _NoScrollSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {PC_BORDER_FOCUS};
    }}
    _NoScrollSpinBox::up-button,
    _NoScrollSpinBox::down-button,
    QDoubleSpinBox::up-button,
    QDoubleSpinBox::down-button {{
        width: 0px;
        border: none;
    }}
    QPushButton#stepBtn {{
        background-color: {PC_BTN_BG};
        color: {PC_LABEL_MID};
        border: 1px solid {PC_BORDER_MID};
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        min-width: 24px;
        max-width: 24px;
        min-height: 24px;
        max-height: 24px;
    }}
    QPushButton#stepBtn:hover   {{ background-color: {PC_BTN_HOVER}; color: {PC_ACCENT}; border-color: {PC_BORDER_FOCUS}; }}
    QPushButton#stepBtn:pressed {{ background-color: {PC_BTN_PRESS}; color: {PC_LABEL}; }}
    QCheckBox {{
        color: {PC_LABEL};
        font-size: 12px;
        spacing: 8px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {PC_BORDER_MID};
        border-radius: 4px;
        background: {PC_SPINBOX_BG};
    }}
    QCheckBox::indicator:hover {{ border-color: {PC_ACCENT}; }}
    QCheckBox::indicator:checked {{
        background: {PC_ACCENT2};
        border-color: {PC_ACCENT2};
        image: none;
    }}
    QCheckBox::indicator:checked:hover {{
        background: {PC_ACCENT2_HOVER};
        border-color: {PC_ACCENT2_HOVER};
    }}
"""

PARAM_PANEL_STYLE = f"""
    ParamsController {{
        background-color: {PC_BG};
        border: 1px solid {PC_BORDER};
        border-radius: 10px;
    }}
    QWidget#headerBar {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {PC_HEADER_BG2}, stop:1 {PC_HEADER_BG});
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }}
    QLabel#headerTitle {{
        color: {PC_LABEL};
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.9px;
        background: transparent;
    }}
    QLabel#headerDot {{
        color: {PC_ACCENT};
        font-size: 16px;
        background: transparent;
    }}
    QFrame#divider {{
        background: {PC_BORDER};
        border: none;
        max-height: 1px;
    }}
    QWidget#gridArea {{ background: {PC_GRID_BG}; }}
    QWidget#footerBar {{
        background-color: {PC_FOOTER_BG};
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
    }}
    QPushButton#resetBtn {{
        background-color: {PC_RESET_BG};
        color: {PC_LABEL_MID};
        border: 1px solid {PC_BORDER_MID};
        border-radius: 6px;
        padding: 4px 16px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.6px;
        min-width: 80px;
    }}
    QPushButton#resetBtn:hover {{
        background-color: {PC_RESET_HOVER};
        color: {PC_LABEL};
        border-color: {PC_ACCENT};
    }}
    QPushButton#resetBtn:pressed {{ background-color: {PC_RESET_PRESS}; }}
"""

PARAM_CELL_OVERLAY = f"""
    ParamControlWidget {{
        background-color: {PC_CELL_BG};
        border: 1px solid {PC_BORDER_MID};
        border-radius: 7px;
    }}
"""
