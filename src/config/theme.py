"""Palette, typographie et stylesheet globale."""

CLR_BG             = "#F8F9FA"
CLR_SURFACE        = "#FFFFFF"
CLR_PRIMARY        = "#1A73E8"
CLR_PRIMARY_DARK   = "#174EA6"
CLR_PRIMARY_LIGHT  = "#E8F0FE"
CLR_PRIMARY_HOVER  = "#F0F6FE"
CLR_TEXT           = "#202124"
CLR_TEXT_SECONDARY = "#5F6368"
CLR_BORDER         = "#DADCE0"

CLR_SUCCESS = "#34A853"
CLR_WARNING = "#FBBC04"
CLR_DANGER  = "#EA4335"

CLR_HEADER_BG       = "#202124"
CLR_HEADER_SUBTITLE = "#BDC1C6"
CLR_BADGE_BG        = "#3C4043"
CLR_STATUS_TEXT     = "#9AA0A6"

CLR_PLOT_BG         = "#F5F7FA"
CLR_PLOT_CENTER     = "#6750A4"
CLR_PLOT_PARTICLE   = "#1E88E5"
CLR_PLOT_ORANGE     = "#FF9800"
CLR_PLOT_LIGHT_GRAY = "#E0E0E0"

RGB_PLOT_CENTER   = (0.404, 0.314, 0.647, 1.0)
RGB_PLOT_PARTICLE = (0.12,  0.53,  0.90,  1.0)
RGB_PLOT_ORANGE   = (1.0,   0.6,   0.0,   0.8)
RGB_PLOT_GRAY     = (0.878, 0.878, 0.878, 0.4)
RGB_CENTER_BALL   = (0.91,  0.26,  0.21,  1.0)
RGB_MARKER        = (0.18,  0.82,  0.28,  1.0)

CLR_ML_TRUE        = CLR_SUCCESS
CLR_ML_PRED        = CLR_PRIMARY
CLR_ML_OBS_BRUSH   = CLR_PLOT_ORANGE

CLR_WHITE       = "#FFFFFF"
CLR_WHITE_HOVER = "rgba(255,255,255,0.15)"

FS_XS     = "11px"
FS_SM     = "12px"
FS_BASE   = "13px"
FS_MD     = "14px"
FS_METRIC = "17px"
FS_LG     = "18px"
FS_XL     = "20px"
FS_2XL    = "24px"
FS_3XL    = "26px"

SMALL_BALL_RADIUS = 0.015
LARGE_BALL_RADIUS = 0.025

STYLESHEET = f"""
* {{ font-family: 'Google Sans','Roboto','Segoe UI',sans-serif; font-size: {FS_BASE}; }}
QMainWindow {{ background: {CLR_BG}; }}
QWidget {{ background: {CLR_BG}; color: {CLR_TEXT}; }}
QScrollArea {{ background: {CLR_BG}; border: none; }}
QLabel {{ color: {CLR_TEXT}; background: transparent; border: none; }}

QFrame[card="true"] {{
    background: {CLR_SURFACE}; border: 1px solid {CLR_BORDER};
    border-radius: 12px; padding: 16px;
}}
QFrame[card="true"]:hover {{ border-color: {CLR_PRIMARY}; background: {CLR_PRIMARY_HOVER}; }}

QFrame[role="info"] {{
    background: {CLR_PRIMARY_LIGHT}; border: 1px solid {CLR_PRIMARY};
    border-radius: 12px;
}}
QFrame[role="info"] QLabel {{ color: {CLR_PRIMARY_DARK}; }}

QLabel[role="page-title"]  {{ font-size: {FS_3XL}; font-weight: 500; }}
QLabel[role="panel-title"] {{ font-size: {FS_XL};  font-weight: 500; }}
QLabel[role="section"]     {{ font-size: {FS_LG};  font-weight: 500; margin-top: 8px; }}
QLabel[role="secondary"]   {{ color: {CLR_TEXT_SECONDARY}; font-size: {FS_BASE}; }}

QPushButton {{
    background: {CLR_PRIMARY}; color: white; border: none;
    border-radius: 20px; padding: 8px 24px;
    font-weight: 500; min-height: 28px;
}}
QPushButton:hover   {{ background: #1557B0; }}
QPushButton:pressed {{ background: {CLR_PRIMARY_DARK}; }}
QPushButton[secondary="true"] {{
    background: transparent; color: {CLR_PRIMARY}; border: 1px solid {CLR_BORDER};
}}
QPushButton[secondary="true"]:hover {{ background: {CLR_PRIMARY_HOVER}; border-color: {CLR_PRIMARY}; }}
QPushButton[flat="true"] {{
    background: transparent; color: {CLR_PRIMARY}; border: none; padding: 8px 12px;
}}
QPushButton[flat="true"]:hover {{ background: {CLR_PRIMARY_LIGHT}; border-radius: 8px; }}

QTextEdit {{
    background: {CLR_SURFACE}; border: 1px solid {CLR_BORDER};
    border-radius: 8px; padding: 12px; color: {CLR_TEXT};
}}
QTabWidget::pane {{
    border: 1px solid {CLR_BORDER}; border-radius: 8px;
    background: {CLR_SURFACE}; top: -1px;
}}
QTabBar::tab {{
    background: transparent; color: {CLR_TEXT_SECONDARY};
    padding: 10px 20px; border: none;
    border-bottom: 2px solid transparent; font-weight: 500;
}}
QTabBar::tab:selected {{ color: {CLR_PRIMARY}; border-bottom: 2px solid {CLR_PRIMARY}; }}
QTabBar::tab:hover:!selected {{ color: {CLR_TEXT}; background: {CLR_PRIMARY_HOVER}; }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{
    background: {CLR_BORDER}; border-radius: 4px; min-height: 40px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QComboBox {{
    background: {CLR_SURFACE}; border: 1px solid {CLR_BORDER};
    border-radius: 8px; padding: 6px 12px;
}}
QComboBox:hover {{ border-color: {CLR_PRIMARY}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QDoubleSpinBox, QSpinBox {{
    background: {CLR_SURFACE}; border: 1px solid {CLR_BORDER};
    border-radius: 6px; padding: 4px 8px;
}}
QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: {CLR_PRIMARY}; }}
"""
