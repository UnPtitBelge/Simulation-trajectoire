from dataclasses import fields
from math import floor, log10

from PySide6.QtCore import QTimer, Signal
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
    """Single-row control for one parameter (numeric or boolean)."""

    value_changed = Signal(str, object)

    def __init__(
        self, param_name, default_value, min_value=None, max_value=None, step=None
    ):
        super().__init__()
        self.param_name = param_name
        self.default_value = default_value

        self.label = QLabel(param_name)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if isinstance(default_value, bool):
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(bool(default_value))
            self.checkbox.stateChanged.connect(self._checkbox_changed)
            control_layout = QHBoxLayout()
            control_layout.setContentsMargins(0, 0, 0, 0)
            control_layout.setSpacing(2)
            control_layout.addWidget(self.checkbox)
        else:
            self.spin_box = QDoubleSpinBox()
            if min_value is None:
                min_value = (
                    default_value - abs(default_value) - 10
                    if default_value != 0
                    else -100.0
                )
            if max_value is None:
                max_value = (
                    default_value + abs(default_value) + 10
                    if default_value != 0
                    else 100.0
                )
            if step is None:
                step = ParamControlWidget.calculate_default_step(default_value)
            try:
                self.spin_box.setRange(min_value, max_value)
                self.spin_box.setSingleStep(step)
            except Exception:
                self.spin_box.setRange(-1e9, 1e9)
                self.spin_box.setSingleStep(0.1)
            try:
                self.spin_box.setValue(float(default_value))
            except Exception:
                self.spin_box.setValue(0.0)
            self.spin_box.setDecimals(3)
            self.spin_box.setMaximumWidth(110)
            self.spin_box.valueChanged.connect(self.emit_value_changed)

            self.increment_button = QPushButton("+")
            self.increment_button.setFixedSize(20, 20)
            self.increment_button.clicked.connect(self.spin_box.stepUp)

            self.decrement_button = QPushButton("-")
            self.decrement_button.setFixedSize(20, 20)
            self.decrement_button.clicked.connect(self.spin_box.stepDown)

            control_layout = QHBoxLayout()
            control_layout.setContentsMargins(0, 0, 0, 0)
            control_layout.setSpacing(2)
            control_layout.addWidget(self.decrement_button)
            control_layout.addWidget(self.spin_box)
            control_layout.addWidget(self.increment_button)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        main_layout.addWidget(self.label)
        main_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)

    def _checkbox_changed(self, state):
        self.value_changed.emit(self.param_name, bool(state))

    def emit_value_changed(self, value):
        self.value_changed.emit(self.param_name, value)

    def get_value(self):
        if hasattr(self, "spin_box"):
            return self.spin_box.value()
        if hasattr(self, "checkbox"):
            return self.checkbox.isChecked()
        return None

    @staticmethod
    def calculate_default_step(default_value) -> float:
        """Fallback step used when ParamsController does not supply one."""
        return ParamsController._calculate_step(default_value, is_int=False)


class ParamsController(QWidget):
    """Generates UI controls from a dataclass and forwards changes to a plot."""

    def __init__(self, params, param_type, plot=None):
        super().__init__()
        self.params = params
        self.param_type = param_type
        self.plot = plot
        self.default_params = param_type()
        self.param_controls: dict = {}

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)

        self._pending_updates: dict = {}
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(50)
        self._debounce_timer.timeout.connect(self._flush_pending_update)

        for field in fields(self.params):
            param_name = field.name
            default_value = getattr(self.params, param_name)

            if isinstance(default_value, bool):
                control = ParamControlWidget(param_name, default_value)
            elif isinstance(default_value, (int, float)):
                is_int = isinstance(default_value, int)
                step = self._calculate_step(default_value, is_int=is_int)
                if default_value == 0:
                    min_value, max_value = -100.0, 100.0
                else:
                    min_value = default_value * 0.1
                    max_value = default_value * 10
                control = ParamControlWidget(
                    param_name, default_value, min_value, max_value, step
                )
            else:
                control = ParamControlWidget(param_name, 0.0, 0.0, 100.0, 1.0)

            control.value_changed.connect(self.on_value_changed)
            self.param_controls[param_name] = control
            self.main_layout.addWidget(control)

        reset_button = QPushButton("Reset")
        reset_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        reset_button.setFixedSize(60, 20)
        reset_button.clicked.connect(self._reset_to_default)
        self.main_layout.addWidget(reset_button)

    @staticmethod
    def _calculate_step(value: float, is_int: bool = False) -> float:
        """Return a step size proportional to the order of magnitude of `value`.

        Strategy:
          - The step is 1/100th of the value's order of magnitude, i.e.
            10^(floor(log10(|value|)) - 1). This gives exactly 100 steps
            to cross one order of magnitude, regardless of the scale.
          - For integer fields the step is always rounded up to the nearest
            integer ≥ 1, so int spinboxes always move by whole numbers.
          - Zero and very small values fall back to a safe default.

        Examples
        --------
        value=0.001  → magnitude 1e-3  → step 1e-4   (0.0001)
        value=0.05   → magnitude 1e-2  → step 1e-3   (0.001)
        value=0.3    → magnitude 1e-1  → step 1e-2   (0.01)
        value=0.8    → magnitude 1e-1  → step 1e-2   (0.01)
        value=9.81   → magnitude 1e1   → step 1e-1   (0.1)
        value=13.0   → magnitude 1e1   → step 1e-1   (0.1)   ← was 1.0
        value=45.0   → magnitude 1e1   → step 1e-1   (0.1)   ← was 1.0
        value=50.0   → magnitude 1e1   → step 1e-1   (0.1) → int→ 1
        value=800    → magnitude 1e2   → step 1e0    (1.0) → int→ 1
        value=1000.0 → magnitude 1e3   → step 1e1    (10)  → int→ 10
        """
        abs_val = abs(value)

        if abs_val < 1e-12:
            # Zero or effectively zero: safe fallback
            return 1 if is_int else 0.01

        # floor(log10(|v|)) gives the exponent of the leading digit.
        # Subtract 1 to get a step ~1% of the value's magnitude.
        exponent = floor(log10(abs_val)) - 1
        step = 10.0**exponent

        if is_int:
            # Integer fields always move by whole numbers (minimum 1)
            return max(1, round(step))

        return step

    def on_value_changed(self, param_name: str, value) -> None:
        """Accumulate changes and fire a single plot update after 50 ms of inactivity."""
        setattr(self.params, param_name, value)
        if self.plot is not None:
            self._pending_updates[param_name] = value
            self._debounce_timer.start()

    def _flush_pending_update(self) -> None:
        """Send all accumulated param changes to the plot in one single call."""
        if self.plot is not None and self._pending_updates:
            self.plot.update_params(**self._pending_updates)
            self._pending_updates.clear()

    def _reset_to_default(self) -> None:
        """Reset all params to defaults, update the UI and notify the plot immediately."""
        for field in fields(self.params):
            param_name = field.name
            default_value = getattr(self.default_params, param_name)
            setattr(self.params, param_name, default_value)

            control = self.param_controls.get(param_name)
            if control is None:
                continue
            if hasattr(control, "spin_box"):
                control.spin_box.blockSignals(True)
                try:
                    control.spin_box.setValue(float(default_value))
                finally:
                    control.spin_box.blockSignals(False)
            elif hasattr(control, "checkbox"):
                control.checkbox.blockSignals(True)
                try:
                    control.checkbox.setChecked(bool(default_value))
                finally:
                    control.checkbox.blockSignals(False)

        self._debounce_timer.stop()
        self._pending_updates.clear()
        if self.plot is not None:
            all_defaults = {
                field.name: getattr(self.default_params, field.name)
                for field in fields(self.params)
            }
            self.plot.update_params(**all_defaults)
