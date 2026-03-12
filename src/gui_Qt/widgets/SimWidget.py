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
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)
from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from simulations.simML.PlotML import PlotML
from utils.params_controller import ParamsController
from utils.stylesheet import (
    HINT_BAR_STYLE,
    PANEL_STYLE,
    PAUSE_STYLE,
    PLAYBACK_BAR_STYLE,
    RESET_STYLE,
    SCROLL_AREA_STYLE,
    SEPARATOR_STYLE,
    START_STYLE,
)

log = logging.getLogger(__name__)


class _SimPrepareWorker(QThread):
    """Runs _prepare_simulation() off the main thread to keep the UI responsive."""

    done = Signal()

    def __init__(self, plot) -> None:
        super().__init__()
        self._plot = plot

    def run(self) -> None:
        self._plot._prepare_simulation()
        self.done.emit()


# Maximum height the control panel scroll-area is allowed to grow to.
# The panel will naturally be as tall as its contents up to this ceiling;
# a scrollbar appears only when contents overflow.
_PANEL_MAX_HEIGHT = 520


class SimWidget(QWidget):
    """Base widget hosting a plot and a collapsible control panel.

    Ctrl+P toggles the panel. The hint bar shows a ⚙ Controls button
    that does the same and disappears when the panel is open.

    Attributes:
        plot:                The plot backend instance.
        main_layout:         Root QVBoxLayout.
        controls_widget:     Panel container, hidden by default.
        controls_layout:     QVBoxLayout inside controls_widget.
        hint_bar:            Always-visible bar at the bottom of the plot.
        start_button:        Restarts the animation from frame 0.
        pause_button:        Pauses or resumes the timer.
        reset_button:        Rewinds to frame 0.
        _params_area_layout: Layout where subclasses add ParamsController widgets.
        _controls_scroll:    QScrollArea wrapping controls_widget; initialised to
                             None here and assigned by subclasses.
    """

    def __init__(self, plot: "Plot2d | Plot3d | PlotML") -> None:
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.plot = plot
        self._controls_scroll: QScrollArea | None = None
        log.debug("SimWidget.__init__ — plot type: %s", type(plot).__name__)

        # Use QStackedLayout(StackAll) so the GL/plot widget is ALWAYS painted
        # (its OpenGL context initialises immediately) while the loading overlay
        # sits on top until the worker thread finishes.
        self._plot_container = QWidget()
        _stack = QStackedLayout(self._plot_container)
        _stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        _stack.addWidget(self.plot.widget)  # layer 0 — always painted

        self._loading_widget = QWidget()
        self._loading_widget.setStyleSheet("background: rgba(20,20,20,210);")
        _llo = QVBoxLayout(self._loading_widget)
        self._loading_label = QLabel("Calcul en cours…")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _llo.addWidget(self._loading_label)
        _stack.addWidget(self._loading_widget)  # layer 1 — covers the plot

        self.main_layout.addWidget(self._plot_container, stretch=1)

        # Hint bar
        self.hint_bar = QWidget()
        self.hint_bar.setObjectName("hintBar")
        self.hint_bar.setFixedHeight(30)
        self.hint_bar.setStyleSheet(HINT_BAR_STYLE)

        hint_layout = QHBoxLayout(self.hint_bar)
        hint_layout.setContentsMargins(12, 0, 8, 0)
        hint_layout.setSpacing(8)

        hint_label = QLabel("Space  Pause   ·   Ctrl+R  Reset")
        hint_label.setObjectName("hintLabel")
        hint_layout.addWidget(hint_label)
        hint_layout.addStretch()

        self._hint_toggle_btn = QPushButton("⚙  Controls  (Ctrl+P)")
        self._hint_toggle_btn.setObjectName("hintToggleBtn")
        self._hint_toggle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._hint_toggle_btn.setFixedHeight(22)
        self._hint_toggle_btn.clicked.connect(self.toggle_controls)
        hint_layout.addWidget(self._hint_toggle_btn)

        self.main_layout.addWidget(self.hint_bar)

        # Controls panel
        self.controls_widget = QWidget()
        self.controls_widget.setObjectName("controlsWidget")
        self.controls_widget.setStyleSheet(PANEL_STYLE)

        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(0)

        # Playback row
        playback_bar = QWidget()
        playback_bar.setObjectName("playbackBar")
        playback_bar.setStyleSheet(PLAYBACK_BAR_STYLE)
        playback_bar.setFixedHeight(52)

        pb_layout = QHBoxLayout(playback_bar)
        pb_layout.setContentsMargins(14, 0, 14, 0)
        pb_layout.setSpacing(10)

        playback_title = QLabel("PLAYBACK")
        playback_title.setObjectName("playbackTitle")
        pb_layout.addWidget(playback_title)
        pb_layout.addStretch()

        self.start_button = QPushButton("▶  Start")
        self.start_button.setStyleSheet(START_STYLE)
        self.start_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.start_button.clicked.connect(self.start_animation)
        pb_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("⏸  Pause")
        self.pause_button.setStyleSheet(PAUSE_STYLE)
        self.pause_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.pause_button.clicked.connect(self.toggle_pause_animation)
        pb_layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("↺  Reset")
        self.reset_button.setStyleSheet(RESET_STYLE)
        self.reset_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.reset_button.clicked.connect(self.reset_animation)
        pb_layout.addWidget(self.reset_button)

        self.controls_layout.addWidget(playback_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setFixedHeight(1)
        sep.setStyleSheet(SEPARATOR_STYLE)
        self.controls_layout.addWidget(sep)

        self._params_area_layout = QVBoxLayout()
        self._params_area_layout.setSpacing(6)
        self._params_area_layout.setContentsMargins(10, 8, 10, 8)
        self.controls_layout.addLayout(self._params_area_layout)

        self.controls_widget.setVisible(False)
        self.setup_shortcuts()

        # Run the heavy simulation preparation off the main thread so the
        # Qt event loop (and OpenGL context init) stay alive.
        log.debug(
            "SimWidget — starting background prepare for %s", type(self.plot).__name__
        )
        self._worker = _SimPrepareWorker(self.plot)
        self._worker.done.connect(self._on_simulation_ready)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_simulation_ready(self) -> None:
        """Called on the main thread once _prepare_simulation() has finished."""
        self.plot._prepared = True
        self.plot.current_frame = 0
        log.info(
            "SimWidget — simulation ready for %s | n_frames=%d",
            type(self.plot).__name__,
            self.plot._n_frames,
        )
        self.plot._draw_initial_frame()
        self._loading_widget.setVisible(False)
        self._worker = None

    def setup_shortcuts(self) -> None:
        self.pause_shortcut = QShortcut(QKeySequence("Space"), self)
        self.pause_shortcut.activated.connect(self.toggle_pause_animation)

        self.reset_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.reset_shortcut.activated.connect(self.reset_animation)

        self.controls_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.controls_shortcut.activated.connect(self.toggle_controls)

    def toggle_controls(self) -> None:
        scroll = getattr(self, "_controls_scroll", None)
        target = scroll if scroll is not None else self.controls_widget

        if target.isHidden():
            log.debug("Controls panel shown (%s)", type(self.plot).__name__)
            target.setVisible(True)
            self._hint_toggle_btn.setVisible(False)
        else:
            log.debug("Controls panel hidden (%s)", type(self.plot).__name__)
            target.setVisible(False)
            self._hint_toggle_btn.setVisible(True)

    def start_animation(self) -> None:
        if not self.plot._prepared:
            log.debug("start_animation called before simulation ready — ignored")
            return
        log.info("Animation started — plot: %s", type(self.plot).__name__)
        self.plot.stop_animation()
        self.plot.start_animation()
        self.pause_button.setText("⏸  Pause")

    def toggle_pause_animation(self) -> None:
        if not self.plot._prepared:
            log.debug("toggle_pause_animation called before simulation ready — ignored")
            return
        if self.plot.animation_timer.isActive():
            log.info(
                "Animation paused — plot: %s | frame: %d",
                type(self.plot).__name__,
                self.plot.current_frame,
            )
            self.plot.stop_animation()
            self.pause_button.setText("▶  Resume")
        else:
            log.info(
                "Animation resumed — plot: %s | frame: %d",
                type(self.plot).__name__,
                self.plot.current_frame,
            )
            self.plot.start_animation()
            self.pause_button.setText("⏸  Pause")

    def reset_animation(self) -> None:
        if not self.plot._prepared:
            log.debug("reset_animation called before simulation ready — ignored")
            return
        log.info("Animation reset — plot: %s", type(self.plot).__name__)
        self.plot.reset_animation()
        self.pause_button.setText("⏸  Pause")


def _make_panel_scroll(controls_widget: QWidget) -> QScrollArea:
    """Wrap *controls_widget* in a styled scroll area for the panel."""
    scroll = QScrollArea()
    scroll.setWidget(controls_widget)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    # Let the panel grow with its contents up to _PANEL_MAX_HEIGHT.
    scroll.setMaximumHeight(_PANEL_MAX_HEIGHT)
    scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    scroll.setStyleSheet(SCROLL_AREA_STYLE)
    scroll.setVisible(False)
    return scroll


class SimWidget3d(SimWidget):
    """SimWidget for the 3-D surface simulation."""

    def __init__(self, plot: Plot3d) -> None:
        log.debug("SimWidget3d — initialising")
        super().__init__(plot)

        self.params_controller = ParamsController(
            plot.sim_params, type(plot.sim_params), plot
        )
        self._params_area_layout.addWidget(self.params_controller)

        self._controls_scroll = _make_panel_scroll(self.controls_widget)
        self.main_layout.addWidget(self._controls_scroll)
        log.debug("SimWidget3d — ready")


class SimWidget2d(SimWidget):
    """SimWidget for the 2-D orbital simulation."""

    def __init__(self, plot: Plot2d) -> None:
        log.debug("SimWidget2d — initialising")
        super().__init__(plot)

        self.params_controller = ParamsController(
            plot.sim_params, type(plot.sim_params), plot
        )
        self._params_area_layout.addWidget(self.params_controller)

        self._controls_scroll = _make_panel_scroll(self.controls_widget)
        self.main_layout.addWidget(self._controls_scroll)
        log.debug("SimWidget2d — ready")


class SimWidgetML(SimWidget):
    """SimWidget for the ML regression demo."""

    def __init__(self, plot: PlotML) -> None:
        log.debug("SimWidgetML — initialising")
        super().__init__(plot)

        self.params_controller = ParamsController(
            plot.sim_params, type(plot.sim_params), plot
        )
        self._params_area_layout.addWidget(self.params_controller)

        self._controls_scroll = _make_panel_scroll(self.controls_widget)
        self.main_layout.addWidget(self._controls_scroll)
        log.debug("SimWidgetML — ready")
