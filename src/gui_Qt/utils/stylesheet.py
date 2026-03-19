# ===========================================================================
# stylesheet.py — single source of truth for all app styles
# ===========================================================================

# ---------------------------------------------------------------------------
# Material Design 3 — light theme tokens (used by libre mode)
# ---------------------------------------------------------------------------

# Surfaces
MD3_BG              = "#F8F9FA"   # page background (Google gray-50)
MD3_SURFACE         = "#FFFFFF"   # card / panel surface
MD3_SURFACE_VAR     = "#E8EAED"   # surface variant (Google gray-200)
MD3_SURFACE_TINT    = "#EEF2FF"   # lightly tinted surface (hover states)

# Text / on-surface
MD3_ON_SURFACE      = "#202124"   # primary text (Google gray-900)
MD3_ON_SURFACE_VAR  = "#5F6368"   # secondary text (Google gray-600)
MD3_ON_SURFACE_DIM  = "#9AA0A6"   # dim / placeholder (Google gray-500)

# Borders
MD3_OUTLINE         = "#BDC1C6"   # standard border (Google gray-400)
MD3_OUTLINE_VAR     = "#DADCE0"   # subtle border (Google gray-300)

# Primary (Google Blue)
MD3_PRIMARY         = "#1A73E8"
MD3_ON_PRIMARY      = "#FFFFFF"
MD3_PRIMARY_CONT    = "#D2E3FC"   # primary container (light blue)
MD3_ON_PRIMARY_CONT = "#041E49"   # text on primary container

# Navigation rail
MD3_NAV_BG          = "#FFFFFF"
MD3_NAV_INDICATOR   = "#D2E3FC"   # active item pill background
MD3_NAV_ACTIVE_CLR  = "#1A73E8"   # active icon / label colour
MD3_NAV_INACTIVE    = "#5F6368"   # inactive icon / label colour

# Elevation / shadow
MD3_SHADOW_SM       = "rgba(0,0,0,0.06)"
MD3_SHADOW          = "rgba(0,0,0,0.10)"

# ---------------------------------------------------------------------------
# Colour tokens — dark theme (defaults)
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

# Plot colours (never change with theme)
CLR_PLOT_BG       = "#070810"
CLR_PLOT_GRID     = "#1a1d2e"
CLR_PLOT_AXIS     = "#363b58"
CLR_PLOT_PARTICLE = "#E53935"
CLR_PLOT_CENTER   = "#e07a10"
CLR_PLOT_DRAP     = "#7a5c30"
CLR_PLOT_TRUE     = "#4ade80"
CLR_PLOT_PRED     = "#f87171"
CLR_PLOT_MARKER   = "#60a5fa"

# Dashboard / overlay colours (theme-aware via set_theme)
CLR_OVERLAY_BG   = "rgba(20, 20, 20, 210)"
CLR_GAUGE_TRACK  = "#1a1d2e"
CLR_MINI_BG      = "#070810"
CLR_MINI_BORDER  = "#1a1d2e"

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
# Light theme tokens
# ---------------------------------------------------------------------------
_L_BASE      = "#f4f6fd"
_L_MANTLE    = "#eceef8"
_L_CRUST     = "#e2e5f5"
_L_SURFACE0  = "#d5d9f0"
_L_SURFACE1  = "#c8cde8"
_L_SURFACE2  = "#b5bbde"
_L_TEXT      = "#1a1d2e"
_L_SUBTEXT   = "#3d4268"
_L_DIM       = "#7880a8"
_L_PANEL_BG      = "#eceef8"
_L_TOPBAR_BG     = "#f4f6fd"
_L_BORDER        = "#c8cde8"
_L_BORDER_LIGHT  = "#d5d9f0"
_L_ACCENT        = "#2b5ce6"
_L_ACCENT2       = "#1e4dd4"
_L_ACCENT_LIGHT  = "#e8effd"
_L_ACCENT_HOVER  = "#4070f0"
_L_PC_BG         = "#eceef8"
_L_PC_HEADER_BG  = "#f4f6fd"
_L_PC_HEADER_BG2 = "#eceef8"
_L_PC_FOOTER_BG  = "#eceef8"
_L_PC_GRID_BG    = "#d5d9f0"
_L_PC_CELL_BG    = "#c8cde8"
_L_PC_BORDER     = "#c8cde8"
_L_PC_BORDER_MID = "#b5bbde"
_L_PC_LABEL      = "#1a1d2e"
_L_PC_LABEL_DIM  = "#5860a0"
_L_PC_LABEL_MID  = "#3d4268"
_L_PC_SPINBOX_BG = "#ffffff"
_L_PC_BTN_BG     = "#d5d9f0"
_L_PC_BTN_HOVER  = "#c8cde8"
_L_PC_BTN_PRESS  = "#b5bbde"
_L_PC_RESET_BG   = "#d5d9f0"
_L_PC_RESET_HOVER = "#c8cde8"
_L_PC_RESET_PRESS = "#b5bbde"
_L_PC_ACCENT     = "#2b5ce6"
_L_PC_ACCENT2    = "#1e4dd4"
_L_PC_ACCENT2_HOVER = "#4070f0"
_L_PC_BORDER_FOCUS = "#2b5ce6"

_L_PLOT_BG        = "#ffffff"
_L_PLOT_GRID      = "#c8cde8"
_L_PLOT_PARTICLE  = "#E53935"

from utils.ui_constants import (
    SS_BASE_FS, SS_TAB_PAD_V, SS_TAB_PAD_H, SS_TAB_FS, SS_TAB_LETTER_SP,
    SS_TAB_MIN_W, SS_SCROLL_V_W, SS_SCROLL_H_H, SS_SCROLL_R, SS_SCROLL_MIN_HW,
    SS_TOOLTIP_FS, SS_CLOSE_FS, SS_CLOSE_LETTER, SS_NAV_FS, SS_BTN_FS,
    SS_BTN_PAD_V, SS_BTN_PAD_H, SS_BTN_RADIUS, SS_BTN_MIN_W, SS_BTN_WEIGHT,
    SS_SECTION_FS, SS_SECTION_LSP, SS_HINT_FS, SS_HINT_LSP, SS_HINT_BTN_FS,
    SS_HINT_BTN_PAD, SS_PLAYBACK_FS, SS_PLAYBACK_LSP, SS_CELL_LABEL_FS,
    SS_CELL_LABEL_LSP, SS_SPIN_FS, SS_SPIN_MIN_H, SS_SPIN_PAD, SS_STEP_BTN_FS,
    SS_STEP_BTN_SZ, SS_CHECKBOX_FS, SS_CHECKBOX_SZ, SS_CHECKBOX_R,
    SS_HEADER_FS, SS_HEADER_LSP, SS_HEADER_DOT_FS, SS_RESET_BTN_FS,
    SS_RESET_BTN_PAD, SS_RESET_BTN_LSP, SS_RESET_BTN_MIN_W,
)

# ---------------------------------------------------------------------------
# Build functions — reference module-level globals at call time
# ---------------------------------------------------------------------------

def _mk_btn_base() -> str:
    disabled_clr   = CLR_SURFACE2
    disabled_bg    = CLR_MANTLE
    disabled_bdr   = CLR_BORDER_LIGHT
    return (
        "QPushButton {{"
        "    background-color: {bg};"
        "    color: {text};"
        "    border: 1.5px solid {border};"
        f"    border-radius: {SS_BTN_RADIUS}px;"
        f"    padding: {SS_BTN_PAD_V}px {SS_BTN_PAD_H}px;"
        f"    font-size: {SS_BTN_FS}px;"
        f"    font-weight: {SS_BTN_WEIGHT};"
        "    letter-spacing: 0.3px;"
        f"    min-width: {SS_BTN_MIN_W}px;"
        "}}"
        "QPushButton:hover   {{ background-color: {hover}; border-color: {hover_border}; color: {hover_text}; }}"
        "QPushButton:pressed {{ background-color: {press}; }}"
        f"QPushButton:disabled {{{{ color: {disabled_clr}; background-color: {disabled_bg}; border-color: {disabled_bdr}; }}}}"
    )


def _mk_start_style() -> str:
    return BTN_BASE.format(
        bg=CLR_GREEN_BG,
        text=CLR_GREEN,
        border=CLR_GREEN_BORDER,
        hover=CLR_GREEN,
        hover_border=CLR_GREEN,
        hover_text="#000000",
        press=CLR_GREEN_PRESS,
    )


def _mk_pause_style() -> str:
    return BTN_BASE.format(
        bg=CLR_AMBER_BG,
        text=CLR_AMBER,
        border=CLR_AMBER_BORDER,
        hover=CLR_AMBER,
        hover_border=CLR_AMBER,
        hover_text="#000000",
        press=CLR_AMBER_PRESS,
    )


def _mk_reset_style() -> str:
    return BTN_BASE.format(
        bg=CLR_SLATE_BG,
        text=CLR_SLATE,
        border=CLR_SLATE_BORDER,
        hover=CLR_SLATE_HOVER,
        hover_border=CLR_SURFACE2,
        hover_text=CLR_TEXT,
        press=CLR_SLATE_PRESS,
    )


def _mk_app_stylesheet() -> str:
    return f"""
/* ── Base ─────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {CLR_BASE};
    color: {CLR_TEXT};
    font-family: "Inter", "SF Pro Text", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: {SS_BASE_FS}px;
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
    font-size: {SS_CLOSE_FS}px;
    font-weight: 700;
    letter-spacing: {SS_CLOSE_LETTER}px;
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
    font-size: {SS_NAV_FS}px;
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
    padding: {SS_TAB_PAD_V}px {SS_TAB_PAD_H}px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: {SS_TAB_FS}px;
    letter-spacing: {SS_TAB_LETTER_SP}px;
    min-width: {SS_TAB_MIN_W}px;
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
    width: {SS_SCROLL_V_W}px;
    margin: 2px 1px;
}}
QScrollBar::handle:vertical {{
    background: {CLR_SURFACE2};
    border-radius: {SS_SCROLL_R}px;
    min-height: {SS_SCROLL_MIN_HW}px;
}}
QScrollBar::handle:vertical:hover  {{ background: {CLR_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{
    background: transparent;
    height: {SS_SCROLL_H_H}px;
    margin: 1px 2px;
}}
QScrollBar::handle:horizontal {{
    background: {CLR_SURFACE2};
    border-radius: {SS_SCROLL_R}px;
    min-width: {SS_SCROLL_MIN_HW}px;
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
    font-size: {SS_TOOLTIP_FS}px;
}}

/* ── Separator frames ────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {CLR_BORDER};
    border: none;
    background: {CLR_BORDER};
}}
"""


def _mk_panel_style() -> str:
    return f"""
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
        font-size: {SS_SECTION_FS}px;
        font-weight: 700;
        letter-spacing: {SS_SECTION_LSP}px;
        background: transparent;
        padding: 0 2px;
    }}
"""


def _mk_hint_bar_style() -> str:
    return f"""
    QWidget#hintBar {{
        background: {CLR_MANTLE};
        border-top: 1px solid {CLR_BORDER};
    }}
    QLabel#hintLabel {{
        color: {CLR_DIM};
        font-size: {SS_HINT_FS}px;
        font-style: italic;
        background: transparent;
        letter-spacing: {SS_HINT_LSP}px;
    }}
    QPushButton#hintToggleBtn {{
        background-color: {CLR_ACCENT_LIGHT};
        color: {CLR_ACCENT};
        border: 1px solid {CLR_ACCENT};
        border-radius: 6px;
        padding: {SS_HINT_BTN_PAD};
        font-size: {SS_HINT_BTN_FS}px;
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


def _mk_playback_bar_style() -> str:
    return f"""
    QWidget#playbackBar {{
        background-color: {CLR_MANTLE};
        border-bottom: 1px solid {CLR_BORDER};
    }}
    QLabel#playbackTitle {{
        color: {CLR_DIM};
        font-size: {SS_PLAYBACK_FS}px;
        font-weight: 700;
        letter-spacing: {SS_PLAYBACK_LSP}px;
        background: transparent;
    }}
"""


def _mk_separator_style() -> str:
    return f"background: {CLR_BORDER}; border: none;"


def _mk_video_sep_style() -> str:
    return f"background: {CLR_BORDER}; border: none;"


def _mk_param_cell_style() -> str:
    return f"""
    ParamControlWidget {{
        background: transparent;
    }}
    QLabel#cellLabel {{
        color: {PC_LABEL_DIM};
        font-size: {SS_CELL_LABEL_FS}px;
        font-weight: 700;
        letter-spacing: {SS_CELL_LABEL_LSP}px;
        background: transparent;
    }}
    _NoScrollSpinBox, QDoubleSpinBox {{
        background-color: {PC_SPINBOX_BG};
        color: {PC_LABEL};
        border: 1px solid {PC_BORDER_MID};
        border-radius: 5px;
        padding: {SS_SPIN_PAD};
        font-size: {SS_SPIN_FS}px;
        min-height: {SS_SPIN_MIN_H}px;
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
        font-size: {SS_STEP_BTN_FS}px;
        font-weight: bold;
        min-width: {SS_STEP_BTN_SZ}px;
        max-width: {SS_STEP_BTN_SZ}px;
        min-height: {SS_STEP_BTN_SZ}px;
        max-height: {SS_STEP_BTN_SZ}px;
    }}
    QPushButton#stepBtn:hover   {{ background-color: {PC_BTN_HOVER}; color: {PC_ACCENT}; border-color: {PC_BORDER_FOCUS}; }}
    QPushButton#stepBtn:pressed {{ background-color: {PC_BTN_PRESS}; color: {PC_LABEL}; }}
    QCheckBox {{
        color: {PC_LABEL};
        font-size: {SS_CHECKBOX_FS}px;
        spacing: 8px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: {SS_CHECKBOX_SZ}px;
        height: {SS_CHECKBOX_SZ}px;
        border: 1px solid {PC_BORDER_MID};
        border-radius: {SS_CHECKBOX_R}px;
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


def _mk_param_panel_style() -> str:
    return f"""
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
        font-size: {SS_HEADER_FS}px;
        font-weight: 700;
        letter-spacing: {SS_HEADER_LSP}px;
        background: transparent;
    }}
    QLabel#headerDot {{
        color: {PC_ACCENT};
        font-size: {SS_HEADER_DOT_FS}px;
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
        padding: {SS_RESET_BTN_PAD};
        font-size: {SS_RESET_BTN_FS}px;
        font-weight: 700;
        letter-spacing: {SS_RESET_BTN_LSP}px;
        min-width: {SS_RESET_BTN_MIN_W}px;
    }}
    QPushButton#resetBtn:hover {{
        background-color: {PC_RESET_HOVER};
        color: {PC_LABEL};
        border-color: {PC_ACCENT};
    }}
    QPushButton#resetBtn:pressed {{ background-color: {PC_RESET_PRESS}; }}
"""


def _mk_param_cell_overlay() -> str:
    return f"""
    ParamControlWidget {{
        background-color: {PC_CELL_BG};
        border: 1px solid {PC_BORDER_MID};
        border-radius: 7px;
    }}
"""


# ---------------------------------------------------------------------------
# Module-level style constants (initialised from build functions)
# ---------------------------------------------------------------------------

BTN_BASE           = _mk_btn_base()
START_STYLE        = _mk_start_style()
PAUSE_STYLE        = _mk_pause_style()
RESET_STYLE        = _mk_reset_style()
APP_STYLESHEET     = _mk_app_stylesheet()
PANEL_STYLE        = _mk_panel_style()
HINT_BAR_STYLE     = _mk_hint_bar_style()
PLAYBACK_BAR_STYLE = _mk_playback_bar_style()
SEPARATOR_STYLE    = _mk_separator_style()
SCROLL_AREA_STYLE  = "border: none; background: transparent;"
VIDEO_SEP_STYLE    = _mk_video_sep_style()
PARAM_CELL_STYLE   = _mk_param_cell_style()
PARAM_PANEL_STYLE  = _mk_param_panel_style()
PARAM_CELL_OVERLAY = _mk_param_cell_overlay()


# ---------------------------------------------------------------------------
# Theme switching
# ---------------------------------------------------------------------------

def set_theme(light: bool) -> None:
    """Switch between dark (default) and light theme.

    Updates all global CLR_* and PC_* constants then rebuilds every
    style-string constant so subsequent reads pick up the new theme.
    Plots colours (CLR_PLOT_*) and status colours (green/amber/slate/red)
    are intentionally left unchanged — they look fine on both themes.
    """
    global CLR_BASE, CLR_MANTLE, CLR_CRUST, CLR_SURFACE0, CLR_SURFACE1, CLR_SURFACE2
    global CLR_TEXT, CLR_SUBTEXT, CLR_DIM
    global CLR_PANEL_BG, CLR_TOPBAR_BG, CLR_BORDER, CLR_BORDER_LIGHT
    global CLR_ACCENT, CLR_ACCENT2, CLR_ACCENT_LIGHT, CLR_ACCENT_HOVER
    global CLR_START_BG, CLR_START_HOVER, CLR_START_PRESS
    global CLR_PAUSE_BG, CLR_PAUSE_HOVER, CLR_PAUSE_PRESS
    global CLR_RESET_BG, CLR_RESET_HOVER, CLR_RESET_PRESS
    global PC_BG, PC_HEADER_BG, PC_HEADER_BG2, PC_FOOTER_BG
    global PC_GRID_BG, PC_CELL_BG, PC_BORDER, PC_BORDER_MID, PC_BORDER_FOCUS
    global PC_LABEL, PC_LABEL_DIM, PC_LABEL_MID
    global PC_ACCENT, PC_ACCENT2, PC_ACCENT2_HOVER
    global PC_SPINBOX_BG, PC_BTN_BG, PC_BTN_HOVER, PC_BTN_PRESS
    global PC_RESET_BG, PC_RESET_HOVER, PC_RESET_PRESS
    global BTN_BASE, START_STYLE, PAUSE_STYLE, RESET_STYLE
    global APP_STYLESHEET, PANEL_STYLE, HINT_BAR_STYLE, PLAYBACK_BAR_STYLE
    global SEPARATOR_STYLE, VIDEO_SEP_STYLE
    global PARAM_CELL_STYLE, PARAM_PANEL_STYLE, PARAM_CELL_OVERLAY
    global CLR_OVERLAY_BG, CLR_GAUGE_TRACK, CLR_MINI_BG, CLR_MINI_BORDER
    global CLR_PLOT_BG, CLR_PLOT_GRID, CLR_PLOT_PARTICLE

    if light:
        CLR_BASE     = _L_BASE
        CLR_MANTLE   = _L_MANTLE
        CLR_CRUST    = _L_CRUST
        CLR_SURFACE0 = _L_SURFACE0
        CLR_SURFACE1 = _L_SURFACE1
        CLR_SURFACE2 = _L_SURFACE2
        CLR_TEXT     = _L_TEXT
        CLR_SUBTEXT  = _L_SUBTEXT
        CLR_DIM      = _L_DIM
        CLR_PANEL_BG     = _L_PANEL_BG
        CLR_TOPBAR_BG    = _L_TOPBAR_BG
        CLR_BORDER       = _L_BORDER
        CLR_BORDER_LIGHT = _L_BORDER_LIGHT
        CLR_ACCENT       = _L_ACCENT
        CLR_ACCENT2      = _L_ACCENT2
        CLR_ACCENT_LIGHT = _L_ACCENT_LIGHT
        CLR_ACCENT_HOVER = _L_ACCENT_HOVER
        PC_BG          = _L_PC_BG
        PC_HEADER_BG   = _L_PC_HEADER_BG
        PC_HEADER_BG2  = _L_PC_HEADER_BG2
        PC_FOOTER_BG   = _L_PC_FOOTER_BG
        PC_GRID_BG     = _L_PC_GRID_BG
        PC_CELL_BG     = _L_PC_CELL_BG
        PC_BORDER      = _L_PC_BORDER
        PC_BORDER_MID  = _L_PC_BORDER_MID
        PC_BORDER_FOCUS = _L_PC_BORDER_FOCUS
        PC_LABEL       = _L_PC_LABEL
        PC_LABEL_DIM   = _L_PC_LABEL_DIM
        PC_LABEL_MID   = _L_PC_LABEL_MID
        PC_SPINBOX_BG  = _L_PC_SPINBOX_BG
        PC_BTN_BG      = _L_PC_BTN_BG
        PC_BTN_HOVER   = _L_PC_BTN_HOVER
        PC_BTN_PRESS   = _L_PC_BTN_PRESS
        PC_RESET_BG    = _L_PC_RESET_BG
        PC_RESET_HOVER = _L_PC_RESET_HOVER
        PC_RESET_PRESS = _L_PC_RESET_PRESS
        PC_ACCENT      = _L_PC_ACCENT
        PC_ACCENT2     = _L_PC_ACCENT2
        PC_ACCENT2_HOVER = _L_PC_ACCENT2_HOVER
        CLR_OVERLAY_BG  = "rgba(232, 237, 250, 220)"
        CLR_GAUGE_TRACK = _L_SURFACE1
        CLR_MINI_BG     = _L_CRUST
        CLR_MINI_BORDER = _L_SURFACE1
        CLR_PLOT_BG      = _L_PLOT_BG
        CLR_PLOT_GRID    = _L_PLOT_GRID
        CLR_PLOT_PARTICLE = _L_PLOT_PARTICLE
    else:
        CLR_BASE     = "#0e0f15"
        CLR_MANTLE   = "#131520"
        CLR_CRUST    = "#191c2a"
        CLR_SURFACE0 = "#1f2235"
        CLR_SURFACE1 = "#272b40"
        CLR_SURFACE2 = "#363b58"
        CLR_TEXT     = "#dde1f0"
        CLR_SUBTEXT  = "#8890b0"
        CLR_DIM      = "#4f5472"
        CLR_PANEL_BG     = "#131520"
        CLR_TOPBAR_BG    = "#0e0f15"
        CLR_BORDER       = "#232640"
        CLR_BORDER_LIGHT = "#1e2135"
        CLR_ACCENT       = "#5b8ff9"
        CLR_ACCENT2      = "#4a7bef"
        CLR_ACCENT_LIGHT = "#1a2350"
        CLR_ACCENT_HOVER = "#7aa3fb"
        PC_BG          = "#131520"
        PC_HEADER_BG   = "#0e0f15"
        PC_HEADER_BG2  = "#131520"
        PC_FOOTER_BG   = "#131520"
        PC_GRID_BG     = "#1f2235"
        PC_CELL_BG     = "#272b40"
        PC_BORDER      = "#232640"
        PC_BORDER_MID  = "#2a2d45"
        PC_BORDER_FOCUS = "#5b8ff9"
        PC_LABEL       = "#dde1f0"
        PC_LABEL_DIM   = "#4f5472"
        PC_LABEL_MID   = "#8890b0"
        PC_SPINBOX_BG  = "#191c2a"
        PC_BTN_BG      = "#1f2235"
        PC_BTN_HOVER   = "#1a2350"
        PC_BTN_PRESS   = "#363b58"
        PC_RESET_BG    = "#1f2235"
        PC_RESET_HOVER = "#272b40"
        PC_RESET_PRESS = "#363b58"
        PC_ACCENT      = "#5b8ff9"
        PC_ACCENT2     = "#4a7bef"
        PC_ACCENT2_HOVER = "#6a9eff"
        CLR_OVERLAY_BG  = "rgba(20, 20, 20, 210)"
        CLR_GAUGE_TRACK = "#1a1d2e"
        CLR_MINI_BG     = "#070810"
        CLR_MINI_BORDER = "#1a1d2e"
        CLR_PLOT_BG      = "#070810"
        CLR_PLOT_GRID    = "#1a1d2e"
        CLR_PLOT_PARTICLE = "#E53935"

    # Button palette aliases (status colours stay same on both themes)
    CLR_START_BG    = CLR_GREEN_BG
    CLR_START_HOVER = CLR_GREEN_HOVER
    CLR_START_PRESS = CLR_GREEN_PRESS
    CLR_PAUSE_BG    = CLR_AMBER_BG
    CLR_PAUSE_HOVER = CLR_AMBER_HOVER
    CLR_PAUSE_PRESS = CLR_AMBER_PRESS
    CLR_RESET_BG    = CLR_SLATE_BG
    CLR_RESET_HOVER = CLR_SLATE_HOVER
    CLR_RESET_PRESS = CLR_SLATE_PRESS

    # Rebuild all style strings
    BTN_BASE           = _mk_btn_base()
    START_STYLE        = _mk_start_style()
    PAUSE_STYLE        = _mk_pause_style()
    RESET_STYLE        = _mk_reset_style()
    APP_STYLESHEET     = _mk_app_stylesheet()
    PANEL_STYLE        = _mk_panel_style()
    HINT_BAR_STYLE     = _mk_hint_bar_style()
    PLAYBACK_BAR_STYLE = _mk_playback_bar_style()
    SEPARATOR_STYLE    = _mk_separator_style()
    VIDEO_SEP_STYLE    = _mk_video_sep_style()
    PARAM_CELL_STYLE   = _mk_param_cell_style()
    PARAM_PANEL_STYLE  = _mk_param_panel_style()
    PARAM_CELL_OVERLAY = _mk_param_cell_overlay()
