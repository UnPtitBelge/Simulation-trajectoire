"""Application entry point and main window.

Modes
-----
Normal (default)    Maximised window, all tabs.
``--presentation``  Fullscreen, tab bar hidden, keys 1–4 select and
                    auto-start each simulation.
``--libre``         Fullscreen with live info overlays on every simulation.
``--debug``         Verbose logging to file and console.

Tab layout
----------
1. 2D MCU         — uniform circular motion
2. 3D Cône        — Newton cone (constant slope, semi-implicit Euler)
3. 3D Membrane    — Laplace membrane (logarithmic surface, velocity-Verlet)
4. Machine Learning — linear regression trajectory demo
5. Vidéo          — real-world tracking video
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from utils.logger import get_log_path, setup_logging

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Libre mode navigation bar
# ---------------------------------------------------------------------------

class _LibreNavBar(QWidget):
    """Barre de navigation du mode libre : question + 4 boutons-onglets."""

    tab_selected = Signal(int)

    _LABELS = ["2D MCU", "3D Cône", "3D Membrane", "ML"]
    _COLORS = ["#06d6a0", "#ff6b35", "#118ab2", "#ef476f"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setObjectName("libreNavBar")
        self._btns: list[QPushButton] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)

        question = QLabel("Comment les ordinateurs simulent la réalité ?")
        question.setObjectName("libreNavTitle")
        layout.addWidget(question)
        layout.addStretch()

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        bc = QHBoxLayout(btn_container)
        bc.setContentsMargins(0, 0, 0, 0)
        bc.setSpacing(6)

        for i, (label, color) in enumerate(zip(self._LABELS, self._COLORS)):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, idx=i: self.tab_selected.emit(idx))
            self._btns.append(btn)
            bc.addWidget(btn)

        layout.addWidget(btn_container)
        self._refresh_styles(0)

    def set_active(self, idx: int) -> None:
        for btn in self._btns:
            btn.setChecked(False)
        if 0 <= idx < len(self._btns):
            self._btns[idx].setChecked(True)
        self._refresh_styles(idx)

    def _refresh_styles(self, active: int) -> None:
        for i, (btn, color) in enumerate(zip(self._btns, self._COLORS)):
            if btn.isChecked():
                btn.setStyleSheet(
                    f"QPushButton {{ background: {color}22; color: {color}; "
                    f"border: 1px solid {color}; border-radius: 6px; "
                    f"font-size: 11px; font-weight: 700; padding: 4px 14px; min-width: 0; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: #4f5472; "
                    f"border: 1px solid #232640; border-radius: 6px; "
                    f"font-size: 11px; padding: 4px 14px; min-width: 0; }}"
                    f"QPushButton:hover {{ color: {color}; border-color: {color}44; }}"
                )


# ---------------------------------------------------------------------------
# Lazy tab widget
# ---------------------------------------------------------------------------

class LazyTabWidget(QTabWidget):
    """QTabWidget that defers widget construction until a tab is first shown.

    Each tab is registered with a factory callable.  The factory is
    invoked once — on first activation — and its result replaces the
    placeholder widget.  This keeps startup fast even when some simulations
    require several seconds of computation.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._factories: dict[int, Callable[[], QWidget]] = {}
        self._swapping = False
        self.currentChanged.connect(self._on_tab_changed)

    def addLazyTab(self, factory: Callable[[], QWidget], label: str) -> None:
        """Register a tab factory.  The tab shows a blank placeholder until activated."""
        placeholder = QWidget()
        index = self.addTab(placeholder, label)
        self._factories[index] = factory
        log.debug("Lazy tab registered — index=%d label=%r", index, label)

    def _on_tab_changed(self, index: int) -> None:
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
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(
        self,
        presentation_mode: bool = False,
        libre_mode: bool = False,
    ) -> None:
        super().__init__()
        self.presentation_mode = presentation_mode
        self.libre_mode = libre_mode
        self.setWindowTitle("Models & Simulations")

        # Charger les configs de conditions initiales une seule fois.
        # En mode normal les deux restent None → les Plot utilisent leurs défauts.
        self._pconf = None
        self._lconf = None
        if presentation_mode:
            from utils import presentation_config
            self._pconf = presentation_config
            log.info("Presentation mode — config loaded from utils.presentation_config")
        elif libre_mode:
            from utils import libre_config
            self._lconf = libre_config
            log.info("Libre mode — config loaded from utils.libre_config")

        container = QWidget()
        self.setCentralWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        if presentation_mode or libre_mode:
            top_bar.setVisible(False)
        else:
            top_bar.setFixedHeight(38)

        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(14, 0, 8, 0)
        tb_layout.setSpacing(0)

        title_label = QLabel("⬡  Models & Simulations")
        title_label.setObjectName("topBarTitle")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
        title_label.setFont(title_font)
        tb_layout.addWidget(title_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb_layout.addWidget(spacer)

        close_btn = QPushButton("✕  Close")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(96, 28)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.clicked.connect(self._on_close_clicked)
        tb_layout.addWidget(close_btn)

        root.addWidget(top_bar)

        # ── Libre nav bar (libre mode only) ───────────────────────────────
        if libre_mode:
            self._libre_nav = _LibreNavBar()
            root.addWidget(self._libre_nav)

        # ── Tab widget ────────────────────────────────────────────────────
        self.tabs = LazyTabWidget()
        if presentation_mode:
            self.tabs.tabBar().hide()
            self.tabs.setStyleSheet("background-color: #000000;")
        elif libre_mode:
            self.tabs.tabBar().hide()

        lm = libre_mode  # shorthand for lambdas below
        self.tabs.addLazyTab(lambda: self._make_mcu(lm),      "2D MCU")
        self.tabs.addLazyTab(lambda: self._make_cone(lm),     "3D Cône")
        self.tabs.addLazyTab(lambda: self._make_membrane(lm), "3D Membrane")
        self.tabs.addLazyTab(lambda: self._make_ml(lm),       "Machine Learning")

        root.addWidget(self.tabs, stretch=1)

        if libre_mode:
            self._libre_nav.tab_selected.connect(self._switch_and_run)
            self.tabs.currentChanged.connect(self._libre_nav.set_active)

        # Build the first visible tab immediately.
        # Mode présentation : MCU en premier (le présentateur navigue avec 1-4).
        # Mode libre        : MCU en premier (auto-start intégré dans SimWidget).
        # Mode normal        : 3D Cône par défaut.
        if presentation_mode or libre_mode:
            self.tabs._on_tab_changed(0)
        else:
            self.tabs._on_tab_changed(1)

        log.info("MainWindow ready")

        if presentation_mode:
            self._setup_presentation_shortcuts()
        if libre_mode:
            self._setup_libre_shortcuts()

    # ── Presentation-mode keyboard shortcuts ─────────────────────────────

    def _setup_presentation_shortcuts(self) -> None:
        ctx = Qt.ShortcutContext.ApplicationShortcut
        for key, idx in [("1", 0), ("2", 1), ("3", 2), ("4", 3)]:
            QShortcut(QKeySequence(key), self, context=ctx).activated.connect(
                lambda i=idx: self._switch_and_run(i)
            )
        QShortcut(
            QKeySequence("Esc"), self, context=ctx
        ).activated.connect(self._on_close_clicked)

    def _setup_libre_shortcuts(self) -> None:
        ctx = Qt.ShortcutContext.ApplicationShortcut
        for key, idx in [("1", 0), ("2", 1), ("3", 2), ("4", 3)]:
            QShortcut(QKeySequence(key), self, context=ctx).activated.connect(
                lambda i=idx: self._switch_and_run(i)
            )
        QShortcut(
            QKeySequence("Esc"), self, context=ctx
        ).activated.connect(self._on_close_clicked)

    def _switch_and_run(self, index: int) -> None:
        """Pause current tab, switch, then start the new tab."""
        current = self.tabs.currentWidget()
        if current is not None and current is not self.tabs.widget(index):
            if hasattr(current, "plot") and hasattr(current.plot, "animation_timer"):
                if current.plot.animation_timer.isActive():
                    current.plot.stop_animation()
                    current.pause_button.setText("▶  Resume")

        self.tabs.setCurrentIndex(index)
        self.tabs._on_tab_changed(index)   # build if not yet built

        widget = self.tabs.currentWidget()
        if hasattr(widget, "reset_animation") and hasattr(widget, "start_animation"):
            widget.reset_animation()
            widget.start_animation()

    # ── Tab factory methods ───────────────────────────────────────────────

    def _params(self, key: str):
        """Retourne les paramètres scriptés selon le mode actif, ou None."""
        if self._pconf:
            return self._pconf.fresh(getattr(self._pconf, key.upper()))
        if self._lconf:
            return self._lconf.fresh(getattr(self._lconf, key.upper()))
        return None

    def _make_mcu(self, libre_mode: bool = False) -> QWidget:
        from simulations.sim2d.PlotMCU import PlotMCU
        from widgets.SimWidget import SimWidgetMCU
        return SimWidgetMCU(PlotMCU(self._params("mcu")), libre_mode=libre_mode)

    def _make_cone(self, libre_mode: bool = False) -> QWidget:
        from simulations.sim3d.PlotCone import PlotCone
        from widgets.SimWidget import SimWidget3d
        return SimWidget3d(PlotCone(self._params("cone")), libre_mode=libre_mode)

    def _make_membrane(self, libre_mode: bool = False) -> QWidget:
        from simulations.sim3d.PlotMembrane import PlotMembrane
        from widgets.SimWidget import SimWidget3d
        return SimWidget3d(PlotMembrane(self._params("membrane")), libre_mode=libre_mode)

    def _make_ml(self, libre_mode: bool = False) -> QWidget:
        from simulations.simML.PlotML import PlotML
        from widgets.SimWidget import SimWidgetML
        return SimWidgetML(PlotML(self._params("ml")), libre_mode=libre_mode)

    # ── Close ─────────────────────────────────────────────────────────────

    def _on_close_clicked(self) -> None:
        log.info("Close — quitting")
        QApplication.quit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def handle_interrupt(signum, frame) -> None:
    log.info("SIGINT received — shutting down")
    print("\nShutting down…")
    QApplication.quit()


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--debug",        action="store_true")
    parser.add_argument("--presentation", action="store_true")
    parser.add_argument("--libre",        action="store_true")
    args, remaining = parser.parse_known_args()

    setup_logging(debug=args.debug)
    log.info(
        "Starting — debug=%s presentation=%s libre=%s  log=%s",
        args.debug, args.presentation, args.libre, get_log_path(),
    )

    app = QApplication(remaining)

    from utils.stylesheet import APP_STYLESHEET
    app.setStyleSheet(APP_STYLESHEET)

    font = QFont("Inter", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    signal.signal(signal.SIGINT, handle_interrupt)

    window = MainWindow(
        presentation_mode=args.presentation,
        libre_mode=args.libre,
    )
    if args.presentation or args.libre:
        window.showFullScreen()
    else:
        window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
