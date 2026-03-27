"""Fenêtre principale — QTabWidget avec 5 onglets de simulation.

Chaque onglet = QSplitter(sim_widget | controls_panel).
La config est lue depuis les TOML via le dict `configs`.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QWidget

from ui.controls import ControlsPanel
from ui.cone_widget import ConeWidget
from ui.membrane_widget import MembraneWidget
from ui.mcu_widget import MCUWidget
from ui.ml_widget import MLWidget


def _make_tab(sim_widget, cfg: dict) -> QWidget:
    """Assemble sim_widget + panneau de contrôle dans un QSplitter."""
    controls = ControlsPanel(cfg)
    # Connexion : changement CI → relance la simulation
    controls.params_changed.connect(lambda p: sim_widget.setup(p))
    # Premier lancement avec le preset par défaut
    sim_widget.setup(controls.current_params())
    sim_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(sim_widget)
    splitter.addWidget(controls)
    splitter.setStretchFactor(0, 3)
    splitter.setStretchFactor(1, 1)
    return splitter


def _make_ml_tab(ml_widget: MLWidget, cfg: dict) -> QWidget:
    """Onglet ML avec sélecteurs algo/contexte supplémentaires."""
    from PySide6.QtWidgets import QComboBox

    controls = ControlsPanel(cfg)

    algo_combo = QComboBox()
    algo_combo.addItems(["linear", "mlp"])
    algo_combo.currentTextChanged.connect(ml_widget.set_algo)
    controls.add_extra_widget("Algorithme", algo_combo)

    if ml_widget._mode == "synth":
        ctx_names = cfg.get("synth", {}).get("contexts", {}).get("names", ["100pct"])
        ctx_combo = QComboBox()
        ctx_combo.addItems(ctx_names)
        ctx_combo.currentTextChanged.connect(ml_widget.set_context)
        controls.add_extra_widget("Contexte d'entraînement", ctx_combo)

    controls.params_changed.connect(lambda p: ml_widget.setup(p))
    ml_widget.setup(controls.current_params())
    ml_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(ml_widget)
    splitter.addWidget(controls)
    splitter.setStretchFactor(0, 3)
    splitter.setStretchFactor(1, 1)
    return splitter


class MainWindow(QMainWindow):
    def __init__(self, configs: dict, real_models: dict, parent=None):
        """
        configs     : {"mcu": {...}, "cone": {...}, "membrane": {...}, "ml": {...}}
        real_models : {"linear": LinearStepModel, "mlp": MLPStepModel}
        """
        super().__init__(parent)
        self.setWindowTitle("Simulation de trajectoires")
        self.resize(1200, 750)

        tabs = QTabWidget()
        tabs.addTab(_make_tab(MCUWidget(configs["mcu"]),           configs["mcu"]),      "MCU")
        tabs.addTab(_make_tab(ConeWidget(configs["cone"]),         configs["cone"]),     "Cône")
        tabs.addTab(_make_tab(MembraneWidget(configs["membrane"]), configs["membrane"]), "Membrane")
        tabs.addTab(
            _make_ml_tab(MLWidget(configs["ml"], mode="real",  models=real_models), configs["ml"]),
            "ML — Réel",
        )
        tabs.addTab(
            _make_ml_tab(MLWidget(configs["ml"], mode="synth"), configs["ml"]),
            "ML — Synthétique",
        )
        self.setCentralWidget(tabs)
