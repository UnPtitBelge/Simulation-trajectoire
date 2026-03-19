"""ui_strings.py — All user-visible text strings for the Qt UI.

Centralising strings here makes copy-editing and future localisation
straightforward.  No imports, no dependencies.
"""

# ── Application ───────────────────────────────────────────────────────────
WINDOW_TITLE     = "Models & Simulations"
TOPBAR_TITLE     = "⬡  Models & Simulations"
CLOSE_BTN        = "✕  Close"

# ── Libre nav bar ─────────────────────────────────────────────────────────
NAV_QUESTION     = "Comment les ordinateurs simulent la réalité ?"
NAV_HOME_BTN     = "⌂  Scénarios"
NAV_SIM_LABELS   = ["2D MCU", "3D Cône", "3D Membrane", "ML"]

# ── Normal-mode tab labels ────────────────────────────────────────────────
TAB_MCU          = "2D MCU"
TAB_CONE         = "3D Cône"
TAB_MEMBRANE     = "3D Membrane"
TAB_ML           = "Machine Learning"

# ── Scenario landing page ─────────────────────────────────────────────────
LANDING_HEADER   = "Scénarios"
LANDING_SUBTITLE = "Comment les ordinateurs simulent la réalité ?"
LANDING_HINT     = "Raccourcis clavier :  1  2  3  4"
LANDING_BTN      = "Lancer  →"
LANDING_SIM_KEYS = ["2d_mcu", "3d_cone", "3d_membrane", "ml"]
LANDING_SIM_NUMS = ["1", "2", "3", "4"]

# ── SimWidget playback controls ───────────────────────────────────────────
LOADING_TEXT     = "Calcul en cours…"
HINT_TEXT        = "Space  Pause   ·   Ctrl+R  Reset"
CONTROLS_BTN     = "⚙  Controls  (Ctrl+P)"
PLAYBACK_TITLE   = "PLAYBACK"
START_BTN        = "▶  Start"
PAUSE_BTN        = "⏸  Pause"
RESUME_BTN       = "▶  Resume"
RESET_BTN        = "↺  Reset"

# ── ParamsController ──────────────────────────────────────────────────────
PC_RESET_BTN     = "↺  Réinitialiser"

# ── Dashboard section labels ──────────────────────────────────────────────
DASH_SECTION_MODEL = "LE MODÈLE"
DASH_SECTION_LIVE  = "EN DIRECT"
DASH_SECTION_TRAJ  = "TRAJECTOIRE"
DASH_SECTION_SPEED = "VITESSE"
DASH_SECTION_EXPL  = "EXPLICATION"

# ── Dashboard level selector ──────────────────────────────────────────────
DASH_LEVELS      = ["decouverte", "lycee", "avance"]
DASH_LEVEL_ICONS = ["🔍 Découverte", "📐 Secondaire", "∑ Avancé"]
DASH_GAUGE_UNIT  = "m/s"
DASH_FACT_TITLE  = "💡  Le savais-tu ?"

# ── Formula popup dialog ───────────────────────────────────────────────────
FORMULA_POPUP_TITLE  = "Détail de la formule"
FORMULA_CLOSE_BTN    = "Fermer"

# ── Dashboard extra levels ─────────────────────────────────────────────────
DASH_LEVEL_EXTREME   = "extreme"
DASH_LEVEL_COMPARE   = "compare"
DASH_ICON_EXTREME    = "⚡ Extrêmes"
DASH_ICON_COMPARE    = "⇌ Comparaison"

# ── MD3 libre nav rail ────────────────────────────────────────────────────
MD3_NAV_LABELS   = ["MCU", "Cône", "Membrane", "ML", "Scénarios"]
MD3_NAV_ICONS    = ["◯", "△", "◻", "◈", "⊞"]   # Unicode shapes (monospace)
MD3_APP_TITLE    = "Simulations"

# ── MD3 sidebar section labels ────────────────────────────────────────────
MD3_SECTION_MODEL    = "MODÈLE"
MD3_SECTION_LIVE     = "EN DIRECT"
MD3_SECTION_EXPL     = "EXPLICATION"

# ── MD3 scenarios page ────────────────────────────────────────────────────
MD3_SCEN_TITLE       = "Scénarios"
MD3_SCEN_SUBTITLE    = "Explorez les simulations avec des conditions initiales préconfigurées."
MD3_SCEN_LAUNCH_BTN  = "Lancer"
MD3_SCEN_COMPARE_HDR = "Comparaison"
MD3_SCEN_COMPARE_SUB = "Placez deux simulations côte à côte pour les comparer."
MD3_SCEN_SIM_NAMES   = {
    "2d_mcu":      "2D MCU",
    "3d_cone":     "3D Cône",
    "3d_membrane": "3D Membrane",
    "ml":          "ML",
}

# ── Comparison widget ─────────────────────────────────────────────────────
MD3_CMP_LAUNCH_BTN   = "▶  Démarrer les deux"
MD3_CMP_STOP_BTN     = "⏸  Arrêter"
MD3_CMP_LOADING      = "Calcul en cours…"
MD3_CMP_SELECT_SIM   = "Simulation :"
MD3_CMP_SELECT_SCEN  = "Scénario :"
