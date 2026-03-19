"""Simulation widget framework.

Provides the base SimWidget and three concrete subclasses that pair a
plot backend with a scrollable control panel and playback buttons.

Class hierarchy
---------------
SimWidget          — base: plot container, hint bar, playback buttons,
                     loading overlay, Ctrl+P / Space / Ctrl+R shortcuts.
├── SimWidget3d    — for Plot3dBase subclasses (cone, membrane).
├── SimWidgetMCU   — for PlotMCU (2-D circular motion).
└── SimWidgetML    — for PlotML (machine-learning demo).

Background preparation
-----------------------
Heavy simulation setup (``_prepare_simulation``) runs in a ``QThread``
so the Qt event loop stays alive while the OpenGL context initialises.
The loading overlay covers the plot until the thread completes.
"""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from simulations.sim2d.PlotMCU import PlotMCU
from simulations.sim3d.Plot3dBase import Plot3dBase
from simulations.simML.PlotML import PlotML
from utils.params_controller import ParamsController
from utils import stylesheet as _ss
from utils.ui_constants import (
    SIM_PANEL_MAX_H, SIM_HINT_H, SIM_HINT_BTN_H, SIM_HINT_MARGINS,
    SIM_HINT_SPACING, SIM_PLAYBACK_H, SIM_PLAYBACK_MARGINS, SIM_PLAYBACK_SPACING,
    SIM_SEP_H, SIM_PARAMS_MARGINS, SIM_PARAMS_SPACING, SIM_LOADING_FS,
)
from utils.ui_strings import (
    LOADING_TEXT, HINT_TEXT, CONTROLS_BTN, PLAYBACK_TITLE,
    START_BTN, PAUSE_BTN, RESUME_BTN, RESET_BTN,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background worker thread
# ---------------------------------------------------------------------------

class _SimPrepareWorker(QThread):
    """Runs ``_prepare_simulation()`` off the main thread."""

    done = Signal()

    def __init__(self, plot) -> None:
        super().__init__()
        self._plot = plot

    def run(self) -> None:
        self._plot._prepare_simulation()
        self.done.emit()


# ---------------------------------------------------------------------------
# Scroll-area factory
# ---------------------------------------------------------------------------

def _make_panel_scroll(controls_widget: QWidget) -> QScrollArea:
    """Wrap *controls_widget* in a styled, bounded scroll area."""
    scroll = QScrollArea()
    scroll.setWidget(controls_widget)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setMaximumHeight(SIM_PANEL_MAX_H)
    scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    scroll.setStyleSheet(_ss.SCROLL_AREA_STYLE)
    scroll.setVisible(False)
    return scroll


# ---------------------------------------------------------------------------
# Base widget
# ---------------------------------------------------------------------------

class SimWidget(QWidget):
    """Base widget hosting a plot and a collapsible control panel.

    The plot is rendered in a QGridLayout so a semi-transparent loading
    overlay and the optional LiveInfoWidget can be stacked on top of it.

    Attributes
    ----------
    plot              The plot backend instance.
    main_layout       Root QVBoxLayout.
    controls_widget   Panel container (hidden by default).
    controls_layout   QVBoxLayout inside controls_widget.
    hint_bar          Always-visible bar below the plot (hidden in libre mode).
    start_button      Restarts the animation from frame 0.
    pause_button      Pauses or resumes the timer.
    reset_button      Rewinds to frame 0.
    _libre_dashboard  LibreDashboard panel (libre mode only, else None).
    _params_area_layout  QVBoxLayout where subclasses add ParamsController.
    _controls_scroll  QScrollArea wrapping controls_widget; set by subclasses.
    """

    def __init__(
        self,
        plot: "Plot3dBase | PlotMCU | PlotML",
        libre_mode: bool = False,
    ) -> None:
        super().__init__()
        self.libre_mode = libre_mode
        self.plot = plot
        self._controls_scroll: QScrollArea | None = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        log.debug("SimWidget.__init__ — plot: %s", type(plot).__name__)

        # ── Plot container (plot + loading overlay) ───────────────────────
        from PySide6.QtWidgets import QGridLayout
        self._plot_container = QWidget()
        grid = QGridLayout(self._plot_container)
        grid.setContentsMargins(0, 0, 0, 0)

        grid.addWidget(self.plot.widget, 0, 0)

        # Loading overlay — hidden once simulation is ready
        self._loading_widget = QWidget()
        self._loading_widget.setStyleSheet(f"background: {_ss.CLR_OVERLAY_BG};")
        _llo = QVBoxLayout(self._loading_widget)
        self._loading_label = QLabel(LOADING_TEXT)
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setStyleSheet(f"color: {_ss.CLR_TEXT}; font-size: {SIM_LOADING_FS}px;")
        _llo.addWidget(self._loading_label)
        grid.addWidget(self._loading_widget, 0, 0)

        # En mode libre : panneau latéral à droite, pas d'overlay
        self._libre_dashboard = None
        if self.libre_mode:
            from utils import libre_config
            from widgets.LibreDashboard import LibreInfoStrip
            self._libre_dashboard = LibreInfoStrip(
                sim_type=self.plot.SIM_TYPE,
                content=libre_config.CONTENT[self.plot.SIM_TYPE],
            )
            self.main_layout.addWidget(self._plot_container, stretch=1)
            self.main_layout.addWidget(self._libre_dashboard)
        else:
            self.main_layout.addWidget(self._plot_container, stretch=1)

        # ── Hint bar ──────────────────────────────────────────────────────
        self.hint_bar = QWidget()
        self.hint_bar.setObjectName("hintBar")
        self.hint_bar.setFixedHeight(SIM_HINT_H)
        self.hint_bar.setStyleSheet(_ss.HINT_BAR_STYLE)

        hint_layout = QHBoxLayout(self.hint_bar)
        hint_layout.setContentsMargins(*SIM_HINT_MARGINS)
        hint_layout.setSpacing(SIM_HINT_SPACING)

        hint_label = QLabel(HINT_TEXT)
        hint_label.setObjectName("hintLabel")
        hint_layout.addWidget(hint_label)
        hint_layout.addStretch()

        self._hint_toggle_btn = QPushButton(CONTROLS_BTN)
        self._hint_toggle_btn.setObjectName("hintToggleBtn")
        self._hint_toggle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._hint_toggle_btn.setFixedHeight(SIM_HINT_BTN_H)
        self._hint_toggle_btn.clicked.connect(self.toggle_controls)
        hint_layout.addWidget(self._hint_toggle_btn)

        # La barre d'indications est masquée en mode libre (le dashboard la remplace)
        if self.libre_mode:
            self.hint_bar.setVisible(False)
        self.main_layout.addWidget(self.hint_bar)

        # ── Control panel ─────────────────────────────────────────────────
        self.controls_widget = QWidget()
        self.controls_widget.setObjectName("controlsWidget")
        self.controls_widget.setStyleSheet(_ss.PANEL_STYLE)

        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(0)

        # Playback row
        playback_bar = QWidget()
        playback_bar.setObjectName("playbackBar")
        playback_bar.setStyleSheet(_ss.PLAYBACK_BAR_STYLE)
        playback_bar.setFixedHeight(SIM_PLAYBACK_H)

        pb_layout = QHBoxLayout(playback_bar)
        pb_layout.setContentsMargins(*SIM_PLAYBACK_MARGINS)
        pb_layout.setSpacing(SIM_PLAYBACK_SPACING)

        pb_title = QLabel(PLAYBACK_TITLE)
        pb_title.setObjectName("playbackTitle")
        pb_layout.addWidget(pb_title)
        pb_layout.addStretch()

        self.start_button = QPushButton(START_BTN)
        self.start_button.setStyleSheet(_ss.START_STYLE)
        self.start_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.start_button.clicked.connect(self.start_animation)
        pb_layout.addWidget(self.start_button)

        self.pause_button = QPushButton(PAUSE_BTN)
        self.pause_button.setStyleSheet(_ss.PAUSE_STYLE)
        self.pause_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pause_button.clicked.connect(self.toggle_pause_animation)
        pb_layout.addWidget(self.pause_button)

        self.reset_button = QPushButton(RESET_BTN)
        self.reset_button.setStyleSheet(_ss.RESET_STYLE)
        self.reset_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.reset_button.clicked.connect(self.reset_animation)
        pb_layout.addWidget(self.reset_button)

        self.controls_layout.addWidget(playback_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setFixedHeight(SIM_SEP_H)
        sep.setStyleSheet(_ss.SEPARATOR_STYLE)
        self.controls_layout.addWidget(sep)

        self._params_area_layout = QVBoxLayout()
        self._params_area_layout.setSpacing(SIM_PARAMS_SPACING)
        self._params_area_layout.setContentsMargins(*SIM_PARAMS_MARGINS)
        self.controls_layout.addLayout(self._params_area_layout)

        self.controls_widget.setVisible(False)
        self._setup_shortcuts()

        # ── Background simulation preparation ─────────────────────────────
        log.debug("SimWidget — launching background prepare for %s", type(plot).__name__)
        self._worker = _SimPrepareWorker(self.plot)
        self._worker.done.connect(self._on_simulation_ready)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_simulation_ready(self) -> None:
        """Called on the main thread once ``_prepare_simulation`` has finished."""
        self.plot._prepared = True
        self.plot.current_frame = 0
        log.info(
            "SimWidget — ready: %s  n_frames=%d",
            type(self.plot).__name__,
            self.plot._n_frames,
        )
        self.plot._draw_initial_frame()
        self._loading_widget.setVisible(False)
        self._worker = None
        # En mode libre, la simulation démarre automatiquement
        if self.libre_mode:
            self.start_animation()

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts: Space (pause), Ctrl+R (reset), Ctrl+P (controls)."""
        self.pause_shortcut    = QShortcut(QKeySequence("Space"),  self)
        self.reset_shortcut    = QShortcut(QKeySequence("Ctrl+R"), self)
        self.controls_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.pause_shortcut.activated.connect(self.toggle_pause_animation)
        self.reset_shortcut.activated.connect(self.reset_animation)
        self.controls_shortcut.activated.connect(self.toggle_controls)

    # ── Control panel toggle ──────────────────────────────────────────────

    def toggle_controls(self) -> None:
        """Show or hide the scrollable control panel."""
        target = self._controls_scroll if self._controls_scroll is not None \
                 else self.controls_widget
        if target.isHidden():
            target.setVisible(True)
            self._hint_toggle_btn.setVisible(False)
        else:
            target.setVisible(False)
            self._hint_toggle_btn.setVisible(True)

    # ── Playback actions ─────────────────────────────────────────────────

    def start_animation(self) -> None:
        if not self.plot._prepared:
            return
        self.plot.stop_animation()
        self.plot.start_animation()
        self.pause_button.setText(PAUSE_BTN)

    def toggle_pause_animation(self) -> None:
        if not self.plot._prepared:
            return
        if self.plot.animation_timer.isActive():
            self.plot.stop_animation()
            self.pause_button.setText(RESUME_BTN)
        else:
            self.plot.start_animation()
            self.pause_button.setText(PAUSE_BTN)

    def reset_animation(self) -> None:
        if not self.plot._prepared:
            return
        self.plot.reset_animation()
        self.pause_button.setText(PAUSE_BTN)


# ---------------------------------------------------------------------------
# Concrete subclasses
# ---------------------------------------------------------------------------

class SimWidget3d(SimWidget):
    """SimWidget for Plot3dBase subclasses (cone or membrane)."""

    def __init__(self, plot: Plot3dBase, libre_mode: bool = False) -> None:
        """Attach a 3-D plot backend and create the parameter controller."""
        log.debug("SimWidget3d — init")
        super().__init__(plot, libre_mode=libre_mode)

        self.params_controller = ParamsController(
            plot.sim_params, type(plot.sim_params), plot
        )
        self._params_area_layout.addWidget(self.params_controller)
        self._controls_scroll = _make_panel_scroll(self.controls_widget)
        self.main_layout.addWidget(self._controls_scroll)

        if self.libre_mode:
            self.plot.frame_updated.connect(self._on_frame_updated)

        log.debug("SimWidget3d — ready")

    def _on_frame_updated(self, idx: int) -> None:
        """Forward the current frame's position/velocity to the libre dashboard."""
        if not self.plot.trajectory_xs:
            return
        if idx >= len(self.plot.trajectory_xs) or not self.plot.trajectory_vxs:
            return
        self._libre_dashboard.update_data(
            x  = self.plot.trajectory_xs[idx],
            y  = self.plot.trajectory_ys[idx],
            vx = self.plot.trajectory_vxs[idx],
            vy = self.plot.trajectory_vys[idx],
            z  = self.plot.trajectory_zs[idx],
        )


class SimWidgetMCU(SimWidget):
    """SimWidget for the 2-D MCU circular motion simulation."""

    def __init__(self, plot: PlotMCU, libre_mode: bool = False) -> None:
        """Attach the MCU plot backend and create the parameter controller."""
        log.debug("SimWidgetMCU — init")
        super().__init__(plot, libre_mode=libre_mode)

        self.params_controller = ParamsController(
            plot.sim_params, type(plot.sim_params), plot
        )
        self._params_area_layout.addWidget(self.params_controller)
        self._controls_scroll = _make_panel_scroll(self.controls_widget)
        self.main_layout.addWidget(self._controls_scroll)

        if self.libre_mode:
            self.plot.frame_updated.connect(self._on_frame_updated)

        log.debug("SimWidgetMCU — ready")

    def _on_frame_updated(self, idx: int) -> None:
        """Forward the current frame's 2-D position/velocity to the libre dashboard."""
        if not self.plot.trajectory_xs:
            return
        if idx >= len(self.plot.trajectory_xs):
            return
        self._libre_dashboard.update_data(
            x  = self.plot.trajectory_xs[idx],
            y  = self.plot.trajectory_ys[idx],
            vx = self.plot.trajectory_vxs[idx],
            vy = self.plot.trajectory_vys[idx],
        )


class SimWidgetML(SimWidget):
    """SimWidget for the ML regression demo."""

    def __init__(self, plot: PlotML, libre_mode: bool = False) -> None:
        """Attach the ML plot backend and create the parameter controller."""
        log.debug("SimWidgetML — init")
        super().__init__(plot, libre_mode=libre_mode)

        self.params_controller = ParamsController(
            plot.sim_params, type(plot.sim_params), plot
        )
        self._params_area_layout.addWidget(self.params_controller)
        self._controls_scroll = _make_panel_scroll(self.controls_widget)
        self.main_layout.addWidget(self._controls_scroll)

        if self.libre_mode:
            self.plot.frame_updated.connect(self._on_frame_updated)

        log.debug("SimWidgetML — ready")

    def _on_frame_updated(self, idx: int) -> None:
        """Forward the predicted trajectory position/velocity to the libre dashboard.

        Velocity is estimated as a finite difference from the previous frame.
        """
        if self.plot._pred_traj.shape[0] == 0:
            return
        idx = min(idx, self.plot._pred_traj.shape[0] - 1)
        x, y = self.plot._pred_traj[idx]
        dt = self.plot.sim_params.frame_ms / 1000.0
        if idx > 0:
            prev_x, prev_y = self.plot._pred_traj[idx - 1]
            vx = (x - prev_x) / dt
            vy = (y - prev_y) / dt
        else:
            vx, vy = 0.0, 0.0
        self._libre_dashboard.update_data(x=x, y=y, vx=vx, vy=vy)
