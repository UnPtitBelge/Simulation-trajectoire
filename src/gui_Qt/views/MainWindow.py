from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
)

from layouts.Plot2d import Plot2d
from layouts.Plot3d import Plot3d


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
        self.plot_2d = Plot2d()
        self.tab_2d.setLayout(self.plot_2d.layout)

        # Initial plot
        self.plot_2d.update()

        # Setup 3d tab
        self.plot_3d = Plot3d()
        self.tab_3d.setLayout(self.plot_3d.layout)

        # Initial plot
        self.plot_3d.update()
