"""ScenarioHub — Single-page hub and lazy tab widget for simulation modes.

Contains two classes:

* ``LazyTabWidget`` — QTabWidget that defers widget construction until a tab
  is first activated, keeping startup fast.
* ``ScenarioHub`` — QStackedWidget-based hub for presentation/libre mode.
  Manages 4 simulation slots; switching does not affect an outer tab bar.
"""
from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LazyTabWidget
# ---------------------------------------------------------------------------

class LazyTabWidget(QTabWidget):
    """QTabWidget that defers widget construction until a tab is first shown.

    Each tab is registered with a factory callable.  The factory is
    invoked once — on first activation — and its result replaces the
    placeholder widget.  This keeps startup fast even when some simulations
    require several seconds of computation.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the lazy tab widget and connect the tab-change signal."""
        super().__init__(parent)
        self._factories: dict[int, Callable[[], QWidget]] = {}
        self._swapping = False
        self.currentChanged.connect(self._on_tab_changed)

    def addLazyTab(self, factory: Callable[[], QWidget], label: str) -> None:
        """Register a tab factory.  The tab shows a blank placeholder until activated.

        Parameters
        ----------
        factory : Callable[[], QWidget]
            Zero-argument callable that returns the real tab widget.
        label : str
            Tab bar label text.
        """
        placeholder = QWidget()
        index = self.addTab(placeholder, label)
        self._factories[index] = factory
        log.debug("Lazy tab registered — index=%d label=%r", index, label)

    def _on_tab_changed(self, index: int) -> None:
        """Build the real widget for *index* the first time the tab is activated."""
        if self._swapping or index not in self._factories:
            return
        label   = self.tabText(index)
        factory = self._factories.pop(index)
        log.info("Building tab — index=%d label=%r", index, label)
        widget  = factory()
        self._swapping = True
        self.removeTab(index)
        self.insertTab(index, widget, label)
        self.setCurrentIndex(index)
        self._swapping = False

    def preload_all(self) -> None:
        """Build all pending tabs immediately, keep tab 0 selected."""
        for index in sorted(self._factories.keys()):
            label   = self.tabText(index)
            factory = self._factories.pop(index)
            widget  = factory()
            self._swapping = True
            self.removeTab(index)
            self.insertTab(index, widget, label)
            self._swapping = False
        self.setCurrentIndex(0)
        log.info("All tabs preloaded")


# ---------------------------------------------------------------------------
# ScenarioHub
# ---------------------------------------------------------------------------

class ScenarioHub(QWidget):
    """Single-page hub for presentation/libre mode.

    Manages 4 simulation slots in an internal QStackedWidget.
    Switching scenarios does NOT change any outer tab — only the internal
    stack index.  Each slot is lazily built on first activation.

    Parameters
    ----------
    factories : list[Callable[[], QWidget]]
        One factory per slot.  Slot 0 is conventionally the landing page.
    parent : QWidget | None
        Optional parent widget.

    Signals
    -------
    slot_changed(int)
        Emitted after switching to a new slot, with the slot index.
    """

    slot_changed = Signal(int)

    def __init__(self, factories: list, parent: QWidget | None = None) -> None:
        """Build the stacked widget and register one placeholder per factory."""
        super().__init__(parent)
        self._factories = factories          # list[callable -> QWidget]
        self._built = [False] * len(factories)

        self._stack = QStackedWidget()
        for _ in factories:
            self._stack.addWidget(QWidget())  # placeholder

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._stack, stretch=1)

    def switch_to(self, idx: int) -> None:
        """Build (if needed) and show slot *idx*.

        If the slot has not been built yet, the registered factory is called
        once and its result replaces the placeholder.  After switching, if the
        new widget has ``reset_animation`` and ``start_animation`` methods,
        both are called in that order.

        Parameters
        ----------
        idx : int
            0-based slot index.
        """
        if not self._built[idx]:
            widget = self._factories[idx]()
            self._built[idx] = True
            # Replace placeholder
            old = self._stack.widget(idx)
            self._stack.removeWidget(old)
            old.deleteLater()
            self._stack.insertWidget(idx, widget)
        self._stack.setCurrentIndex(idx)
        self.slot_changed.emit(idx)
        # Auto-start: reset + start if simulation is ready
        w = self._stack.currentWidget()
        if hasattr(w, "reset_animation") and hasattr(w, "start_animation"):
            w.reset_animation()
            w.start_animation()

    def current_widget(self) -> QWidget:
        """Return the widget currently displayed in the stack."""
        return self._stack.currentWidget()

    def current_index(self) -> int:
        """Return the index of the currently displayed slot."""
        return self._stack.currentIndex()
