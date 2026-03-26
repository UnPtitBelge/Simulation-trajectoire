"""MainWindow — central widget with stacked views for all modes."""

from enum import IntEnum
from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.content import APP_TITLE, SIM
from src.content.chapters import CHAPTERS
from src.model.simulation import SIMULATIONS
from src.model.simulation.base import Plot3dBase
from src.util.theme import (
    CLR_HEADER_BG,
    CLR_HEADER_SUBTITLE,
    CLR_STATUS_TEXT,
    FS_LG,
    FS_SM,
    FS_XS,
)

from .dashboard import ComparisonView, SimDashboard, SimToRealView
from .components.menu import build_menu, make_card
from .param_panel import ParamPanel
from .presentation import GuardPage, TimelineBar
from .pages.theory import TheoryPage


class Page(IntEnum):
    """Indices of pages in the central QStackedWidget."""
    GUARD = 0
    MENU = 1
    DASHBOARD = 2
    THEORY = 3
    SIM_TO_REAL = 4


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self._allow_close = True
        self._sim_idx = 0
        self._key_filter = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Ensure main window maintains focus for keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        # Install focus change handler
        self.installEventFilter(self)

        self._pres_widget = self._build_guard_page()

        # Initialize UI components and simulations
        self._menu_widget, self._sim_grid = build_menu(
            on_open_comparison=self._open_comparison,
            on_open_theory=self._open_theory,
        )
        self._dash_stack = QStackedWidget()
        self._theory_page = TheoryPage(on_back=self.show_menu)
        self._sim_to_real_view: "SimToRealView | None" = None

        self.stack.addWidget(self._pres_widget)      # Page.GUARD
        self.stack.addWidget(self._menu_widget)      # Page.MENU
        self.stack.addWidget(self._dash_stack)       # Page.DASHBOARD
        self.stack.addWidget(self._theory_page)      # Page.THEORY
        # Page.SIM_TO_REAL : ajoutée plus tard en lazy init

        self.plots = []
        self.keys = []
        self.dashboards = []
        self._comparison = None

        for sim_key, _label, PlotCls, _in_pres in SIMULATIONS:
            plot = PlotCls()
            plot.setup()
            self.plots.append(plot)
            self.keys.append(sim_key)

            dash = SimDashboard(sim_key, plot, on_back=self.show_menu, parent=self)
            self.dashboards.append(dash)
            self._dash_stack.addWidget(dash)

        # Indices des simulations visibles en mode normal (navigation 1-4 / ←→)
        self._pres_indices: list[int] = [
            i for i, (*_, in_pres) in enumerate(SIMULATIONS) if in_pres
        ]

        self._populate_sim_cards()

        # Param panel — floating overlay on the right edge
        self._param_panel = ParamPanel(self)
        self._param_panel.raise_()

    def eventFilter(self, obj, event):
        """Ensure main window maintains focus for keyboard events."""
        # Handle focus events to keep keyboard responsiveness
        if event.type() == event.Type.FocusIn:
            self.setFocus()
            return True

        # Pass key events to the main window even if they come through widgets
        if event.type() == event.Type.KeyPress:
            # Let the main window handle key events first
            self.keyPressEvent(event)
            return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Handle key press events for global shortcuts."""
        # Handle window close shortcut first
        if event.key() == Qt.Key.Key_Escape and event.modifiers() == (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
        ):
            self._allow_close = True
            self.close()
            return

        if (
            event.key() == Qt.Key.Key_P
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.toggle_param_panel()
            return

        # If we have a key filter installed, let it handle the event
        if self._key_filter is not None:
            if self._key_filter.eventFilter(self, event):
                event.accept()
                return

        # Default handling
        super().keyPressEvent(event)

    # ── guard page view ────────────────────────────────────────

    def _build_guard_page(self) -> QWidget:
        """Build the guard page: welcome screen."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Guard page (full screen welcome)
        self._guard = GuardPage()
        self._guard.started.connect(self._guard_start)

        # Timeline bar
        self._timeline = TimelineBar()
        self._timeline.chapter_clicked.connect(self.pres_goto_chapter)
        self._timeline.hide()

        # Header (compact, shown during navigation)
        header = QWidget()
        header.setStyleSheet(f"background:{CLR_HEADER_BG}; padding:4px 16px;")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 4, 16, 4)

        self._pres_title = QLabel(APP_TITLE)
        self._pres_title.setStyleSheet(f"background:transparent; color:white; font-size:{FS_LG}; font-weight:500;")
        h.addWidget(self._pres_title)

        self._pres_subtitle = QLabel("")
        self._pres_subtitle.setStyleSheet(f"background:transparent; color:{CLR_HEADER_SUBTITLE}; font-size:{FS_SM}; font-style:italic;")
        h.addWidget(self._pres_subtitle, stretch=1)

        self._pres_status = QLabel("Prêt")
        self._pres_status.setStyleSheet(f"background:transparent; color:{CLR_STATUS_TEXT};")
        h.addWidget(self._pres_status)

        hint = QLabel("←→ · 1-4 · Espace · R · F1-3 · T · Ctrl+1-3 · Échap")
        hint.setStyleSheet(f"background:transparent; color:{CLR_STATUS_TEXT}; font-size:{FS_XS};")
        h.addWidget(hint)

        self._pres_header = header
        self._pres_header.hide()

        # Simulation host layout
        self._pres_host = QVBoxLayout()

        # Marker bar
        self._marker_bar = QWidget()
        self._marker_bar.setObjectName("markerBar")
        self._marker_bar.setStyleSheet(
            f"QWidget#markerBar {{ background: {CLR_HEADER_BG}; }}"
        )
        mbar = QHBoxLayout(self._marker_bar)
        mbar.setContentsMargins(16, 5, 16, 5)
        mbar.setSpacing(12)
        lbl = QLabel("Repères :")
        lbl.setStyleSheet(f"background: transparent; color: {CLR_STATUS_TEXT}; font-size: {FS_SM};")
        mbar.addWidget(lbl)
        self._marker_count_lbl = QLabel("0")
        self._marker_count_lbl.setStyleSheet(
            f"background: transparent; color: {CLR_HEADER_SUBTITLE}; font-size: {FS_SM}; font-weight: 500;"
        )
        mbar.addWidget(self._marker_count_lbl)
        mbar.addStretch()
        self._marker_add_btn = QPushButton("Ajouter [M]")
        self._marker_add_btn.clicked.connect(self._on_add_marker)
        mbar.addWidget(self._marker_add_btn)
        self._marker_clear_btn = QPushButton("Effacer tous [Suppr]")
        self._marker_clear_btn.setProperty("secondary", True)
        self._marker_clear_btn.clicked.connect(self._on_clear_markers)
        mbar.addWidget(self._marker_clear_btn)
        self._marker_bar.setVisible(False)

        # Assemble: guard + [header + timeline + sim area + markers]
        lay.addWidget(self._guard)
        lay.addWidget(self._pres_header)
        lay.addWidget(self._timeline)
        lay.addLayout(self._pres_host, stretch=1)
        lay.addWidget(self._marker_bar)

        # Chapter navigation state
        self._pres_ch_idx = 0
        self._pres_step_idx = 0

        return w

    def _populate_sim_cards(self):
        for i, key in enumerate(self.keys):
            info = SIM.get(key, {})
            c = make_card(
                info.get("title") or key,
                info.get("short") or "",
                lambda _, idx=i: self.open_dashboard(idx),
            )
            self._sim_grid.addWidget(c, i // 2, i % 2)

    # ── navigation ─────────────────────────────────────────────

    def show_menu(self):
        self.stack.setCurrentIndex(Page.MENU)

    def show_guard(self):
        self.stack.setCurrentIndex(Page.GUARD)

    def open_dashboard(self, idx: int):
        if 0 <= idx < len(self.dashboards):
            self._sim_idx = idx
            self._dash_stack.setCurrentIndex(idx)
            self.stack.setCurrentIndex(Page.DASHBOARD)
            self._param_panel.update_plot(self.plots[idx])

    def _open_theory(self):
        self.stack.setCurrentIndex(Page.THEORY)

    def _open_comparison(self):
        if self._comparison is None:
            self._comparison = ComparisonView(self.plots, self.keys, self)
            back = QPushButton("← Retour au menu")
            back.setProperty("flat", True)
            back.clicked.connect(self.show_menu)
            cast(QBoxLayout, self._comparison.layout()).insertWidget(0, back, alignment=Qt.AlignmentFlag.AlignLeft)
            self.stack.addWidget(self._comparison)
        self.stack.setCurrentWidget(self._comparison)

    def _open_sim_to_real(self):
        if self._sim_to_real_view is None:
            view = SimToRealView(on_back=self.show_menu, parent=self)
            self._sim_to_real_view = view
            self.stack.addWidget(view)
        if self._sim_to_real_view is not None:
            self.stack.setCurrentWidget(self._sim_to_real_view)

    # ── simulation control (used by modes) ─────────────────────

    def activate_sim(self, idx: int, auto_start: bool = False):
        if not (0 <= idx < len(self.plots)):
            return
        prev_idx = self._sim_idx
        self._sim_idx = idx

        # Only re-parent widgets if the simulation changed
        if prev_idx != idx or self._pres_host.count() == 0:
            while self._pres_host.count():
                item = self._pres_host.takeAt(0)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
            self._pres_host.addWidget(self.plots[idx].widget)
        self._param_panel.update_plot(self.plots[idx])
        info = SIM.get(self.keys[idx], {})
        self._pres_title.setText(f"{APP_TITLE} — {info.get('title', '')}")
        self._pres_subtitle.setText(info.get("short", ""))
        tagline = info.get("tagline", "")
        self.set_status(tagline if tagline else "Prêt")

        is_3d = isinstance(self.plots[idx], Plot3dBase)
        self._marker_bar.setVisible(is_3d)
        if is_3d:
            self._update_marker_count()

        self.show_guard()

        plot = self.plots[idx]
        if auto_start:
            if not plot._ready and not plot._computing:
                # First time showing this simulation — trigger computation.
                plot._start_after_setup = True
                plot.setup()
            else:
                plot.reset()
                plot.start()
            self.set_status("Lecture…")

    def next_sim(self):
        idxs = self._pres_indices
        if not idxs:
            return
        pos = idxs.index(self._sim_idx) if self._sim_idx in idxs else 0
        self.activate_sim(idxs[(pos + 1) % len(idxs)], auto_start=True)

    def prev_sim(self):
        idxs = self._pres_indices
        if not idxs:
            return
        pos = idxs.index(self._sim_idx) if self._sim_idx in idxs else 0
        self.activate_sim(idxs[(pos - 1) % len(idxs)], auto_start=True)

    def current_plot(self):
        if 0 <= self._sim_idx < len(self.plots):
            return self.plots[self._sim_idx]
        return None

    # ── chapter-based navigation ──────────────────────────────

    def _guard_start(self) -> None:
        """Called when user clicks 'Commencer' on the guard page."""
        self.show_menu()

    def show_guard(self) -> None:
        """Show the guard page."""
        # Stop current simulation
        p = self.current_plot()
        if p and p.timer.isActive():
            p.stop()

        self._guard.show()
        self._marker_bar.hide()

        # Hide sim widget from host
        while self._pres_host.count():
            item = self._pres_host.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        self.show_guard()
        self._guard.setFocus()

    def pres_goto_chapter(self, ch_idx: int, step_idx: int = 0) -> None:
        """Navigate to a specific chapter and step."""
        if not (0 <= ch_idx < len(CHAPTERS)):
            return
        self._pres_ch_idx = ch_idx
        self._pres_step_idx = step_idx
        self._pres_apply_step()

    def pres_next_step(self) -> None:
        """Advance to the next step, or next chapter if at the end."""
        ch = CHAPTERS[self._pres_ch_idx]
        if self._pres_step_idx + 1 < len(ch.steps):
            self._pres_step_idx += 1
        elif self._pres_ch_idx + 1 < len(CHAPTERS):
            self._pres_ch_idx += 1
            self._pres_step_idx = 0
        else:
            return  # at the very end
        self._pres_apply_step()

    def pres_prev_step(self) -> None:
        """Go back to the previous step, or previous chapter's last step."""
        if self._pres_step_idx > 0:
            self._pres_step_idx -= 1
        elif self._pres_ch_idx > 0:
            self._pres_ch_idx -= 1
            self._pres_step_idx = len(CHAPTERS[self._pres_ch_idx].steps) - 1
        else:
            return  # at the very beginning
        self._pres_apply_step()

    def _pres_apply_step(self) -> None:
        """Apply the current chapter/step — always a simulation."""
        ch = CHAPTERS[self._pres_ch_idx]
        if not ch.steps:
            return
        step = ch.steps[self._pres_step_idx]

        # Show navigation UI, hide guard
        self._guard.hide()
        self._pres_header.show()
        self._timeline.show()
        self._timeline.set_chapter(
            self._pres_ch_idx, self._pres_step_idx, len(ch.steps),
        )

        sim_key = step.sim_key
        idx = self._find_sim_idx(sim_key)
        if idx is not None:
            plot = self.plots[idx]
            # Apply preset before displaying — mutate params then restart()
            if step.preset:
                presets = type(plot.params).PRESETS
                if step.preset in presets:
                    plot.timer.stop()
                    plot.params = type(plot.params).from_preset(step.preset)
            # Show the simulation widget (restart() handles auto-start)
            self.activate_sim(idx, auto_start=False)
            plot.restart()
            self._pres_subtitle.setText(step.text)
        else:
            self.set_status(f"Simulation '{sim_key}' non trouvée")

        self.show_guard()

    def _find_sim_idx(self, sim_key: str | None) -> int | None:
        """Find the index of a simulation by its key."""
        if sim_key is None:
            return None
        for i, key in enumerate(self.keys):
            if key == sim_key:
                return i
        return None

    def apply_current_preset(self, preset_idx: int):
        p = self.current_plot()
        if not p:
            return
        cls = type(p.params)
        p.apply_preset(preset_idx)
        presets = cls.PRESETS
        keys = list(presets.keys())
        if 0 <= preset_idx < len(keys):
            self.set_status(f"Préréglage : {presets[keys[preset_idx]]['label']}")

    def set_status(self, text: str):
        self._pres_status.setText(text)

    # ── marker controls ───────────────────────────────────────

    def _on_add_marker(self) -> None:
        p = self.current_plot()
        if isinstance(p, Plot3dBase):
            pos = p.get_current_3d_pos()
            if pos is not None:
                p.add_marker(pos)
                self._update_marker_count()

    def _on_clear_markers(self) -> None:
        p = self.current_plot()
        if isinstance(p, Plot3dBase):
            p.clear_markers()
            self._update_marker_count()

    def _update_marker_count(self) -> None:
        p = self.current_plot()
        n = len(p._markers) if isinstance(p, Plot3dBase) else 0
        self._marker_count_lbl.setText(str(n))

    def add_pres_marker(self) -> None:
        self._on_add_marker()
        n = self._marker_count_lbl.text()
        self.set_status(f"Repère ajouté ({n})")

    def clear_pres_markers(self) -> None:
        self._on_clear_markers()
        self.set_status("Repères effacés")

    # ── window behavior ────────────────────────────────────────

    def toggle_param_panel(self) -> None:
        self._param_panel.toggle()
        self._reposition_param_panel()

    def _reposition_param_panel(self) -> None:
        """Keep panel flush against the right edge, full height."""
        pw = self._param_panel.width()
        self._param_panel.setGeometry(
            self.width() - pw, 0, pw, self.height()
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_param_panel()

    def force_close(self) -> None:
        """Allow the window to close and close it (used by key filters)."""
        self._allow_close = True
        self.close()

    def closeEvent(self, event):
        event.accept() if self._allow_close else event.ignore()
