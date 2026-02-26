from dataclasses import asdict

from pyqtgraph.Qt.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from simulations.simML.PlotML import PlotML
from utils.params import (
    PlotParams,
    Simulation2dParams,
    Simulation3dParams,
    SimulationMLParams,
)
from utils.params_controller import ParamsController


class SimWidget(QWidget):
    """Base widget hosting a plot and a collapsible control panel.

    The hosted `plot` object must expose `.widget` (a QWidget) and animation
    methods: `setup_animation`, `start_animation`, `stop_animation`, `reset_animation`,
    and an `animation_timer` QTimer.
    """

    def __init__(self, plot: Plot2d | Plot3d | PlotML) -> None:
        super().__init__()

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Plot widget (visualization area)
        self.plot = plot
        self.main_layout.addWidget(self.plot.widget)

        # Controls container (hidden by default)
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(5, 5, 5, 5)

        # Toggle button to show/hide controls
        self.toggle_button = QPushButton("Show Controls")
        self.toggle_button.clicked.connect(self.toggle_controls)
        self.main_layout.addWidget(self.toggle_button)

        # Layout for control buttons
        buttons_layout = QVBoxLayout()

        # Start button
        self.start_button = QPushButton("Start Animation")
        self.start_button.clicked.connect(self.start_animation)
        buttons_layout.addWidget(self.start_button)

        # Pause / Resume button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause_animation)
        buttons_layout.addWidget(self.pause_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_animation)
        buttons_layout.addWidget(self.reset_button)

        self.controls_layout.addLayout(buttons_layout)

        # Initialize the plot (no animation running)
        self.plot.setup_animation()

        # Hide controls by default
        self.controls_widget.setVisible(False)

        # Keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self) -> None:
        """Configure keyboard shortcuts used by the widget.

        Space: toggle pause/resume
        Ctrl+R: reset animation
        """

        # Use an explicit string-based QKeySequence to avoid static analysis issues
        self.pause_shortcut = QShortcut(QKeySequence("Space"), self)
        self.pause_shortcut.activated.connect(self.toggle_pause_animation)

        # Use the common Ctrl+R sequence string form
        self.reset_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.reset_shortcut.activated.connect(self.reset_animation)

    def toggle_controls(self) -> None:
        """Show or hide the control panel."""
        if self.controls_widget.isVisible():
            self.controls_widget.setVisible(False)
            self.toggle_button.setText("Show Controls")
        else:
            self.controls_widget.setVisible(True)
            self.toggle_button.setText("Hide Controls")

    def start_animation(self) -> None:
        """Restart and start the plot animation."""
        self.plot.stop_animation()
        self.plot.setup_animation()
        self.plot.start_animation()
        self.pause_button.setText("Pause")

    def toggle_pause_animation(self) -> None:
        """Toggle pause/resume of the animation timer."""
        if self.plot.animation_timer.isActive():
            self.plot.animation_timer.stop()
            self.pause_button.setText("Resume")
        else:
            self.plot.animation_timer.start()
            self.pause_button.setText("Pause")

    def reset_animation(self) -> None:
        """Reset the animation to its initial state."""
        self.plot.reset_animation()
        self.pause_button.setText("Pause")


class SimWidget3d(SimWidget):
    """SimWidget specialized for the 3D plot.

    Adds PlotParams and Simulation3dParams controls.
    """

    def __init__(self, plot: Plot3d) -> None:
        super().__init__(plot)

        self.plot_params = PlotParams()
        self.sim_params = Simulation3dParams()

        self.param_control = ParamsController(
            self.plot_params, Simulation3dParams, plot
        )
        self.sim_params_control = ParamsController(
            self.sim_params, Simulation3dParams, plot
        )

        self.controls_layout.addWidget(self.param_control)
        self.controls_layout.addWidget(self.sim_params_control)
        self.main_layout.addWidget(self.controls_widget)


class SimWidget2d(SimWidget):
    """SimWidget specialized for the 2D plot.

    Adds Simulation2dParams controls.
    """

    def __init__(self, plot: Plot2d) -> None:
        super().__init__(plot)

        self.sim_params = Simulation2dParams()

        self.param_control = ParamsController(self.sim_params, Simulation2dParams, plot)

        self.controls_layout.addWidget(self.param_control)
        self.main_layout.addWidget(self.controls_widget)


class SimWidgetML(SimWidget):
    """
    Wrapper for a machine-learning based plot (PlotML).
    This mirrors SimWidget2d/3d: it accepts a plot instance and registers a
    parameter control widget so it can be hosted as a tab in the main GUI.
    """

    def __init__(self, plot: PlotML) -> None:
        """
        Parameters
        ----------
        plot:
            An instance of the ML plotting wrapper (e.g. PlotML). The plot is
            expected to expose the same minimal interface as other plots used
            by SimWidget (a `.widget` attribute and animation controls).
        """
        super().__init__(plot)

        self.sim_params = SimulationMLParams()

        self.param_controller = ParamsController(
            self.sim_params, SimulationMLParams, plot
        )

        # # Initialize the plot with the current ML params so the view reflects defaults
        # # immediately (this will call PlotML.update_params with the dataclass fields).
        # try:
        #     # Use the asdict conversion to pass named parameters to update_params.
        #     self.plot.update_params(**asdict(self.sim_params))
        # except Exception:
        #     # If update fails for any reason, continue silently — the UI will still work.
        #     pass

        self.controls_layout.addWidget(self.param_controller)
        self.main_layout.addWidget(self.controls_widget)
