import argparse
import logging
import signal
import sys

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QTabWidget,
    QWidget,
)
from widgets.VideoPlayerWidget import VideoPlayerWidget

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args, remaining_argv = parser.parse_known_args()

logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class LazyTabWidget(QTabWidget):
    """QTabWidget that builds each tab's widget only the first time it is activated."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._factories: dict[int, callable] = {}
        self._swapping = False
        self.currentChanged.connect(self._on_tab_changed)

    def addLazyTab(self, factory: callable, label: str) -> None:
        """Register a tab with a factory instead of an already-built widget."""
        placeholder = QWidget()
        index = self.addTab(placeholder, label)
        self._factories[index] = factory

    def _on_tab_changed(self, index: int) -> None:
        """Instantiate the real widget the first time a tab is selected."""
        if self._swapping or index not in self._factories:
            return
        factory = self._factories.pop(index)
        label = self.tabText(index)
        real_widget = factory()

        self._swapping = True
        self.removeTab(index)
        self.insertTab(index, real_widget, label)
        self.setCurrentIndex(index)
        self._swapping = False

    def preload_all(self) -> None:
        """Build all pending tab factories immediately, keeping tab 0 visible.

        Iterates over every index that still has a pending factory, builds the
        real widget, swaps out the placeholder — without changing the currently
        visible tab (index 0 stays selected after all builds are done).
        """
        for index in sorted(self._factories.keys()):
            factory = self._factories.pop(index)
            label = self.tabText(index)
            real_widget = factory()

            self._swapping = True
            self.removeTab(index)
            self.insertTab(index, real_widget, label)
            self._swapping = False

        # Restore focus to tab 0 once all widgets are built
        self.setCurrentIndex(0)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Models & Simulations")

        container = QWidget()
        self.setCentralWidget(container)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.video_player = VideoPlayerWidget()
        layout.addWidget(self.video_player, stretch=1)

        self.sim_tab_widget = LazyTabWidget()
        self.sim_tab_widget.addLazyTab(self._make_2d, "2D Simulation")
        self.sim_tab_widget.addLazyTab(self._make_3d, "3D Simulation")
        self.sim_tab_widget.addLazyTab(self._make_ml, "ML Simulation")
        layout.addWidget(self.sim_tab_widget, stretch=1)

        # Build all three tabs upfront — no lazy deferral, no blank flash on switch
        self.sim_tab_widget.preload_all()

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


def handle_interrupt(signum, frame):
    print("\nShutting down application...")
    QApplication.quit()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Starting application (debug=%s)", getattr(args, "debug", False)
    )
    app = QApplication(remaining_argv)
    signal.signal(signal.SIGINT, handle_interrupt)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())
