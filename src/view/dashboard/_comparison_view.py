"""ComparisonView — comparaison côte-à-côte de deux simulations."""

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.content import SIM


class ComparisonView(QWidget):
    """Comparaison côte-à-côte de deux simulations."""

    def __init__(self, plots: list, keys: list[str], parent=None):
        super().__init__(parent)
        self._plots = plots
        self._keys = keys
        self._left = 0
        self._right = min(1, len(plots) - 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Comparaison de simulations")
        title.setProperty("role", "panel-title")
        layout.addWidget(title)

        sel = QHBoxLayout()
        self._lc = QComboBox()
        self._rc = QComboBox()
        for k in keys:
            label = SIM.get(k, {}).get("title", k)
            self._lc.addItem(label)
            self._rc.addItem(label)
        self._lc.setCurrentIndex(self._left)
        self._rc.setCurrentIndex(self._right)
        self._lc.currentIndexChanged.connect(self._set_left)
        self._rc.currentIndexChanged.connect(self._set_right)
        sel.addWidget(QLabel("Gauche :"))
        sel.addWidget(self._lc)
        sel.addStretch()
        sel.addWidget(QLabel("Droite :"))
        sel.addWidget(self._rc)
        layout.addLayout(sel)

        self._plot_row = QHBoxLayout()
        self._left_box = QVBoxLayout()
        self._right_box = QVBoxLayout()
        self._plot_row.addLayout(self._left_box, stretch=1)
        self._plot_row.addLayout(self._right_box, stretch=1)
        layout.addLayout(self._plot_row, stretch=1)

        btns = QHBoxLayout()
        for label, action in [("▶ Lecture", self._start), ("⏸ Pause", self._pause), ("↺ Reset", self._rst)]:
            b = QPushButton(label)
            if "Lecture" not in label:
                b.setProperty("secondary", True)
            b.clicked.connect(action)
            btns.addWidget(b)
        layout.addLayout(btns)

        self._refresh()

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def _refresh(self):
        self._clear(self._left_box)
        self._clear(self._right_box)
        if 0 <= self._left < len(self._plots):
            self._left_box.addWidget(self._plots[self._left].widget)
        if 0 <= self._right < len(self._plots):
            self._right_box.addWidget(self._plots[self._right].widget)

    def _set_left(self, i):
        self._left = i
        self._refresh()

    def _set_right(self, i):
        self._right = i
        self._refresh()

    def _for_both(self, fn):
        for idx in (self._left, self._right):
            if 0 <= idx < len(self._plots):
                fn(self._plots[idx])

    def _start(self):
        self._for_both(lambda p: p.start())

    def _pause(self):
        self._for_both(lambda p: p.stop())

    def _rst(self):
        self._for_both(lambda p: p.reset())
