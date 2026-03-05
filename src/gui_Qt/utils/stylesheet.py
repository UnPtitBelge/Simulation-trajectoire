# ===========================================================================
# stylesheet.py — single source of truth for all app styles
# ===========================================================================

# ---------------------------------------------------------------------------
# Colour tokens
# ---------------------------------------------------------------------------

# Backgrounds
CLR_BASE = "#f5f5f7"
CLR_MANTLE = "#eaeaed"
CLR_CRUST = "#dededf"
CLR_SURFACE0 = "#d0d0d5"
CLR_SURFACE1 = "#b0b0ba"
CLR_SURFACE2 = "#88889a"

# Text
CLR_TEXT = "#1c1c28"
CLR_SUBTEXT = "#44445a"
CLR_DIM = "#7878a0"

# Structural
CLR_PANEL_BG = "#ededf0"
CLR_TOPBAR_BG = "#e2e2e8"
CLR_BORDER = "#c8c8d4"
CLR_BORDER_LIGHT = "#dcdce6"

# Accent — indigo / violet
CLR_ACCENT = "#4f46e5"
CLR_ACCENT2 = "#7c3aed"
CLR_ACCENT_LIGHT = "#e0e7ff"
CLR_ACCENT_HOVER = "#4338ca"  # darker indigo for pressed/hover fills

# Status
CLR_GREEN = "#16a34a"
CLR_GREEN_BG = "#dcfce7"
CLR_GREEN_BORDER = "#86efac"
CLR_GREEN_HOVER = "#15803d"
CLR_GREEN_PRESS = "#166534"

CLR_AMBER = "#d97706"
CLR_AMBER_BG = "#fef3c7"
CLR_AMBER_BORDER = "#fcd34d"
CLR_AMBER_HOVER = "#b45309"
CLR_AMBER_PRESS = "#92400e"

CLR_SLATE = "#475569"
CLR_SLATE_BG = "#f1f5f9"
CLR_SLATE_BORDER = "#cbd5e1"
CLR_SLATE_HOVER = "#e2e8f0"
CLR_SLATE_PRESS = "#cbd5e1"

CLR_RED = "#dc2626"
CLR_RED_BG = "#fee2e2"
CLR_RED_BORDER = "#fca5a5"
CLR_RED_HOVER = "#b91c1c"

# ParamControlWidget / ParamsController internal palette
PC_BG = "#f5f5f7"
PC_HEADER_BG = "#ffffff"
PC_HEADER_BG2 = "#eaeaed"
PC_FOOTER_BG = "#ededf0"
PC_GRID_BG = "#f9f9fb"
PC_CELL_BG = "#ffffff"
PC_BORDER = "#c8c8d4"
PC_BORDER_MID = "#d0d0d5"
PC_BORDER_FOCUS = "#4f46e5"
PC_LABEL = "#1c1c28"
PC_LABEL_DIM = "#7878a0"
PC_LABEL_MID = "#44445a"
PC_ACCENT = "#4f46e5"
PC_ACCENT2 = "#7c3aed"
PC_ACCENT2_HOVER = "#9f67fa"
PC_SPINBOX_BG = "#ffffff"
PC_BTN_BG = "#f1f5f9"
PC_BTN_HOVER = "#e0e7ff"
PC_BTN_PRESS = "#c7d2fe"
PC_RESET_BG = "#f1f5f9"
PC_RESET_HOVER = "#e2e8f0"
PC_RESET_PRESS = "#cbd5e1"

# Plot colours
CLR_PLOT_BG = "#ffffff"
CLR_PLOT_GRID = "#e2e8f0"
CLR_PLOT_AXIS = "#94a3b8"
CLR_PLOT_PARTICLE = "#e11d48"
CLR_PLOT_CENTER = "#16a34a"
CLR_PLOT_TRUE = "#16a34a"
CLR_PLOT_PRED = "#e11d48"
CLR_PLOT_MARKER = "#4f46e5"

# Button palette aliases
CLR_START_BG = CLR_GREEN_BG
CLR_START_HOVER = CLR_GREEN_HOVER
CLR_START_PRESS = CLR_GREEN_PRESS
CLR_PAUSE_BG = CLR_AMBER_BG
CLR_PAUSE_HOVER = CLR_AMBER_HOVER
CLR_PAUSE_PRESS = CLR_AMBER_PRESS
CLR_RESET_BG = CLR_SLATE_BG
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
    "QPushButton:disabled {{ color: #b0b0ba; background-color: #ededf0; border-color: #dcdce6; }}"
)

START_STYLE = BTN_BASE.format(
    bg=CLR_GREEN_BG,
    text=CLR_GREEN,
    border=CLR_GREEN_BORDER,
    hover=CLR_GREEN,
    hover_border=CLR_GREEN,
    hover_text="#ffffff",
    press=CLR_GREEN_PRESS,
)
PAUSE_STYLE = BTN_BASE.format(
    bg=CLR_AMBER_BG,
    text=CLR_AMBER,
    border=CLR_AMBER_BORDER,
    hover=CLR_AMBER,
    hover_border=CLR_AMBER,
    hover_text="#ffffff",
    press=CLR_AMBER_PRESS,
)
RESET_STYLE = BTN_BASE.format(
    bg=CLR_SLATE_BG,
    text=CLR_SLATE,
    border=CLR_SLATE_BORDER,
    hover=CLR_SLATE_HOVER,
    hover_border=CLR_SURFACE1,
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
                    stop:0 #ffffff, stop:1 {CLR_TOPBAR_BG});
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
    color: {CLR_SURFACE2};
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
    background-color: {CLR_CRUST};
}}

/* ── Scroll bars ─────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 2px 1px;
}}
QScrollBar::handle:vertical {{
    background: {CLR_SURFACE1};
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
    background: {CLR_SURFACE1};
    border-radius: 3px;
    min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: {CLR_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}

/* ── Tooltip ─────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {CLR_TEXT};
    color: #ffffff;
    border: none;
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
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {CLR_BASE}, stop:1 {CLR_PANEL_BG});
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
        border: 1.5px solid {CLR_ACCENT};
        border-radius: 6px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.2px;
        min-width: 0;
    }}
    QPushButton#hintToggleBtn:hover {{
        background-color: {CLR_ACCENT};
        color: #ffffff;
        border-color: {CLR_ACCENT};
    }}
    QPushButton#hintToggleBtn:pressed {{
        background-color: {CLR_ACCENT2};
        color: #ffffff;
    }}
"""

PLAYBACK_BAR_STYLE = f"""
    QWidget#playbackBar {{
        background-color: {CLR_TOPBAR_BG};
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

# Separator line used inside SimWidget (QFrame inline style replacement)
SEPARATOR_STYLE = f"background: {CLR_BORDER}; border: none;"

# Scroll area inside SimWidget
SCROLL_AREA_STYLE = "border: none; background: transparent;"

# Vertical separator inside the video controls strip (sits against the dark view)
VIDEO_SEP_STYLE = f"background: {CLR_TEXT}; border: none;"

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
        letter-spacing: 0.8px;
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
    QPushButton#stepBtn:hover   {{ background-color: {PC_BTN_HOVER}; color: {PC_LABEL}; border-color: {PC_BORDER_FOCUS}; }}
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
                        stop:0 {PC_HEADER_BG}, stop:1 {PC_HEADER_BG2});
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

# ---------------------------------------------------------------------------
# Video player stylesheet
# ---------------------------------------------------------------------------

VIDEO_PLAYER_STYLE = f"""
    QWidget#videoPlayerOuter {{
        background-color: {CLR_MANTLE};
    }}
    QGraphicsView#videoView {{
        background-color: #1c1c28;
        border: none;
        border-bottom: 1px solid {CLR_BORDER};
    }}
    QWidget#videoControls {{
        background-color: {CLR_PANEL_BG};
        border-top: 1px solid {CLR_BORDER};
    }}
    QFrame#videoSep {{
        background: {CLR_BORDER};
        border: none;
    }}
    QPushButton#videoBtn {{
        background-color: {CLR_SLATE_BG};
        color: {CLR_SLATE};
        border: 1.5px solid {CLR_SLATE_BORDER};
        border-radius: 7px;
        padding: 6px 18px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
        min-width: 72px;
    }}
    QPushButton#videoBtn:hover   {{ background-color: {CLR_SLATE}; color: #ffffff; border-color: {CLR_SLATE}; }}
    QPushButton#videoBtn:pressed {{ background-color: {CLR_SLATE_PRESS}; color: #ffffff; }}
    QPushButton#videoBtn:disabled {{
        color: {CLR_SURFACE2};
        background-color: {CLR_CRUST};
        border-color: {CLR_BORDER_LIGHT};
    }}
    QPushButton#videoBtnPlay {{
        background-color: {CLR_GREEN_BG};
        color: {CLR_GREEN};
        border: 1.5px solid {CLR_GREEN_BORDER};
        border-radius: 7px;
        padding: 6px 18px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.3px;
        min-width: 80px;
    }}
    QPushButton#videoBtnPlay:hover   {{ background-color: {CLR_GREEN}; color: #ffffff; border-color: {CLR_GREEN}; }}
    QPushButton#videoBtnPlay:pressed {{ background-color: {CLR_GREEN_PRESS}; color: #ffffff; }}
    QPushButton#videoBtnLoad {{
        background-color: {CLR_ACCENT_LIGHT};
        color: {CLR_ACCENT};
        border: 1.5px solid {CLR_ACCENT};
        border-radius: 7px;
        padding: 6px 18px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
        min-width: 80px;
    }}
    QPushButton#videoBtnLoad:hover   {{ background-color: {CLR_ACCENT}; color: #ffffff; border-color: {CLR_ACCENT}; }}
    QPushButton#videoBtnLoad:pressed {{ background-color: {CLR_ACCENT2}; color: #ffffff; }}
    QSlider#videoSlider::groove:horizontal {{
        height: 4px;
        background: {CLR_SURFACE0};
        border-radius: 2px;
    }}
    QSlider#videoSlider::handle:horizontal {{
        background: {CLR_ACCENT};
        border: 2px solid #ffffff;
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider#videoSlider::handle:horizontal:hover {{ background: {CLR_ACCENT2}; }}
    QSlider#videoSlider::sub-page:horizontal {{
        background: {CLR_ACCENT};
        border-radius: 2px;
    }}
    QLabel#videoTimeLabel {{
        color: {CLR_DIM};
        font-size: 11px;
        background: transparent;
        min-width: 90px;
    }}
    QLabel#videoPlaceholder {{
        color: {CLR_SURFACE2};
        font-size: 14px;
        font-style: italic;
        background: transparent;
        letter-spacing: 0.3px;
    }}
"""
