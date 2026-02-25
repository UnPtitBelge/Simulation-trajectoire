from pyqtgraph.Qt.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from utils.params import PlotParams, Simulation2dParams, Simulation3dParams
from utils.params_controller import ParamControl2dWidget, ParamControl3dWidget


class SimWidget(QWidget):
    def __init__(self, plot: Plot2d | Plot3d) -> None:
        super().__init__()
        self.plot_layout = QVBoxLayout()

        self.plot = plot
        self.plot_layout.addWidget(self.plot.widget)

        # Parameters layout
        self.params_layout = QHBoxLayout()

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Start button
        self.start_button = QPushButton("Start Animation")
        self.start_button.clicked.connect(self.start_animation)
        buttons_layout.addWidget(self.start_button)

        # Pause/Resume button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause_animation)
        buttons_layout.addWidget(self.pause_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_animation)
        buttons_layout.addWidget(self.reset_button)

        self.params_layout.addLayout(buttons_layout)

        # Initial plot (without animation)
        self.plot.setup_animation()

    def start_animation(self) -> None:
        """Start the animation."""
        self.plot.stop_animation()
        self.plot.setup_animation()
        self.plot.start_animation()
        self.pause_button.setText("Pause")

    def toggle_pause_animation(self) -> None:
        """Toggle between pausing and resuming the animation."""
        if self.plot.animation_timer.isActive():
            self.plot.animation_timer.stop()
            self.pause_button.setText("Resume")
        else:
            self.plot.animation_timer.start()
            self.pause_button.setText("Pause")

    def reset_animation(self) -> None:
        """Reset the animation to the start."""
        self.plot.reset_animation()
        self.pause_button.setText("Pause")


class SimWidget3d(SimWidget):
    def __init__(self, plot: Plot3d) -> None:
        super().__init__(plot)

        self.plot_params = PlotParams()
        self.sim_params = Simulation3dParams()

        self.param_control = ParamControl3dWidget(
            self.plot_params, self.sim_params, plot
        )

        self.params_layout.addWidget(self.param_control)
        self.plot_layout.addLayout(self.params_layout)

        self.setLayout(self.plot_layout)


class SimWidget2d(SimWidget):
    def __init__(self, plot: Plot2d) -> None:
        super().__init__(plot)

        # Initialize 2D simulation parameters
        sim_params = Simulation2dParams()

        # Create the parameter control widget for 2D
        self.param_control = ParamControl2dWidget(sim_params, plot)

        # Add the parameter control widget to the params layout
        self.params_layout.addWidget(self.param_control)

        # Set the main layout
        self.plot_layout.addLayout(self.params_layout)
        self.setLayout(self.plot_layout)
