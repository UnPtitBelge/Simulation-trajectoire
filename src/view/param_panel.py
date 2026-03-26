"""Collapsible parameter panel — toggled by Ctrl+P.

Reads PARAM_RANGES from the active simulation's params class to build
controls dynamically. Supports three control types:
  - Float sliders (default): continuous values with min/max/step
  - Discrete choices (type="discrete"): toggle buttons for enums
  - Boolean toggles (type="bool"): on/off checkboxes

Changes are debounced (300 ms) before triggering plot.setup().
"""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.utils.theme import (
    CLR_BG,
    CLR_BORDER,
    CLR_PRIMARY,
    CLR_PRIMARY_DARK,
    CLR_PRIMARY_LIGHT,
    CLR_TEXT_SECONDARY,
    CLR_WHITE,
    CLR_WHITE_FAINT,
    CLR_WHITE_HOVER,
    FS_LG,
    FS_MD,
    FS_SM,
    FS_XS,
    SLIDER_GROOVE_H,
    SLIDER_GROOVE_RADIUS,
    SLIDER_HANDLE_MARGIN,
    SLIDER_HANDLE_RADIUS,
    SLIDER_HANDLE_SIZE,
)

_DEBOUNCE_MS = 300
_PANEL_W = 310
_SLIDER_STEPS = 200


def _float_to_slider(val: float, spec: dict) -> int:
    lo, hi = spec["min"], spec["max"]
    if spec.get("scale") == "log" and lo > 0:
        return round((math.log(val) - math.log(lo)) / (math.log(hi) - math.log(lo)) * _SLIDER_STEPS)
    return round((val - lo) / (hi - lo) * _SLIDER_STEPS)


def _slider_to_float(pos: int, spec: dict) -> float:
    lo, hi = spec["min"], spec["max"]
    if spec.get("scale") == "log" and lo > 0:
        raw = math.exp(math.log(lo) + pos / _SLIDER_STEPS * (math.log(hi) - math.log(lo)))
    else:
        raw = lo + pos / _SLIDER_STEPS * (hi - lo)
    step = spec["step"]
    return round(round(raw / step) * step, 10)


class ParamPanel(QWidget):
    """Right-side overlay panel to live-edit simulation parameters."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._plot = None
        self._sliders: dict[str, QSlider] = {}
        self._val_labels: dict[str, QLabel] = {}
        self._discrete_groups: dict[str, QButtonGroup] = {}
        self._bool_checks: dict[str, QCheckBox] = {}

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._apply)

        self.setFixedWidth(_PANEL_W)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"ParamPanel {{ background: {CLR_BG}; border-left: 2px solid {CLR_BORDER}; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setVisible(False)

        self._build_skeleton()

    # ── public API ──────────────────────────────────────────────────────

    def toggle(self) -> None:
        self.setVisible(not self.isVisible())
        if self.isVisible():
            self.raise_()

    def update_plot(self, plot) -> None:
        if self._plot is not None:
            try:
                self._plot.setup_done.disconnect(self._on_setup_done)
            except RuntimeError:
                pass

        self._plot = plot
        if plot is not None:
            plot.setup_done.connect(self._on_setup_done)
            self._rebuild_controls()
            self._set_status_ready()

    # ── internal UI construction ─────────────────────────────────────────

    def _build_skeleton(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(f"background: {CLR_PRIMARY_DARK}; padding: 0;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(14, 10, 10, 10)

        self._title_lbl = QLabel("Paramètres")
        self._title_lbl.setStyleSheet(
            f"color: {CLR_WHITE}; font-size: {FS_LG}; font-weight: 500;"
        )
        h_lay.addWidget(self._title_lbl, stretch=1)

        hint = QLabel("Ctrl+P")
        hint.setStyleSheet(f"color: {CLR_WHITE_FAINT}; font-size: {FS_XS};")
        h_lay.addWidget(hint)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            f"QPushButton {{ color: {CLR_WHITE}; border: none; font-size: {FS_MD}; }}"
            f"QPushButton:hover {{ background: {CLR_WHITE_HOVER}; border-radius: 4px; }}"
        )
        close_btn.clicked.connect(self.hide)
        h_lay.addWidget(close_btn)

        root.addWidget(header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"background: {CLR_BG};")

        self._controls_widget = QWidget()
        self._controls_widget.setStyleSheet(f"background: {CLR_BG};")
        self._controls_layout = QVBoxLayout(self._controls_widget)
        self._controls_layout.setContentsMargins(14, 14, 14, 14)
        self._controls_layout.setSpacing(16)

        self._empty_lbl = QLabel("Aucune simulation active.")
        self._empty_lbl.setStyleSheet(f"color: {CLR_TEXT_SECONDARY}; font-size: {FS_SM};")
        self._controls_layout.addWidget(self._empty_lbl)
        self._controls_layout.addStretch()

        self._scroll.setWidget(self._controls_widget)
        root.addWidget(self._scroll, stretch=1)

        # Status bar
        status_bar = QFrame()
        status_bar.setStyleSheet(
            f"background: {CLR_PRIMARY_LIGHT}; border-top: 1px solid {CLR_BORDER};"
        )
        s_lay = QHBoxLayout(status_bar)
        s_lay.setContentsMargins(14, 6, 14, 6)

        self._status_lbl = QLabel("Prêt")
        self._status_lbl.setStyleSheet(f"color: {CLR_PRIMARY}; font-size: {FS_XS};")
        s_lay.addWidget(self._status_lbl)

        root.addWidget(status_bar)

    def _rebuild_controls(self) -> None:
        self._sliders.clear()
        self._val_labels.clear()
        self._discrete_groups.clear()
        self._bool_checks.clear()

        while self._controls_layout.count():
            item = self._controls_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if self._plot is None or self._plot.params is None:
            self._controls_layout.addWidget(self._empty_lbl)
            self._controls_layout.addStretch()
            return

        params = self._plot.params
        ranges = type(params).PARAM_RANGES

        if not ranges:
            lbl = QLabel("Aucun paramètre ajustable pour cette simulation.")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {CLR_TEXT_SECONDARY}; font-size: {FS_SM};")
            self._controls_layout.addWidget(lbl)
            self._controls_layout.addStretch()
            return

        for field_name, spec in ranges.items():
            current_val = getattr(params, field_name, None)
            param_type = spec.get("type", "float")

            if param_type == "discrete":
                row = self._make_discrete_row(field_name, spec, current_val)
            elif param_type == "bool":
                row = self._make_bool_row(field_name, spec, bool(current_val))
            else:
                row = self._make_slider_row(field_name, spec, float(current_val or spec["min"]))
            self._controls_layout.addWidget(row)

        self._controls_layout.addStretch()

    # ── control builders ──────────────────────────────────────────────────

    def _make_slider_row(self, field: str, spec: dict, value: float) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f"background: {CLR_BG};")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        lbl_row = QHBoxLayout()
        name_lbl = QLabel(spec["label"])
        name_lbl.setStyleSheet(f"font-size: {FS_SM}; font-weight: 500;")
        lbl_row.addWidget(name_lbl, stretch=1)

        val_lbl = QLabel(self._fmt(value, spec))
        val_lbl.setStyleSheet(
            f"font-size: {FS_SM}; color: {CLR_PRIMARY}; "
            f"font-family: monospace; font-weight: 500;"
        )
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_row.addWidget(val_lbl)
        lay.addLayout(lbl_row)

        range_hint = QLabel(f"{spec['min']} → {spec['max']}")
        range_hint.setStyleSheet(f"font-size: {FS_XS}; color: {CLR_TEXT_SECONDARY};")
        lay.addWidget(range_hint)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, _SLIDER_STEPS)
        slider.setValue(_float_to_slider(value, spec))
        slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ height: {SLIDER_GROOVE_H}; background: {CLR_BORDER}; border-radius: {SLIDER_GROOVE_RADIUS}; }}"
            f"QSlider::handle:horizontal {{ width: {SLIDER_HANDLE_SIZE}; height: {SLIDER_HANDLE_SIZE}; margin: {SLIDER_HANDLE_MARGIN}; "
            f"background: {CLR_PRIMARY}; border-radius: {SLIDER_HANDLE_RADIUS}; }}"
            f"QSlider::sub-page:horizontal {{ background: {CLR_PRIMARY}; border-radius: {SLIDER_GROOVE_RADIUS}; }}"
        )
        slider.valueChanged.connect(
            lambda pos, f=field, s=spec, lbl=val_lbl: self._on_slider(f, s, pos, lbl)
        )
        lay.addWidget(slider)

        self._sliders[field] = slider
        self._val_labels[field] = val_lbl

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {CLR_BORDER};")
        lay.addWidget(sep)

        return container

    def _make_discrete_row(self, field: str, spec: dict, current_val) -> QWidget:
        """Build a row of toggle buttons for discrete choices (e.g. integrator)."""
        container = QWidget()
        container.setStyleSheet(f"background: {CLR_BG};")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        name_lbl = QLabel(spec["label"])
        name_lbl.setStyleSheet(f"font-size: {FS_SM}; font-weight: 500;")
        lay.addWidget(name_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        group = QButtonGroup(container)
        group.setExclusive(True)

        choices = spec["choices"]
        labels = spec.get("choice_labels", [str(c) for c in choices])

        for idx, (choice, label) in enumerate(zip(choices, labels)):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(choice == current_val)
            btn.setFixedHeight(30)
            btn.setStyleSheet(
                f"QPushButton {{ background: {CLR_BORDER}; border: 1px solid {CLR_BORDER}; "
                f"border-radius: 4px; font-size: {FS_XS}; padding: 2px 8px; }}"
                f"QPushButton:checked {{ background: {CLR_PRIMARY}; color: white; border-color: {CLR_PRIMARY}; }}"
            )
            group.addButton(btn, idx)
            btn_row.addWidget(btn)

        lay.addLayout(btn_row)

        group.idToggled.connect(
            lambda idx, checked, f=field, c=choices: self._on_discrete(f, c, idx, checked)
        )
        self._discrete_groups[field] = group

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {CLR_BORDER};")
        lay.addWidget(sep)

        return container

    def _make_bool_row(self, field: str, spec: dict, value: bool) -> QWidget:
        """Build a checkbox toggle for boolean parameters."""
        container = QWidget()
        container.setStyleSheet(f"background: {CLR_BG};")
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 4, 0, 4)

        cb = QCheckBox(spec["label"])
        cb.setChecked(value)
        cb.setStyleSheet(f"font-size: {FS_SM}; font-weight: 500;")
        cb.toggled.connect(lambda checked, f=field: self._on_bool(f, checked))
        lay.addWidget(cb)

        self._bool_checks[field] = cb
        return container

    # ── slots ────────────────────────────────────────────────────────────

    def _on_slider(self, field: str, spec: dict, pos: int, val_lbl: QLabel) -> None:
        val = _slider_to_float(pos, spec)
        val_lbl.setText(self._fmt(val, spec))
        self._set_status("En attente…")
        self._debounce.start()

    def _on_discrete(self, field: str, choices: list, idx: int, checked: bool) -> None:
        if not checked:
            return
        self._set_status("En attente…")
        self._debounce.start()

    def _on_bool(self, field: str, checked: bool) -> None:
        self._set_status("En attente…")
        self._debounce.start()

    def _apply(self) -> None:
        if self._plot is None or self._plot.params is None:
            return
        params = self._plot.params
        ranges = type(params).PARAM_RANGES

        for field_name, spec in ranges.items():
            param_type = spec.get("type", "float")

            if param_type == "discrete" and field_name in self._discrete_groups:
                group = self._discrete_groups[field_name]
                idx = group.checkedId()
                if 0 <= idx < len(spec["choices"]):
                    setattr(params, field_name, spec["choices"][idx])

            elif param_type == "bool" and field_name in self._bool_checks:
                setattr(params, field_name, self._bool_checks[field_name].isChecked())

            elif field_name in self._sliders:
                new_val = _slider_to_float(self._sliders[field_name].value(), spec)
                setattr(params, field_name, new_val)

        self._set_status("Calcul en cours…")
        self._plot.setup()

    def _on_setup_done(self) -> None:
        self._set_status_ready()
        # Don't overwrite controls if the user has pending changes (debounce active)
        if not self._debounce.isActive():
            self._sync_from_params()

    def _sync_from_params(self) -> None:
        """Sync all controls to match current params (e.g. after preset change)."""
        if self._plot is None or self._plot.params is None:
            return
        params = self._plot.params
        ranges = type(params).PARAM_RANGES

        for field_name, spec in ranges.items():
            val = getattr(params, field_name, None)
            param_type = spec.get("type", "float")

            if param_type == "discrete" and field_name in self._discrete_groups:
                group = self._discrete_groups[field_name]
                choices = spec["choices"]
                for idx, choice in enumerate(choices):
                    if choice == val:
                        btn = group.button(idx)
                        if btn:
                            btn.blockSignals(True)
                            btn.setChecked(True)
                            btn.blockSignals(False)
                        break

            elif param_type == "bool" and field_name in self._bool_checks:
                cb = self._bool_checks[field_name]
                cb.blockSignals(True)
                cb.setChecked(bool(val))
                cb.blockSignals(False)

            elif field_name in self._sliders:
                self._sliders[field_name].blockSignals(True)
                self._sliders[field_name].setValue(_float_to_slider(float(val or spec["min"]), spec))
                self._sliders[field_name].blockSignals(False)
                if field_name in self._val_labels:
                    self._val_labels[field_name].setText(self._fmt(float(val or spec["min"]), spec))

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(val: float, spec: dict) -> str:
        step = spec["step"]
        decimals = max(0, -int(f"{step:e}".split("e")[1]))
        return f"{val:.{decimals}f}"

    def _set_status(self, text: str) -> None:
        self._status_lbl.setText(text)

    def _set_status_ready(self) -> None:
        self._status_lbl.setText("✓ Prêt")
        self._status_lbl.setStyleSheet(f"color: {CLR_PRIMARY_DARK}; font-size: {FS_XS};")
