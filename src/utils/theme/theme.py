"""Theme constants and styling for the application."""

# ── Core palette ─────────────────────────────────────────────────────────────

CLR_BG = "#F8F9FA"
CLR_SURFACE = "#FFFFFF"
CLR_PRIMARY = "#1A73E8"
CLR_PRIMARY_DARK = "#174EA6"   # text on light-blue backgrounds
CLR_PRIMARY_LIGHT = "#E8F0FE"  # info-box / highlight background
CLR_PRIMARY_HOVER = "#F0F6FE"  # very-light hover surface
CLR_TEXT = "#202124"
CLR_TEXT_SECONDARY = "#5F6368"
CLR_BORDER = "#DADCE0"

# ── Semantic status colors ────────────────────────────────────────────────────

CLR_SUCCESS = "#34A853"
CLR_WARNING = "#FBBC04"
CLR_DANGER = "#EA4335"

# Difficulty → color mapping (shared between menu cards and scenario pages)
DIFFICULTY_COLORS: dict[str, str] = {
    "Débutant": CLR_SUCCESS,
    "Intermédiaire": CLR_WARNING,
    "Avancé": CLR_DANGER,
    "Central": CLR_PRIMARY,
}


def difficulty_color(diff: str) -> str:
    """Return the badge color for a given difficulty string."""
    return DIFFICULTY_COLORS.get(diff, CLR_TEXT_SECONDARY)

# ── Presentation mode header ──────────────────────────────────────────────────

CLR_HEADER_BG = "#202124"
CLR_HEADER_SUBTITLE = "#BDC1C6"
CLR_BADGE_BG = "#3C4043"
CLR_STATUS_TEXT = "#9AA0A6"

# ── Plot / simulation colors ──────────────────────────────────────────────────

CLR_PLOT_BG = "#F5F7FA"
CLR_PLOT_CENTER = "#6750A4"
CLR_PLOT_PARTICLE = "#1E88E5"
CLR_PLOT_ORANGE = "#FF9800"
CLR_PLOT_LIGHT_GRAY = "#E0E0E0"

# RGB equivalents (0–1) for pyqtgraph / OpenGL
RGB_PLOT_CENTER = (0.404, 0.314, 0.647, 1.0)
RGB_PLOT_PARTICLE = (0.12, 0.53, 0.90, 1.0)
RGB_PLOT_ORANGE = (1.0, 0.6, 0.0, 0.8)
RGB_PLOT_LIGHT_GRAY = (0.878, 0.878, 0.878, 0.4)
RGB_CENTER_BALL = (0.91, 0.26, 0.21, 1.0)

# ── ML-specific colors ────────────────────────────────────────────────────────

CLR_ML_BG = "#1F2937"
CLR_ML_TRUE = CLR_SUCCESS
CLR_ML_PRED = CLR_PRIMARY
CLR_ML_OBS_BRUSH = CLR_PLOT_ORANGE
CLR_ML_OBS_PEN = "#E65100"
CLR_ML_CURSOR_BRUSH = CLR_PRIMARY

# ── Typography scale ──────────────────────────────────────────────────────────
# Use these anywhere a font-size appears in setStyleSheet() or HTML strings.

FS_XS = "11px"     # hint text, tiny badges
FS_SM = "12px"     # captions, equations, secondary labels
FS_BASE = "13px"   # default body (set globally in STYLESHEET)
FS_MD = "14px"     # slightly emphasised body, form labels
FS_METRIC = "17px" # metric value in dashboard cards
FS_LG = "18px"     # section headings
FS_XL = "20px"     # panel / comparison titles
FS_2XL = "24px"    # page titles (theory, scenario)
FS_3XL = "26px"    # main welcome title

# ── Badge / pill styling ──────────────────────────────────────────────────────
BADGE_PADDING = "2px 10px"
BADGE_RADIUS = "10px"
TAG_PADDING = "4px 10px"
TAG_RADIUS = "8px"
BLOCK_PADDING = "8px"

# ── Slider dimensions ─────────────────────────────────────────────────────────
SLIDER_GROOVE_H = "6px"
SLIDER_GROOVE_RADIUS = "3px"
SLIDER_HANDLE_SIZE = "16px"
SLIDER_HANDLE_MARGIN = "-5px 0"
SLIDER_HANDLE_RADIUS = "8px"

# ── Metric card ───────────────────────────────────────────────────────────────
METRIC_CARD_H = 60

# ── Dashboard layout ──────────────────────────────────────────────────────────
DASH_LEFT_W = 300    # left sidebar width (SimDashboard params panel)
DASH_SIDEBAR_W = 360 # left panel width for scenario/extreme/story views
DASH_CHARTS_H = 240  # live charts panel fixed height
SLIDER_H = 18        # slider widget height (param & speed sliders)
VSEP_H = 22          # vertical separator height in control bars

# ── Overlay / on-dark colors ──────────────────────────────────────────────────
CLR_WHITE = "#FFFFFF"
CLR_WHITE_HOVER = "rgba(255,255,255,0.15)"
CLR_WHITE_FAINT = "rgba(255,255,255,0.6)"

# ── Global stylesheet ─────────────────────────────────────────────────────────

STYLESHEET = f"""
* {{ font-family: 'Google Sans','Roboto','Segoe UI',sans-serif; font-size: {FS_BASE}; }}
QMainWindow {{ background: {CLR_BG}; }}
QWidget {{ background: {CLR_BG}; color: {CLR_TEXT}; }}
QScrollArea {{ background: {CLR_BG}; border: none; }}
QLabel {{ color: {CLR_TEXT}; background: transparent; border: none; }}

/* ── Cards ── */
QFrame[card="true"] {{
    background: {CLR_SURFACE}; border: 1px solid {CLR_BORDER};
    border-radius: 12px; padding: 16px;
}}
QFrame[card="true"]:hover {{ border-color: {CLR_PRIMARY}; background: {CLR_PRIMARY_HOVER}; }}

/* ── Info boxes (blue highlight panels) ── */
QFrame[role="info"] {{
    background: {CLR_PRIMARY_LIGHT}; border: 1px solid {CLR_PRIMARY};
    border-radius: 12px;
}}
QFrame[role="info"] QLabel {{ color: {CLR_PRIMARY_DARK}; }}

/* ── Typography roles ── */
QLabel[role="page-title"]  {{ font-size: {FS_3XL}; font-weight: 500; }}
QLabel[role="panel-title"] {{ font-size: {FS_XL}; font-weight: 500; }}
QLabel[role="section"]     {{ font-size: {FS_LG}; font-weight: 500; margin-top: 8px; }}
QLabel[role="secondary"]   {{ color: {CLR_TEXT_SECONDARY}; font-size: {FS_BASE}; }}

/* ── Buttons ── */
QPushButton {{
    background: {CLR_PRIMARY}; color: white; border: none;
    border-radius: 20px; padding: 8px 24px;
    font-weight: 500; min-height: 28px;
}}
QPushButton:hover {{ background: #1557B0; }}
QPushButton:pressed {{ background: {CLR_PRIMARY_DARK}; }}
QPushButton[secondary="true"] {{
    background: transparent; color: {CLR_PRIMARY}; border: 1px solid {CLR_BORDER};
}}
QPushButton[secondary="true"]:hover {{ background: {CLR_PRIMARY_HOVER}; border-color: {CLR_PRIMARY}; }}
QPushButton[flat="true"] {{
    background: transparent; color: {CLR_PRIMARY}; border: none; padding: 8px 12px;
}}
QPushButton[flat="true"]:hover {{ background: {CLR_PRIMARY_LIGHT}; border-radius: 8px; }}

/* ── Inputs ── */
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
"""


def apply_theme(app):
    app.setStyleSheet(STYLESHEET)
