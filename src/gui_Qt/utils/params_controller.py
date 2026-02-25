from dataclasses import fields

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from utils.params import PlotParams, Simulation2dParams, Simulation3dParams


class ParamControl3dWidget(QWidget):
    def __init__(
        self,
        plot_params: PlotParams,
        sim_params: Simulation3dParams,
        plot: Plot3d,
    ):
        super().__init__()
        self.plot_params = plot_params
        self.sim_params = sim_params
        self.plot = plot
        self.default_plot_params = self.plot_params.__class__()
        self.default_sim_params = self.sim_params.__class__()
        self.value_labels = {}  # Dictionary to store value labels

        # Create group boxes for PlotParams and Simulation3dParams
        plot_group = QGroupBox("Plot Parameters")
        sim_group = QGroupBox("Simulation Parameters")

        # Layouts for each group
        plot_layout = QGridLayout()
        sim_layout = QGridLayout()

        # Add PlotParams controls
        self._add_param_control(plot_layout, "Surface Tension", "surface_tension", 0)
        self._add_param_control(plot_layout, "Surface Radius", "surface_radius", 1)
        self._add_param_control(plot_layout, "Center Radius", "center_radius", 2)
        self._add_param_control(plot_layout, "Center Weight", "center_weight", 3)

        # Add Simulation3dParams controls
        self._add_param_control(sim_layout, "Time Step", "time_step", 0, step=0.005)
        self._add_param_control(sim_layout, "Num Steps", "num_steps", 1, step=50)
        self._add_param_control(sim_layout, "Gravity", "g", 2, step=0.5)
        self._add_param_control(
            sim_layout, "Particle Radius", "particle_radius", 3, step=0.01
        )
        self._add_param_control(sim_layout, "Initial X", "x0", 4, step=0.05)
        self._add_param_control(sim_layout, "Initial Y", "y0", 5, step=0.01)
        self._add_param_control(sim_layout, "Initial Velocity", "v_i", 6, step=0.05)
        self._add_param_control(sim_layout, "Launch Angle", "theta", 7, step=5)
        self._add_param_control(
            sim_layout, "Friction Coef", "friction_coef", 8, step=0.05
        )

        # Add Reset to Default button
        reset_button = QPushButton("Reset to Default")
        reset_button.clicked.connect(self._reset_to_default)

        # Layout for the reset button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button)

        # Add parameter layouts and reset button layout to the group layouts
        plot_group_layout = QVBoxLayout()
        plot_group_layout.addLayout(plot_layout)
        plot_group.setLayout(plot_group_layout)

        sim_group_layout = QVBoxLayout()
        sim_group_layout.addLayout(sim_layout)
        sim_group.setLayout(sim_group_layout)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(plot_group)
        main_layout.addWidget(sim_group)
        main_layout.addLayout(reset_layout)

        self.setLayout(main_layout)

    def _add_param_control(self, layout, label, param_name, row, step=0.1):
        """Helper to add a parameter control (label, value label, decrement button, increment button)."""
        label_widget = QLabel(label)

        # Determine which parameter set to use
        param_set = (
            self.plot_params
            if hasattr(self.plot_params, param_name)
            else self.sim_params
        )

        # Create a label to display the current value
        value_label = QLabel(str(getattr(param_set, param_name)))
        self.value_labels[param_name] = value_label

        decrement_button = QPushButton("-")
        increment_button = QPushButton("+")

        decrement_button.clicked.connect(
            lambda _, p=param_name, s=step: self._update_param(p, -s)
        )
        increment_button.clicked.connect(
            lambda _, p=param_name, s=step: self._update_param(p, s)
        )

        layout.addWidget(label_widget, row, 0)
        layout.addWidget(value_label, row, 1)
        layout.addWidget(decrement_button, row, 2)
        layout.addWidget(increment_button, row, 3)

    def _update_param(self, param_name, delta):
        """Update the parameter, update the value label, and call update_params on the plot."""
        if hasattr(self.plot_params, param_name):
            param_set = self.plot_params
        elif hasattr(self.sim_params, param_name):
            param_set = self.sim_params
        else:
            return

        current_value = getattr(param_set, param_name)
        new_value = current_value + delta
        setattr(param_set, param_name, new_value)

        # Update the value label
        if param_name in self.value_labels:
            self.value_labels[param_name].setText(f"{new_value:.4g}")

        print(f"{param_name} updated to: {new_value}")

        if self.plot is not None:
            self.plot.update_params(**{param_name: new_value})

    def _reset_to_default(self):
        """Reset all parameters to their default values."""
        for field in fields(self.plot_params):
            default_value = getattr(self.default_plot_params, field.name)
            setattr(self.plot_params, field.name, default_value)

            # Update the value label
            if field.name in self.value_labels:
                self.value_labels[field.name].setText(f"{default_value:.4g}")

            if self.plot is not None:
                self.plot.update_params(**{field.name: default_value})

        for field in fields(self.sim_params):
            default_value = getattr(self.default_sim_params, field.name)
            setattr(self.sim_params, field.name, default_value)

            # Update the value label
            if field.name in self.value_labels:
                self.value_labels[field.name].setText(f"{default_value:.4g}")

            if self.plot is not None:
                self.plot.update_params(**{field.name: default_value})

        print("All parameters reset to default values.")


class ParamControl2dWidget(QWidget):
    def __init__(
        self,
        sim_params: Simulation2dParams,
        plot: Plot2d,
    ):
        super().__init__()
        self.sim_params = sim_params
        self.plot = plot
        self.default_params = self.sim_params.__class__()  # Store default values
        self.value_labels = {}  # Dictionary to store value labels

        # Group box for 2D parameters
        group_box = QGroupBox("2D Simulation Parameters")
        main_layout = QVBoxLayout()

        # Layout for parameter controls
        param_layout = QGridLayout()

        # Add parameter controls
        self._add_param_control(param_layout, "Gravity (G)", "G", 0, step=0.5)
        self._add_param_control(param_layout, "Mass (M)", "M", 1, step=10.0)
        self._add_param_control(param_layout, "Center Radius (r0)", "r0", 2, step=1.0)
        self._add_param_control(
            param_layout, "Initial Velocity (v0)", "v0", 3, step=0.5
        )
        self._add_param_control(
            param_layout, "Launch Angle (theta_deg)", "theta_deg", 4, step=5.0
        )
        self._add_param_control(
            param_layout, "Damping (gamma)", "gamma", 5, step=0.0005
        )
        self._add_param_control(param_layout, "Trail Length", "trail", 6, step=5)
        self._add_param_control(
            param_layout, "Center Radius", "center_radius", 7, step=0.5
        )
        self._add_param_control(
            param_layout, "Particle Radius", "particle_radius", 8, step=0.1
        )
        self._add_param_control(
            param_layout, "Frame Interval (ms)", "frame_ms", 9, step=1
        )
        self._add_param_control(param_layout, "Time Step (dt)", "dt", 10, step=0.005)

        # Add Reset to Default button
        reset_button = QPushButton("Reset to Default")
        reset_button.clicked.connect(self._reset_to_default)

        # Layout for the reset button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button)

        # Add parameter layout and reset button layout to the main layout
        main_layout.addLayout(param_layout)
        main_layout.addLayout(reset_layout)

        group_box.setLayout(main_layout)

        # Set the main layout for the widget
        widget_layout = QVBoxLayout()
        widget_layout.addWidget(group_box)
        self.setLayout(widget_layout)

    def _add_param_control(self, layout, label, param_name, row, step):
        """Add a control for a parameter (label, value label, decrement button, increment button)."""
        label_widget = QLabel(label)

        # Create a label to display the current value
        current_value = getattr(self.sim_params, param_name)
        value_label = QLabel(f"{current_value:.4g}")
        self.value_labels[param_name] = value_label

        decrement_button = QPushButton("-")
        increment_button = QPushButton("+")

        decrement_button.clicked.connect(
            lambda _, p=param_name, s=step: self._update_param(p, -s)
        )
        increment_button.clicked.connect(
            lambda _, p=param_name, s=step: self._update_param(p, s)
        )

        layout.addWidget(label_widget, row, 0)
        layout.addWidget(value_label, row, 1)
        layout.addWidget(decrement_button, row, 2)
        layout.addWidget(increment_button, row, 3)

    def _update_param(self, param_name, delta):
        """Update the parameter value, update the value label, and call update_params on the plot."""
        if hasattr(self.sim_params, param_name):
            current_value = getattr(self.sim_params, param_name)
            new_value = current_value + delta
            setattr(self.sim_params, param_name, new_value)

            # Update the value label
            if param_name in self.value_labels:
                self.value_labels[param_name].setText(f"{new_value:.4g}")

            print(f"{param_name} updated to: {new_value}")

            if self.plot is not None:
                self.plot.update_params(**{param_name: new_value})

    def _reset_to_default(self):
        """Reset all parameters to their default values."""
        for field in fields(self.sim_params):
            default_value = getattr(self.default_params, field.name)
            setattr(self.sim_params, field.name, default_value)

            # Update the value label
            if field.name in self.value_labels:
                self.value_labels[field.name].setText(f"{default_value:.4g}")

            if self.plot is not None:
                self.plot.update_params(**{field.name: default_value})
        print("All parameters reset to default values.")
