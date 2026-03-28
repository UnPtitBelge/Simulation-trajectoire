"""Fenêtre principale — QTabWidget avec 5 onglets de simulation.

Chaque onglet = QSplitter(sim_widget | controls_panel).
La config est lue depuis les TOML via le dict `configs`.

Raccourcis clavier (actifs quelle que soit la fenêtre active) :
  [ / ]       — preset précédent / suivant (onglet actif)
  L           — algorithme Linéaire  (onglets ML uniquement)
  M           — algorithme MLP       (onglets ML uniquement)
  Ctrl+1/2/3  — contexte d'entraînement (onglet ML — Synthétique uniquement)
  P           — ajouter un marqueur (géré dans BaseSimWidget)
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QLabel, QMainWindow, QSplitter, QTabWidget, QWidget,
)

from ui.base_sim_widget import BaseSimWidget

from ui.controls import ControlsPanel
from ui.cone_widget import ConeWidget
from ui.membrane_widget import MembraneWidget
from ui.mcu_widget import MCUWidget
from ui.ml_widget import MLWidget


class MainWindow(QMainWindow):
    def __init__(self, configs: dict, real_models: dict, parent=None):
        """
        configs     : {"mcu": {...}, "cone": {...}, "membrane": {...}, "ml": {...}}
        real_models : {"linear": LinearStepModel, "mlp": MLPStepModel}
        """
        super().__init__(parent)
        self.setWindowTitle("Simulation de trajectoires")
        self.resize(1200, 750)
        self.statusBar().showMessage("Prêt")

        self._tabs = QTabWidget()
        self._tab_controls: list[ControlsPanel] = []
        self._algo_combos:  dict[int, QComboBox] = {}  # tab_index → QComboBox algo
        self._ctx_combos:   dict[int, QComboBox] = {}  # tab_index → QComboBox contexte

        for cfg_key, WidgetClass, label in [
            ("mcu",      MCUWidget,      "MCU"),
            ("cone",     ConeWidget,     "Cône"),
            ("membrane", MembraneWidget, "Membrane"),
        ]:
            widget = WidgetClass(configs[cfg_key])
            widget.error_occurred.connect(self._show_error)
            tab, controls = self._make_tab(widget, configs[cfg_key])
            self._tab_controls.append(controls)
            self._tabs.addTab(tab, label)

        for mode, models, label in [
            ("real",  real_models, "ML — Réel"),
            ("synth", None,        "ML — Synthétique"),
        ]:
            ml_widget = MLWidget(configs["ml"], mode=mode, models=models)
            ml_widget.error_occurred.connect(self._show_error)
            tab_idx = self._tabs.count()
            tab, controls, algo_combo, ctx_combo = self._make_ml_tab(
                ml_widget, configs["ml"]
            )
            self._tab_controls.append(controls)
            self._algo_combos[tab_idx] = algo_combo
            if ctx_combo is not None:
                self._ctx_combos[tab_idx] = ctx_combo
            self._tabs.addTab(tab, label)

        self.setCentralWidget(self._tabs)
        self._setup_shortcuts()

    # ── Construction des onglets ───────────────────────────────────────────────

    def _make_tab(self, sim_widget, cfg: dict) -> tuple[QWidget, ControlsPanel]:
        """Assemble sim_widget + panneau de contrôle dans un QSplitter."""
        controls = ControlsPanel(cfg)
        controls.params_changed.connect(lambda p: sim_widget.setup(p))
        sim_widget.setup(controls.current_params())
        sim_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(sim_widget)
        splitter.addWidget(controls)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        return splitter, controls

    def _make_ml_tab(
        self, ml_widget: MLWidget, cfg: dict
    ) -> tuple[QWidget, ControlsPanel, QComboBox, QComboBox | None]:
        """Onglet ML avec sélecteurs algo/contexte supplémentaires."""
        controls = ControlsPanel(cfg)

        algo_combo = QComboBox()
        algo_combo.addItems(["linear", "mlp"])
        algo_combo.currentTextChanged.connect(ml_widget.set_algo)
        algo_combo.currentTextChanged.connect(
            lambda _: ml_widget.setup(controls.current_params())
        )
        controls.add_extra_widget("Algorithme  (L / M)", algo_combo)

        ctx_combo = None
        if ml_widget._mode == "synth":
            ctx_names = cfg.get("synth", {}).get("contexts", {}).get("names", ["100pct"])
            ctx_combo = QComboBox()
            ctx_combo.addItems(ctx_names)
            ctx_combo.currentTextChanged.connect(ml_widget.set_context)
            ctx_combo.currentTextChanged.connect(
                lambda _: ml_widget.setup(controls.current_params())
            )
            controls.add_extra_widget("Contexte  (Ctrl+1/2/3)", ctx_combo)

        status_label = QLabel("–")
        status_label.setWordWrap(True)
        controls.add_extra_widget("État", status_label)
        ml_widget.compute_done.connect(lambda: status_label.setText(ml_widget.get_status()))

        controls.params_changed.connect(lambda p: ml_widget.setup(p))
        ml_widget.setup(controls.current_params())
        ml_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(ml_widget)
        splitter.addWidget(controls)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        return splitter, controls, algo_combo, ctx_combo

    # ── Contrôle de lecture ───────────────────────────────────────────────────

    def _active_controls(self) -> ControlsPanel:
        return self._tab_controls[self._tabs.currentIndex()]

    def _active_sim_widget(self) -> BaseSimWidget | None:
        splitter = self._tabs.widget(self._tabs.currentIndex())
        if isinstance(splitter, QSplitter):
            w = splitter.widget(0)
            if isinstance(w, BaseSimWidget):
                return w
        return None

    def _toggle_play(self) -> None:
        w = self._active_sim_widget()
        if w:
            w.toggle()

    def _reset_sim(self) -> None:
        w = self._active_sim_widget()
        if w:
            w.reset()

    def _prev_preset(self) -> None:
        self._active_controls().cycle_preset(-1)

    def _next_preset(self) -> None:
        self._active_controls().cycle_preset(+1)

    def _algo_linear(self) -> None:
        idx = self._tabs.currentIndex()
        if idx in self._algo_combos:
            self._algo_combos[idx].setCurrentText("linear")

    def _algo_mlp(self) -> None:
        idx = self._tabs.currentIndex()
        if idx in self._algo_combos:
            self._algo_combos[idx].setCurrentText("mlp")

    def _set_context(self, n: int) -> None:
        idx = self._tabs.currentIndex()
        if idx in self._ctx_combos:
            combo = self._ctx_combos[idx]
            if n < combo.count():
                combo.setCurrentIndex(n)

    # ── Raccourcis clavier ────────────────────────────────────────────────────

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("["),        self, self._prev_preset)
        QShortcut(QKeySequence("]"),        self, self._next_preset)
        QShortcut(QKeySequence("Space"),    self, self._toggle_play)
        QShortcut(QKeySequence("R"),        self, self._reset_sim)
        QShortcut(QKeySequence("L"),        self, self._algo_linear)
        QShortcut(QKeySequence("M"),        self, self._algo_mlp)
        QShortcut(QKeySequence("Ctrl+1"),   self, lambda: self._set_context(0))
        QShortcut(QKeySequence("Ctrl+2"),   self, lambda: self._set_context(1))
        QShortcut(QKeySequence("Ctrl+3"),   self, lambda: self._set_context(2))

    # ── Feedback erreurs ──────────────────────────────────────────────────────

    def _show_error(self, msg: str) -> None:
        self.statusBar().showMessage(f"Erreur de calcul : {msg}", 5000)
