"""params_controller.py — Qt control panel generated from a simulation dataclass.

Two public classes:

* ``ParamControlWidget`` — a single row controlling one parameter field
  (QCheckBox for bool, _NoScrollSpinBox flanked by ± buttons for numeric).
* ``ParamsController``   — a two-column grid of ParamControlWidget rows,
  with a header, dividers, a Reset button, and 50 ms debounced forwarding
  of changes to the plot backend.

Usage
-----
    ctrl = ParamsController(plot.sim_params, type(plot.sim_params), plot)
    layout.addWidget(ctrl)
"""
import logging
from dataclasses import fields
from math import ceil, floor, log10

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from utils import stylesheet as _ss
from utils.ui_constants import (
    PC_CELL_MARGINS, PC_CELL_SPACING, PC_SPIN_SPACING,
    PC_HEADER_H, PC_HEADER_MARGINS, PC_HEADER_SPACING,
    PC_DIV_H, PC_GRID_MARGINS, PC_GRID_SPACING,
    PC_FOOTER_MARGINS, PC_DEBOUNCE_MS,
)
from utils.ui_strings import PC_RESET_BTN

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# _NoScrollSpinBox
# ---------------------------------------------------------------------------


class _NoScrollSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox that ignores wheel events so they bubble to the scroll area."""

    def wheelEvent(self, event: QWheelEvent) -> None:  # type: ignore[override]
        event.ignore()


# ---------------------------------------------------------------------------
# ParamControlWidget
# ---------------------------------------------------------------------------


class ParamControlWidget(QWidget):
    """Single-cell control for one parameter field (numeric or boolean).

    Uses a QCheckBox for bool fields and a _NoScrollSpinBox flanked by
    step buttons for numeric fields. Emits value_changed(name, value).
    """

    value_changed = Signal(str, object)

    def __init__(
        self,
        param_name: str,
        default_value,
        min_value=None,
        max_value=None,
        step=None,
        display_label: str | None = None,
    ) -> None:
        super().__init__()
        self.param_name = param_name
        self.default_value = default_value
        self.setStyleSheet(_ss.PARAM_CELL_STYLE)

        label_text = display_label if display_label else param_name.replace("_", " ").title()
        self.label = QLabel(label_text)
        self.label.setObjectName("cellLabel")
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        cell_layout = QVBoxLayout(self)
        cell_layout.setContentsMargins(*PC_CELL_MARGINS)
        cell_layout.setSpacing(PC_CELL_SPACING)
        cell_layout.addWidget(self.label)

        if isinstance(default_value, bool):
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(bool(default_value))
            self.checkbox.stateChanged.connect(self._checkbox_changed)
            cell_layout.addWidget(self.checkbox)

        else:
            self.spin_box = _NoScrollSpinBox()

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
                step = ParamsController._calculate_step(default_value, is_int=False)

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

            self.spin_box.setDecimals(
                ParamsController._calculate_decimals(
                    default_value, is_int=isinstance(default_value, int)
                )
            )
            self.spin_box.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            self.spin_box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.spin_box.valueChanged.connect(self.emit_value_changed)

            self.decrement_button = QPushButton("−")
            self.decrement_button.setObjectName("stepBtn")
            self.decrement_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.decrement_button.clicked.connect(self.spin_box.stepDown)

            self.increment_button = QPushButton("+")
            self.increment_button.setObjectName("stepBtn")
            self.increment_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.increment_button.clicked.connect(self.spin_box.stepUp)

            spin_row = QHBoxLayout()
            spin_row.setContentsMargins(0, 0, 0, 0)
            spin_row.setSpacing(PC_SPIN_SPACING)
            spin_row.addWidget(self.decrement_button)
            spin_row.addWidget(self.spin_box)
            spin_row.addWidget(self.increment_button)
            cell_layout.addLayout(spin_row)

    def _checkbox_changed(self, _state: int) -> None:
        """Emit value_changed with the new boolean state."""
        self.value_changed.emit(self.param_name, self.checkbox.isChecked())

    def emit_value_changed(self, value: float) -> None:
        """Emit value_changed with the current spinbox value."""
        self.value_changed.emit(self.param_name, value)

    def get_value(self):
        """Return the current value of this control (float or bool)."""
        if hasattr(self, "spin_box"):
            return self.spin_box.value()
        if hasattr(self, "checkbox"):
            return self.checkbox.isChecked()
        return None


# ---------------------------------------------------------------------------
# ParamsController
# ---------------------------------------------------------------------------


class ParamsController(QWidget):
    """Two-column control panel generated from a dataclass.

    Iterates over dataclasses.fields(params) and places one
    ParamControlWidget per field into a QGridLayout with two columns.
    Changes are written to params immediately and forwarded to
    plot.update_params(**changes) after a 50 ms debounce. A Reset button
    restores factory defaults and calls plot.update_params immediately.

    Field metadata keys used:
        label   Human-readable name (e.g. "Pente α")
        unit    Physical unit string (e.g. "m/s²", "°", "")
    """

    def __init__(self, params, param_type, plot=None) -> None:
        super().__init__()
        self.params = params
        self.param_type = param_type
        self.plot = plot

        log.debug(
            "ParamsController — initialising for %s (plot=%s)",
            param_type.__name__,
            type(plot).__name__ if plot is not None else "None",
        )

        self.default_params: object = param_type()
        self.param_controls: dict[str, ParamControlWidget] = {}

        self.setStyleSheet(_ss.PARAM_PANEL_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self._pending_updates: dict = {}
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(PC_DEBOUNCE_MS)
        self._debounce_timer.timeout.connect(self._flush_pending_update)

        root_vbox = QVBoxLayout(self)
        root_vbox.setContentsMargins(0, 0, 0, 0)
        root_vbox.setSpacing(0)

        # Header
        header_bar = QWidget()
        header_bar.setObjectName("headerBar")
        header_bar.setFixedHeight(PC_HEADER_H)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(*PC_HEADER_MARGINS)
        header_layout.setSpacing(PC_HEADER_SPACING)

        dot = QLabel("●")
        dot.setObjectName("headerDot")
        header_layout.addWidget(dot)

        title_text = param_type.__name__.replace("Simulation", "").replace("Params", " Params").strip()
        title = QLabel(title_text)
        title.setObjectName("headerTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        root_vbox.addWidget(header_bar)

        divider_top = QFrame()
        divider_top.setObjectName("divider")
        divider_top.setFrameShape(QFrame.Shape.HLine)
        divider_top.setFixedHeight(PC_DIV_H)
        root_vbox.addWidget(divider_top)

        # Grid
        grid_area = QWidget()
        grid_area.setObjectName("gridArea")
        grid = QGridLayout(grid_area)
        grid.setContentsMargins(*PC_GRID_MARGINS)
        grid.setSpacing(PC_GRID_SPACING)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for idx, f in enumerate(fields(self.params)):
            param_name = f.name
            default_value = getattr(self.params, param_name)
            row, col = divmod(idx, 2)

            # Build human-readable label with optional unit
            meta_label = f.metadata.get("label", param_name.replace("_", " ").title())
            meta_unit  = f.metadata.get("unit", "")
            display_label = f"{meta_label} ({meta_unit})" if meta_unit else meta_label

            if isinstance(default_value, bool):
                control = ParamControlWidget(param_name, default_value, display_label=display_label)
                log.debug(
                    "ParamsController — bool field: %s = %r", param_name, default_value
                )
            elif isinstance(default_value, (int, float)):
                is_int = isinstance(default_value, int)
                step = self._calculate_step(default_value, is_int=is_int)
                if default_value == 0:
                    min_value, max_value = -100.0, 100.0
                elif default_value > 0:
                    min_value = default_value * 0.1
                    max_value = default_value * 10.0
                else:
                    min_value = default_value * 10.0
                    max_value = default_value * 0.1
                control = ParamControlWidget(
                    param_name, default_value, min_value, max_value, step,
                    display_label=display_label,
                )
                log.debug(
                    "ParamsController — numeric field: %s = %r (step=%g, range=[%g, %g])",
                    param_name,
                    default_value,
                    step,
                    min_value,
                    max_value,
                )
            else:
                log.warning(
                    "ParamsController — unsupported field type for %r (%s); using fallback spinbox",
                    param_name,
                    type(default_value).__name__,
                )
                control = ParamControlWidget(param_name, 0.0, 0.0, 100.0, 1.0, display_label=display_label)

            control.setStyleSheet(control.styleSheet() + _ss.PARAM_CELL_OVERLAY)
            control.value_changed.connect(self.on_value_changed)
            self.param_controls[param_name] = control
            grid.addWidget(control, row, col)

        log.debug(
            "ParamsController — %d controls built for %s",
            len(self.param_controls),
            param_type.__name__,
        )

        root_vbox.addWidget(grid_area)

        divider_bot = QFrame()
        divider_bot.setObjectName("divider")
        divider_bot.setFrameShape(QFrame.Shape.HLine)
        divider_bot.setFixedHeight(PC_DIV_H)
        root_vbox.addWidget(divider_bot)

        # Footer
        footer = QWidget()
        footer.setObjectName("footerBar")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(*PC_FOOTER_MARGINS)
        footer_layout.addStretch()

        reset_button = QPushButton(PC_RESET_BTN)
        reset_button.setObjectName("resetBtn")
        reset_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        reset_button.clicked.connect(self._reset_to_default)
        footer_layout.addWidget(reset_button)

        root_vbox.addWidget(footer)

    @staticmethod
    def _calculate_step(value: float, is_int: bool = False) -> float:
        """Return a step size proportional to the order of magnitude of value."""
        abs_val = abs(value)
        if abs_val < 1e-12:
            return 1 if is_int else 0.01
        step = 10.0 ** (floor(log10(abs_val)) - 1)
        if is_int:
            return max(1, round(step))
        return step

    @staticmethod
    def _calculate_decimals(value: float, is_int: bool = False) -> int:
        """Return the number of decimal places needed to display value."""
        if is_int:
            return 0
        abs_val = abs(value)
        if abs_val < 1e-12:
            return 4
        step_exp = floor(log10(abs_val)) - 1
        decimals = max(1, ceil(-step_exp))
        return min(decimals, 10)

    def on_value_changed(self, param_name: str, value) -> None:
        log.debug(
            "ParamsController — field %r changed to %r (type=%s)",
            param_name,
            value,
            type(value).__name__,
        )
        setattr(self.params, param_name, value)
        if self.plot is not None:
            self._pending_updates[param_name] = value
            self._debounce_timer.start()

    def _flush_pending_update(self) -> None:
        if self.plot is not None and self._pending_updates:
            log.info(
                "ParamsController — flushing %d pending update(s) to %s: %s",
                len(self._pending_updates),
                type(self.plot).__name__,
                list(self._pending_updates.keys()),
            )
            self.plot.update_params(**self._pending_updates)
            self._pending_updates.clear()

    def _reset_to_default(self) -> None:
        log.info(
            "ParamsController — resetting %s to defaults", self.param_type.__name__
        )
        for f in fields(self.params):
            param_name = f.name
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
                f.name: getattr(self.default_params, f.name)
                for f in fields(self.params)
            }
            log.debug(
                "ParamsController — pushing %d default values to %s",
                len(all_defaults),
                type(self.plot).__name__,
            )
            self.plot.update_params(**all_defaults)
