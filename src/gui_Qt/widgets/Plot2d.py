import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class Plot2d:
    def __init__(self) -> None:
        self.layout = QVBoxLayout()

        # 2D plot zone with PyQtGraph
        self.plot_2d = pg.PlotWidget()
        self.plot_2d.setBackground("w")
        self.layout.addWidget(self.plot_2d)

        # Buttons & parameters
        params_layout = QHBoxLayout()
        self._param_x = QDoubleSpinBox()
        self._param_x.setRange(0, 10)
        self._param_x.setValue(1)
        params_layout.addWidget(QLabel("Parameter X:"))
        params_layout.addWidget(self._param_x)

        self.update_button = QPushButton("Update Simulation")
        self.update_button.clicked.connect(self.update)
        params_layout.addWidget(self.update_button)

        self.layout.addLayout(params_layout)

    def update(self):
        """Update the 2D plot."""
        x = np.linspace(0, 10, 100)
        y = np.sin(x * self._param_x.value())
        self.plot_2d.clear()
        self.plot_2d.plot(x, y, pen="b")  # 'b' for blue line
        self.plot_2d.setTitle("2D Simulation")
