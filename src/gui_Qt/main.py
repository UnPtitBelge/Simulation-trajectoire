import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
)
from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from widgets.SimWidget import SimWidget2d, SimWidget3d


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Models & Simulations")
        self.setGeometry(100, 100, 1920, 1080)

        # Main widgets
        tabs = QTabWidget()
        self.tab_2d = QWidget()
        self.tab_3d = QWidget()
        tabs.addTab(self.tab_2d, "2D Simulation")
        tabs.addTab(self.tab_3d, "3D Simulation")

        # Configure widgets
        self.setup_tabs(tabs)

        tabs.setCurrentWidget(self.tab_3d)

        self.setCentralWidget(tabs)

    def setup_tabs(self, tabs: QTabWidget):
        """Setup tabs widgets"""
        # Setup 2D tab
        self.plot_2d = SimWidget2d(Plot2d())
        self.tab_2d.setLayout(self.plot_2d.plot_layout)

        # Setup 3D tab
        self.sim_3d = SimWidget3d(Plot3d())
        self.tab_3d.setLayout(self.sim_3d.plot_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
