"""ui_constants.py — All non-colour, non-text layout, size, and numeric constants.

Every magic number used in the Qt UI lives here.  This file has zero
imports and no dependencies — it is a pure declarations module.
"""

# ── Application font ──────────────────────────────────────────────────────
APP_FONT_FAMILY   = "Inter"
APP_FONT_PT       = 12      # default app font (QFont point size)

# ── Stylesheet base sizes (px values embedded in CSS strings) ─────────────
SS_BASE_FS        = 15      # QWidget default font-size
SS_TAB_PAD_V      = 10      # tab-bar vertical padding
SS_TAB_PAD_H      = 28      # tab-bar horizontal padding
SS_TAB_FS         = 14      # tab-bar font-size
SS_TAB_LETTER_SP  = 0.4     # tab letter-spacing (px)
SS_TAB_MIN_W      = 120     # tab min-width
SS_SCROLL_V_W     = 6       # vertical scrollbar width
SS_SCROLL_H_H     = 6       # horizontal scrollbar height
SS_SCROLL_R       = 3       # scrollbar handle border-radius
SS_SCROLL_MIN_HW  = 28      # scrollbar handle min-height / min-width
SS_TOOLTIP_FS     = 14      # tooltip font-size
SS_CLOSE_FS       = 13      # close button font-size
SS_CLOSE_LETTER   = 0.4     # close button letter-spacing
SS_NAV_FS         = 14      # libre-nav-title font-size
SS_BTN_FS         = 14      # base playback button font-size
SS_BTN_PAD_V      = 8       # base button vertical padding
SS_BTN_PAD_H      = 26      # base button horizontal padding
SS_BTN_RADIUS     = 8       # base button border-radius
SS_BTN_MIN_W      = 100     # base button min-width
SS_BTN_WEIGHT     = 700     # base button font-weight
SS_SECTION_FS     = 12      # PANEL section-label font-size
SS_SECTION_LSP    = 1.4     # section-label letter-spacing
SS_HINT_FS        = 13      # hint-bar label font-size
SS_HINT_LSP       = 0.2     # hint-bar letter-spacing
SS_HINT_BTN_FS    = 13      # hint toggle-button font-size
SS_HINT_BTN_PAD   = "4px 14px"
SS_PLAYBACK_FS    = 12      # playback-bar title font-size
SS_PLAYBACK_LSP   = 1.4     # playback-bar letter-spacing
SS_CELL_LABEL_FS  = 12      # param-cell label font-size
SS_CELL_LABEL_LSP = 0.6     # param-cell label letter-spacing
SS_SPIN_FS        = 14      # spinbox font-size
SS_SPIN_MIN_H     = 28      # spinbox min-height
SS_SPIN_PAD       = "2px 6px"
SS_STEP_BTN_FS    = 14      # ± step button font-size
SS_STEP_BTN_SZ    = 28      # ± step button width = height
SS_CHECKBOX_FS    = 14      # checkbox label font-size
SS_CHECKBOX_SZ    = 20      # checkbox indicator side length
SS_CHECKBOX_R     = 4       # checkbox indicator border-radius
SS_HEADER_FS      = 14      # params-panel header font-size
SS_HEADER_LSP     = 0.9     # params-panel header letter-spacing
SS_HEADER_DOT_FS  = 16      # params-panel accent dot font-size
SS_RESET_BTN_FS   = 13      # params-panel reset-button font-size
SS_RESET_BTN_PAD  = "5px 18px"
SS_RESET_BTN_LSP  = 0.6     # reset-button letter-spacing
SS_RESET_BTN_MIN_W = 80     # reset-button min-width

# ── Top bar ───────────────────────────────────────────────────────────────
TOPBAR_H          = 38      # px — fixed height
TOPBAR_TITLE_PT   = 11      # pt — title font (QFont)
TOPBAR_LETTER_SP  = 0.6     # px — title letter-spacing
TOPBAR_MARGINS    = (14, 0, 8, 0)
CLOSE_W           = 96      # px — close button width
CLOSE_H           = 28      # px — close button height

# ── Libre nav bar ─────────────────────────────────────────────────────────
NAV_H             = 56      # px — fixed height
NAV_HOME_BTN_H    = 36      # px
NAV_BTN_H         = 32      # px — simulation-tab buttons
NAV_BTN_SPACING   = 6       # px
NAV_MARGINS       = (16, 0, 16, 0)
NAV_HOME_SPACING  = 16      # px — gap between home and question label
NAV_BTN_FS        = 14      # px — nav button font-size (CSS)
NAV_BTN_PAD       = "4px 14px"
NAV_BTN_RADIUS    = 6       # px — nav button border-radius
NAV_HOVER_ALPHA   = "44"    # 2-hex-digit alpha for hover border
NAV_ACTIVE_ALPHA  = "22"    # 2-hex-digit alpha for active background

# ── Simulation accent colours (single source of truth) ───────────────────
# Used by _LibreNavBar, _ScenarioLanding, and libre_config.CONTENT.
SIM_COLORS = {
    "2d_mcu":      "#06d6a0",
    "3d_cone":     "#ff6b35",
    "3d_membrane": "#118ab2",
    "ml":          "#ef476f",
}

# ── Level selector accent colours ────────────────────────────────────────
LEVEL_CLR = {
    "decouverte": "#06d6a0",
    "lycee":      "#5b8ff9",
    "avance":     "#ef476f",
}

# ── Scenario landing page ─────────────────────────────────────────────────
LANDING_MARGINS      = (60, 40, 60, 40)
LANDING_SPACING      = 20
LANDING_CARDS_GAP    = 20
LANDING_CARD_MARGINS = (20, 20, 20, 20)
LANDING_CARD_SPACING = 10
LANDING_CARD_RADIUS  = 12   # px — card border-radius
LANDING_ACCENT_H     = 4    # px — colored accent bar height
LANDING_ACCENT_R     = 2    # px — accent bar border-radius
LANDING_FS_HEADER    = 28   # px — "Scénarios" title
LANDING_FS_SUB       = 16   # px — subtitle
LANDING_FS_HINT      = 13   # px — keyboard hint
LANDING_FS_NUM       = 24   # px — scenario number badge
LANDING_FS_TITLE     = 16   # px — card title
LANDING_FS_CARD_SUB  = 13   # px — card subtitle
LANDING_FS_BTN       = 14   # px — launch button
LANDING_BTN_RADIUS   = 8    # px
LANDING_BTN_ALPHA    = "22" # background alpha (active)
LANDING_BTN_H_ALPHA  = "44" # background alpha (hover)

# ── SimWidget ─────────────────────────────────────────────────────────────
SIM_PANEL_MAX_H      = 520  # px — scrollable-controls panel max height
SIM_HINT_H           = 30   # px — hint bar fixed height
SIM_HINT_BTN_H       = 22   # px — hint toggle button height
SIM_HINT_MARGINS     = (12, 0, 8, 0)
SIM_HINT_SPACING     = 8
SIM_PLAYBACK_H       = 52   # px — playback bar fixed height
SIM_PLAYBACK_MARGINS = (14, 0, 14, 0)
SIM_PLAYBACK_SPACING = 10
SIM_SEP_H            = 1    # px — separator line height
SIM_PARAMS_MARGINS   = (10, 8, 10, 8)
SIM_PARAMS_SPACING   = 6
SIM_LOADING_FS       = 15   # px — loading label font-size (CSS)

# ── ParamsController ──────────────────────────────────────────────────────
PC_CELL_MARGINS      = (8, 6, 8, 6)
PC_CELL_SPACING      = 4
PC_SPIN_SPACING      = 4
PC_HEADER_H          = 36   # px
PC_HEADER_MARGINS    = (12, 0, 12, 0)
PC_HEADER_SPACING    = 8
PC_DIV_H             = 1    # px — divider height
PC_GRID_MARGINS      = (8, 8, 8, 8)
PC_GRID_SPACING      = 6
PC_FOOTER_MARGINS    = (10, 6, 10, 6)
PC_DEBOUNCE_MS       = 50   # ms — param-change debounce

# ── LibreDashboard geometry ───────────────────────────────────────────────
DASH_STRIP_H         = 280  # px — LibreInfoStrip fixed height
DASH_THROTTLE        = 4    # frames between orbit/sparkline redraws
DASH_GAUGE_W         = 160  # px
DASH_GAUGE_H         = 88   # px
DASH_GAUGE_HUE_MAX   = 120  # HSV hue at zero speed (green = 120°)
DASH_GAUGE_PEN_W     = 8    # px — arc pen width
DASH_GAUGE_FS_NUM    = 12   # pt (QFont) — numeric speed display
DASH_GAUGE_FS_UNIT   = 7    # pt (QFont) — unit label
DASH_ORBIT_SIZE      = 100  # px — orbit trace square side
DASH_ORBIT_MAXLEN    = 300  # trail history length (deque maxlen)
DASH_ORBIT_ALPHA_LO  = 30   # trail minimum alpha
DASH_ORBIT_ALPHA_HI  = 220  # trail maximum alpha
DASH_ORBIT_PEN_W     = 1.2  # px — trail pen width
DASH_ORBIT_DOT_R     = 4    # px — current-position dot radius
DASH_SPARK_H         = 36   # px — sparkline widget height
DASH_SPARK_MAXLEN    = 80   # speed history length (deque maxlen)
DASH_SPARK_PEN_W     = 1.5  # px — sparkline pen width
DASH_SPARK_YPAD      = 3    # px — top/bottom padding inside sparkline
DASH_BTN_H           = 28   # px — level-selector button height
DASH_SCROLL_W        = 3    # px — explanation scrollbar width
DASH_COL1_MIN_W      = 240  # px
DASH_COL2_MIN_W      = 180  # px
DASH_COL1_MARGINS    = (16, 12, 12, 12)
DASH_COL2_MARGINS    = (12, 12, 12, 12)
DASH_COL3_MARGINS    = (12, 12, 16, 12)
DASH_EQ_MARGINS      = (10, 6, 10, 6)
DASH_EQ_RADIUS       = 5    # px — equation box border-radius
DASH_EQ_ALPHA        = "44" # 2-hex alpha for equation box border
DASH_CARD_MARGINS    = (6, 4, 6, 4)
DASH_CARD_RADIUS     = 4    # px — position card border-radius
DASH_FACT_MARGINS    = (10, 8, 10, 8)
DASH_FACT_RADIUS     = 5    # px — fact box border-radius
DASH_BTN_RADIUS      = 4    # px — level button border-radius
DASH_ORBIT_ROW_MARGINS = (0, 4, 0, 0)
DASH_ORBIT_SPACING   = 8
DASH_CARD_SPACING    = 4
DASH_BTN_ROW_SPACING = 5
DASH_COL_SPACING     = 6
DASH_COL3_SPACING    = 8

# ── LibreDashboard font sizes (px, used in CSS strings) ───────────────────
DASH_FS_SECTION      = 11   # section labels ("LE MODÈLE", etc.)
DASH_FS_TITLE        = 16   # model title
DASH_FS_SUBTITLE     = 13   # model subtitle
DASH_FS_EQ           = 13   # equation text
DASH_FS_AXIS         = 10   # XYZ axis letter
DASH_FS_VALUE        = 13   # XYZ numeric value
DASH_FS_EXPL         = 14   # explanation paragraph
DASH_FS_FACT_TITLE   = 12   # fun-fact title
DASH_FS_FACT_BODY    = 13   # fun-fact body
DASH_FS_BTN          = 10   # level-selector buttons

# ── 3-D simulation rendering ──────────────────────────────────────────────
SIM3D_TRAIL_CAP   = 500     # max trajectory trail points kept
SIM3D_TRAIL_SKIP  = 3       # add trail point every N frames
SIM3D_SPHERE_RES  = 32      # sphere mesh U × V subdivisions
SIM3D_TRAIL_W     = 2       # px — GLLinePlotItem width
SIM3D_TRAIL_ALPHA = 0.5     # trajectory line alpha (0-1)
SIM3D_POLAR_NR    = 60      # polar surface mesh: radial rings
SIM3D_POLAR_NPHI  = 120     # polar surface mesh: angular segments
SIM3D_CAM_DIST    = 5       # GLViewWidget camera distance
SIM3D_CAM_ELEV    = 25      # degrees — camera elevation angle
SIM3D_CAM_AZ      = 5       # degrees — camera azimuth angle

# ---------------------------------------------------------------------------
# Material Design 3 — libre mode layout constants
# ---------------------------------------------------------------------------

# Navigation rail (vertical, left side)
MD3_RAIL_W          = 80    # px — fixed width
MD3_RAIL_ITEM_H     = 72    # px — nav item height (icon + label)
MD3_RAIL_INDICATOR_W = 56   # px — active pill width
MD3_RAIL_INDICATOR_H = 32   # px — active pill height
MD3_RAIL_ICON_PT    = 18    # pt — nav icon font size (QFont)
MD3_RAIL_LABEL_FS   = 11    # px — nav label font size (CSS)
MD3_RAIL_LOGO_H     = 56    # px — logo / title area height

# MD3 sidebar (right panel in LibreSimPage)
MD3_SIDEBAR_W       = 360   # px — fixed sidebar width
MD3_CARD_RADIUS     = 12    # px — card border-radius
MD3_CARD_PADDING    = (16, 14, 16, 14)  # margins inside card
MD3_CARD_SPACING    = 8     # px — spacing between cards
MD3_SIDEBAR_MARGINS = (12, 12, 12, 12)
MD3_SIDEBAR_SPACING = 10

# Fonts within the sidebar
MD3_FS_SECTION      = 11    # px — section label ("MODÈLE", "EN DIRECT")
MD3_FS_TITLE        = 18    # px — simulation title
MD3_FS_SUBTITLE     = 13    # px — subtitle
MD3_FS_EQ           = 13    # px — equation monospace
MD3_FS_VALUE        = 13    # px — numeric value (XYZ)
MD3_FS_AXIS         = 10    # px — axis letter (X / Y / Z)
MD3_FS_EXPL         = 14    # px — explanation text
MD3_FS_FACT         = 13    # px — fun fact body
MD3_FS_CHIP         = 11    # px — level chip label

# Gauge
MD3_GAUGE_W         = 160   # px
MD3_GAUGE_H         = 88    # px
MD3_GAUGE_PEN_W     = 8     # px — arc stroke width

# Sparkline
MD3_SPARK_H         = 40    # px
MD3_SPARK_MAXLEN    = 80
MD3_SPARK_PEN_W     = 2.0

# Orbit miniature
MD3_ORBIT_SIZE      = 96    # px
MD3_ORBIT_MAXLEN    = 300
MD3_ORBIT_ALPHA_LO  = 40
MD3_ORBIT_ALPHA_HI  = 220
MD3_ORBIT_PEN_W     = 1.5
MD3_ORBIT_DOT_R     = 4

# Scenarios page
MD3_SCEN_CARD_W     = 220   # px — fixed scenario card width
MD3_SCEN_CARD_H     = 160   # px — fixed scenario card height
MD3_SCEN_CHIP_H     = 22    # px — sim-type badge height
MD3_SCEN_HEADER_FS  = 26    # px — "Scénarios" title
MD3_SCEN_SECTION_FS = 14    # px — section header font size
MD3_SCEN_CARD_FS    = 15    # px — card title
MD3_SCEN_SUB_FS     = 12    # px — card subtitle

# Comparison widget
MD3_CMP_HEADER_H    = 48    # px — header bar height per slot
MD3_CMP_COMBO_H     = 32    # px — combo box height
MD3_THROTTLE        = 4     # frames between heavy redraws (orbit / sparkline)

# ---------------------------------------------------------------------------
# Formula popup dialog (FormulaDialog)
# ---------------------------------------------------------------------------
FORMULA_DLG_MIN_W   = 520
FORMULA_DLG_MIN_H   = 340
FORMULA_DLG_SPACING = 10
FORMULA_DLG_MARGINS = (20, 20, 20, 20)
FORMULA_DLG_FS      = 13
