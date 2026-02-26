import argparse
import logging
import signal
import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QTabWidget,
)
from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from simulations.simML.PlotML import PlotML
from widgets.SimWidget import SimWidget2d, SimWidget3d, SimWidgetML
from widgets.VideoPlayerWidget import VideoPlayerWidget

# Parse a minimal known-args subset so we can enable optional debug logging
# without consuming the rest of the argv intended for QApplication.
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args, remaining_argv = parser.parse_known_args()

# Configure logging globally; enable DEBUG when --debug is passed.
logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class MainWindow(QMainWindow):
    """Main application window that hosts the video player and simulation tabs.

    Layout:
      - Left: video player
      - Right: tab widget containing different simulations (2D, 3D, ML)

    The window opens in full-screen by default.
    """

    def __init__(self):
        """Initialize the main window UI and populate the widgets."""
        super().__init__()
        self.setWindowTitle("Models & Simulations")

        # Horizontal splitter separating the video area and simulation tabs
        splitter = QSplitter()

        # Video player on the left side of the splitter
        self.video_player = VideoPlayerWidget()
        splitter.addWidget(self.video_player)

        # Tab widget containing simulation views on the right side
        self.sim_tab_widget = QTabWidget()
        # 2D simulation tab
        self.sim_tab_widget.addTab(SimWidget2d(Plot2d()), "2D Simulation")
        # 3D simulation tab
        self.sim_tab_widget.addTab(SimWidget3d(Plot3d()), "3D Simulation")
        # Machine-learning simulation ta
        self.sim_tab_widget.addTab(SimWidgetML(PlotML()), "ML Simulation")

        splitter.addWidget(self.sim_tab_widget)

        # Make the splitter the central widget of the main window
        self.setCentralWidget(splitter)
        # Open full-screen for an immersive view
        self.showFullScreen()


def handle_interrupt(signum, frame):
    """Handle SIGINT (KeyboardInterrupt) by quitting the Qt application.

    This allows the program to be stopped cleanly with Ctrl+C from a terminal.
    """
    print("\nShutting down application...")
    QApplication.quit()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Starting application (debug=%s)", getattr(args, "debug", False)
    )

    # Pass the leftover args to QApplication (so Qt doesn't see the --debug flag)
    app = QApplication(remaining_argv)

    signal.signal(signal.SIGINT, handle_interrupt)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
