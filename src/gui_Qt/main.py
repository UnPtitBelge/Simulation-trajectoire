import argparse
import logging
import signal
import sys
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from utils.logger import get_log_path, setup_logging

log = logging.getLogger(__name__)


class LazyTabWidget(QTabWidget):
    """QTabWidget that defers widget construction until a tab is first shown."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._factories: dict[int, Callable[[], QWidget]] = {}
        self._swapping = False
        self.currentChanged.connect(self._on_tab_changed)

    def addLazyTab(self, factory: Callable[[], QWidget], label: str) -> None:
        placeholder = QWidget()
        index = self.addTab(placeholder, label)
        self._factories[index] = factory
        log.debug("Lazy tab registered — index=%d label=%r", index, label)

    def _on_tab_changed(self, index: int) -> None:
        if self._swapping or index not in self._factories:
            return

        label = self.tabText(index)
        log.info("Building tab on first activation — index=%d label=%r", index, label)

        factory = self._factories.pop(index)
        real_widget = factory()

        self._swapping = True
        self.removeTab(index)
        self.insertTab(index, real_widget, label)
        self.setCurrentIndex(index)
        self._swapping = False

    def preload_all(self) -> None:
        """Build all pending tabs immediately, keeping tab 0 selected."""
        for index in sorted(self._factories.keys()):
            label = self.tabText(index)
            factory = self._factories.pop(index)
            real_widget = factory()

            self._swapping = True
            self.removeTab(index)
            self.insertTab(index, real_widget, label)
            self._swapping = False

        self.setCurrentIndex(0)
        log.info("All tabs preloaded")


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self, presentation_mode: bool = False) -> None:
        super().__init__()
        self.presentation_mode = presentation_mode
        self.setWindowTitle("Models & Simulations")

        container = QWidget()
        self.setCentralWidget(container)

        root_layout = QVBoxLayout(container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top bar — styled entirely via APP_STYLESHEET (#topBar, #topBarTitle, #closeBtn)
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        if self.presentation_mode:
            top_bar.setVisible(False)
        else:
            top_bar.setFixedHeight(38)

        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(14, 0, 8, 0)
        top_bar_layout.setSpacing(0)

        title_label = QLabel("⬡  Models & Simulations")
        title_label.setObjectName("topBarTitle")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
        title_label.setFont(title_font)
        top_bar_layout.addWidget(title_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_bar_layout.addWidget(spacer)

        close_button = QPushButton("✕  Close")
        close_button.setObjectName("closeBtn")
        close_button.setFixedSize(96, 28)
        close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_button.clicked.connect(self._on_close_clicked)
        top_bar_layout.addWidget(close_button)

        root_layout.addWidget(top_bar)

        # Tab widget
        self.sim_tab_widget = LazyTabWidget()
        if self.presentation_mode:
            self.sim_tab_widget.tabBar().hide()
            self.sim_tab_widget.setStyleSheet("background-color: #000000;")
        self.sim_tab_widget.addLazyTab(self._make_2d, "2D Simulation")
        self.sim_tab_widget.addLazyTab(self._make_3d, "3D Simulation")
        self.sim_tab_widget.addLazyTab(self._make_ml, "ML Simulation")
        self.sim_tab_widget.addLazyTab(self._make_video, "Video Player")
        root_layout.addWidget(self.sim_tab_widget, stretch=1)

        if not self.presentation_mode:
            self.sim_tab_widget._on_tab_changed(1)
        else:
            # En mode présentation, on charge la vue 2D par défaut sans la lancer
            # pour éviter d'avoir un écran blanc vide au démarrage
            self.sim_tab_widget._on_tab_changed(0)

        log.info("MainWindow ready")

        if self.presentation_mode:
            self._setup_presentation_shortcuts()

    def _setup_presentation_shortcuts(self) -> None:
        QShortcut(QKeySequence("1"), self, context=Qt.ShortcutContext.ApplicationShortcut).activated.connect(lambda: self._switch_and_run(0))
        QShortcut(QKeySequence("2"), self, context=Qt.ShortcutContext.ApplicationShortcut).activated.connect(lambda: self._switch_and_run(1))
        QShortcut(QKeySequence("3"), self, context=Qt.ShortcutContext.ApplicationShortcut).activated.connect(lambda: self._switch_and_run(2))
        QShortcut(QKeySequence("4"), self, context=Qt.ShortcutContext.ApplicationShortcut).activated.connect(lambda: self._switch_and_run(3))
        QShortcut(QKeySequence("Esc"), self, context=Qt.ShortcutContext.ApplicationShortcut).activated.connect(self._on_close_clicked)

    def _switch_and_run(self, index: int) -> None:
        # Pause current view before switching
        current_idx = self.sim_tab_widget.currentIndex()
        if current_idx != -1 and current_idx != index:
            old_widget = self.sim_tab_widget.currentWidget()
            if old_widget:
                if hasattr(old_widget, "plot") and hasattr(old_widget.plot, "animation_timer"):
                    if old_widget.plot.animation_timer.isActive():
                        old_widget.plot.stop_animation()
                        old_widget.pause_button.setText("▶  Resume")
                elif hasattr(old_widget, "media_player"):
                    old_widget.media_player.pause()

        if self.sim_tab_widget.currentIndex() != index or getattr(self.sim_tab_widget, "_swapping", False):
            self.sim_tab_widget.setCurrentIndex(index)
        
        # Now force lazy tab to evaluate if it hasn't mapped yet
        self.sim_tab_widget._on_tab_changed(index)

        # Reset and start animation or video playback
        current_widget = self.sim_tab_widget.currentWidget()
        if hasattr(current_widget, "reset_animation") and hasattr(current_widget, "start_animation"):
            current_widget.reset_animation()
            current_widget.start_animation()
        elif hasattr(current_widget, "media_player"):
            current_widget.media_player.setPosition(0)
            current_widget.media_player.play()

    def _on_close_clicked(self) -> None:
        log.info("Close button clicked — quitting")
        QApplication.quit()

    @staticmethod
    def _make_2d() -> QWidget:
        from simulations.sim2d.Plot2d import Plot2d
        from widgets.SimWidget import SimWidget2d

        return SimWidget2d(Plot2d())

    @staticmethod
    def _make_3d() -> QWidget:
        from simulations.sim3d.Plot3d import Plot3d
        from widgets.SimWidget import SimWidget3d

        return SimWidget3d(Plot3d())

    @staticmethod
    def _make_ml() -> QWidget:
        from simulations.simML.PlotML import PlotML
        from widgets.SimWidget import SimWidgetML

        return SimWidgetML(PlotML())

    @staticmethod
    def _make_video() -> QWidget:
        from widgets.VideoPlayerWidget import VideoPlayerWidget

        return VideoPlayerWidget()


def handle_interrupt(signum, frame) -> None:
    log.info("SIGINT received — shutting down")
    print("\nShutting down application...")
    QApplication.quit()


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--presentation", action="store_true", help="Start in presentation mode (fullscreen, keys 1/2/3 auto-start views)")
    args, remaining_argv = parser.parse_known_args()

    setup_logging(debug=args.debug)

    log.info(
        "Application starting — debug=%s | presentation=%s | log file: %s", args.debug, args.presentation, get_log_path()
    )

    app = QApplication(remaining_argv)

    from utils.stylesheet import APP_STYLESHEET

    app.setStyleSheet(APP_STYLESHEET)

    default_font = QFont("Inter", 10)
    default_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(default_font)

    signal.signal(signal.SIGINT, handle_interrupt)

    window = MainWindow(presentation_mode=args.presentation)
    if args.presentation:
        window.showFullScreen()
        log.info("Window shown fullscreen — entering Qt event loop")
    else:
        window.showMaximized()
        log.info("Window shown maximized — entering Qt event loop")

    exit_code = app.exec()
    log.info("Qt event loop exited — exit code=%d", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
