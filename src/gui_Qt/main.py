import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSizePolicy,
    QSplitter,
    QTabWidget,
)

from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from widgets.SimWidget import SimWidget2d, SimWidget3d
from widgets.VideoPlayerWidget import VideoPlayerWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Models & Simulations")

        # Create the splitter
        splitter = QSplitter()

        # Create and add the video player widget
        self.video_player = VideoPlayerWidget()
        splitter.addWidget(self.video_player)

        # Create and add the simulation tab widget
        self.sim_tab_widget = QTabWidget()
        self.sim_tab_widget.addTab(SimWidget2d(Plot2d()), "2D Simulation")
        self.sim_tab_widget.addTab(SimWidget3d(Plot3d()), "3D Simulation")
        splitter.addWidget(self.sim_tab_widget)

        # Set the splitter as the central widget
        self.setCentralWidget(splitter)

        # Set initial sizes to 50/50
        splitter.setSizes([self.width() // 3, 2 * self.width() // 3])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
