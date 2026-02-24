import numpy as np
import pyqtgraph.opengl as gl
from pyqtgraph.Qt.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class Plot3d:
    def __init__(self) -> None:
        self.layout = QVBoxLayout()

        # 3D plot zone with PyQtGraph
        self.view_3d = gl.GLViewWidget()
        self.view_3d.setBackgroundColor("w")
        self.view_3d.setCameraPosition(distance=20, elevation=20, azimuth=20)
        self.layout.addWidget(self.view_3d)

        # Buttons & parameters
        params_layout = QHBoxLayout()
        self.param_y = QDoubleSpinBox()
        self.param_y.setRange(0, 10)
        self.param_y.setValue(1)
        params_layout.addWidget(QLabel("Parameter Y:"))
        params_layout.addWidget(self.param_y)

        self.update_button = QPushButton("Update Simulation")
        self.update_button.clicked.connect(self.update)
        params_layout.addWidget(self.update_button)

        self.layout.addLayout(params_layout)

    def update(self):
        """Update the 3D plot with a white curved surface."""
        # Clear old items (except the grid)
        for item in self.view_3d.items:
            self.view_3d.removeItem(item)

        # Generate data for a curved surface (e.g., sinusoidal or paraboloid)
        x = np.linspace(-5, 5, 100)
        y = np.linspace(-5, 5, 100)
        X, Y = np.meshgrid(x, y)
        # Example 1: Curved sinusoidal surface
        # Z = np.sin(np.sqrt(X**2 + Y**2) * self.param_y.value())
        # Example 2: Paraboloid (uncomment to try)
        Z = (X**2 + Y**2) * self.param_y.value()

        # Create a white 3D surface
        surface = gl.GLSurfacePlotItem(
            x=x,
            y=y,
            z=Z,
            color=(1, 1, 1, 1),  # White (RGBA: 1=255)
            shader="shaded",
            smooth=True,
        )
        self.view_3d.addItem(surface)
