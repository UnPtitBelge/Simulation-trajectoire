import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
)

from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from widgets.SimWidget import SimWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Models & Simulations")
        self.setGeometry(100, 100, 800, 600)

        # Main widgets
        tabs = QTabWidget()
        self.tab_2d = QWidget()
        self.tab_3d = QWidget()
        tabs.addTab(self.tab_2d, "2D Simulation")
        tabs.addTab(self.tab_3d, "3D Simulation")

        # Configure widgets
        self.setup_tabs()

        tabs.setCurrentWidget(self.tab_3d)

        self.setCentralWidget(tabs)

    def setup_tabs(self):
        """Setup tabs widgets"""
        # Setup 2d tab
        self.plot_2d = SimWidget(Plot2d())
        self.tab_2d.setLayout(self.plot_2d.layout)

        # Initial 2D plot
        self.plot_2d.plot.redraw()

        # Setup 3d tab
        self.sim_3d = SimWidget(Plot3d())
        self.tab_3d.setLayout(self.sim_3d.layout)

        self.sim_3d.plot.redraw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
