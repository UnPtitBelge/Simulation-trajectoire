from dataclasses import fields

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class ParamControlWidget(QWidget):
    """Single-row control for a parameter (numeric or boolean).

    Emits `value_changed(name, value)` where value is either a numeric type
    (float) or a boolean. The widget adapts to the default_value type:
    - bool -> a QCheckBox is created
    - int/float -> a QDoubleSpinBox with small +/- buttons is used
    """

    value_changed = Signal(str, object)

    def __init__(
        self, param_name, default_value, min_value=None, max_value=None, step=None
    ):
        super().__init__()
        self.param_name = param_name
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

        # Label for the parameter name
        self.label = QLabel(param_name)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Choose control type based on parameter value type
        if isinstance(default_value, bool):
            # Boolean -> checkbox
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(bool(default_value))
            self.checkbox.stateChanged.connect(self._checkbox_changed)

            # Create a small horizontal layout that holds the checkbox as the control
            control_layout = QHBoxLayout()
            control_layout.setContentsMargins(0, 0, 0, 0)
            control_layout.setSpacing(2)
            control_layout.addWidget(self.checkbox)
        else:
            # Numeric -> spinbox with +/- buttons
            self.spin_box = QDoubleSpinBox()

            # If min/max not provided, choose reasonable defaults
            if self.min_value is None:
                # if default is zero, choose a symmetric range
                self.min_value = (
                    default_value - abs(default_value) - 10
                    if default_value != 0
                    else -100.0
                )
            if self.max_value is None:
                self.max_value = (
                    default_value + abs(default_value) + 10
                    if default_value != 0
                    else 100.0
                )
            if self.step is None:
                self.step = self.calculate_default_step(default_value)

            try:
                self.spin_box.setRange(self.min_value, self.max_value)
                self.spin_box.setSingleStep(self.step)
            except Exception:
                # Ensure the spin box is configured even if values are odd
                self.spin_box.setRange(-1e9, 1e9)
                self.spin_box.setSingleStep(0.1)

            # Initialize display value
            try:
                self.spin_box.setValue(float(default_value))
            except Exception:
                # fallback to zero if conversion fails
                self.spin_box.setValue(0.0)

            self.spin_box.setDecimals(3)
            self.spin_box.setMaximumWidth(110)
            self.spin_box.valueChanged.connect(self.emit_value_changed)

            # Small +/- buttons
            self.increment_button = QPushButton("+")
            self.increment_button.setFixedSize(20, 20)
            self.increment_button.clicked.connect(self.spin_box.stepUp)

            self.decrement_button = QPushButton("-")
            self.decrement_button.setFixedSize(20, 20)
            self.decrement_button.clicked.connect(self.spin_box.stepDown)

            # Layout for buttons + spinbox
            spin_box_layout = QHBoxLayout()
            spin_box_layout.setContentsMargins(0, 0, 0, 0)
            spin_box_layout.setSpacing(2)
            spin_box_layout.addWidget(self.decrement_button)
            spin_box_layout.addWidget(self.spin_box)
            spin_box_layout.addWidget(self.increment_button)

            control_layout = spin_box_layout

        # Main horizontal layout: label on the left, control on the right
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        main_layout.addWidget(self.label)

        # Expanding spacer to push control to the right
        main_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        # Add the chosen control layout
        main_layout.addLayout(control_layout)

        self.setLayout(main_layout)

    def _checkbox_changed(self, state):
        """Internal handler for checkbox state changes (int -> bool)."""
        # Qt uses 0/2 for unchecked/checked; convert to bool
        value = bool(state)
        self.value_changed.emit(self.param_name, value)

    def emit_value_changed(self, value):
        """Emit the generic value_changed signal for numeric spinbox updates."""
        self.value_changed.emit(self.param_name, value)

    def get_value(self):
        """Return the current control value (bool or numeric)."""
        if hasattr(self, "spin_box"):
            return self.spin_box.value()
        if hasattr(self, "checkbox"):
            return self.checkbox.isChecked()
        return None


class ParamsController(QWidget):
    """Controller that generates UI controls from a dataclass.

    For each field in the provided dataclass `params`, a ParamControlWidget is
    created. Changes are written back to `params` and forwarded to `plot.update_params`.
    """

    def __init__(self, params, param_type, plot=None):
        super().__init__()
        self.params = params
        self.param_type = param_type
        self.plot = plot
        self.default_params = param_type()
        self.param_controls = {}

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)  # No margins
        self.layout.setSpacing(2)  # Reduced spacing
        self.setLayout(self.layout)

        # Create a control for each dataclass field
        for field in fields(self.params):
            param_name = field.name
            default_value = getattr(self.params, param_name)

            # Handle boolean parameters with a checkbox control
            if isinstance(default_value, bool):
                control = ParamControlWidget(
                    param_name, default_value, None, None, None
                )
            # Numeric parameters (int/float) -> use spinbox with calculated step
            elif isinstance(default_value, (int, float)):
                step = self.calculate_step(default_value)
                # avoid zero-range when default_value is zero
                if default_value == 0:
                    min_value, max_value = -100.0, 100.0
                else:
                    min_value = default_value * 0.1
                    max_value = default_value * 10
                control = ParamControlWidget(
                    param_name, default_value, min_value, max_value, step
                )
            else:
                # Fallback: attempt to create a numeric control with a generic range
                control = ParamControlWidget(param_name, 0.0, 0.0, 100.0, 1.0)

            control.value_changed.connect(self.on_value_changed)
            self.param_controls[param_name] = control
            self.layout.addWidget(control)

        # Reset button
        reset_button = QPushButton("Reset")
        reset_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        reset_button.setFixedSize(60, 20)  # Fixed size for the reset button
        reset_button.clicked.connect(self._reset_to_default)
        self.layout.addWidget(reset_button)

    def calculate_step(self, default_value):
        """Return an appropriate spin step based on the magnitude of the default."""
        if default_value < 1:
            return 0.01
        elif default_value < 10:
            return 0.1
        elif default_value < 100:
            return 1
        else:
            return 10

    def on_value_changed(self, param_name, value):
        """Handle a parameter value change.

        Update the underlying dataclass and notify the attached plot (if any).
        """
        setattr(self.params, param_name, value)
        if self.plot is not None:
            self.plot.update_params(**{param_name: value})

    def _reset_to_default(self):
        """Reset all parameters to their default values and update the UI.

        The underlying dataclass is restored to its default instance and the
        plot is notified of the reset values.
        """

        def _reset_to_default(self):
            """Reset all parameters to their dataclass defaults and update the UI and plot."""
            for field in fields(self.params):
                param_name = field.name
                default_value = getattr(self.default_params, param_name)
                setattr(self.params, param_name, default_value)

                control = self.param_controls.get(param_name)
                if control is None:
                    continue

                # Update control UI depending on control type
                if hasattr(control, "spin_box"):
                    try:
                        control.spin_box.setValue(float(default_value))
                    except Exception:
                        # ignore if conversion fails
                        pass
                elif hasattr(control, "checkbox"):
                    try:
                        control.checkbox.setChecked(bool(default_value))
                    except Exception:
                        pass

                # Notify the plot of the reset value if available
                if self.plot is not None:
                    try:
                        self.plot.update_params(**{param_name: default_value})
                    except Exception:
                        pass
