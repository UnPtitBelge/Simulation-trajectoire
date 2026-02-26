from pyqtgraph.Qt.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from simulations.sim2d.Plot2d import Plot2d
from simulations.sim3d.Plot3d import Plot3d
from utils.params import PlotParams, Simulation2dParams, Simulation3dParams
from widgets.ParamsWidgets import ParamControl2dWidget, ParamControl3dWidget


class SimWidget(QWidget):
    def __init__(self, plot: Plot2d | Plot3d) -> None:
        super().__init__()

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Widget pour la simulation
        self.plot = plot
        self.main_layout.addWidget(self.plot.widget)

        # Widget pour les contrôles
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(5, 5, 5, 5)

        # Bouton pour afficher/masquer les contrôles
        self.toggle_button = QPushButton("Show Controls")
        self.toggle_button.clicked.connect(self.toggle_controls)
        self.main_layout.addWidget(self.toggle_button)

        # Layout pour les boutons de contrôle
        buttons_layout = QVBoxLayout()

        # Bouton Start
        self.start_button = QPushButton("Start Animation")
        self.start_button.clicked.connect(self.start_animation)
        buttons_layout.addWidget(self.start_button)

        # Bouton Pause/Resume
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause_animation)
        buttons_layout.addWidget(self.pause_button)

        # Bouton Reset
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_animation)
        buttons_layout.addWidget(self.reset_button)

        self.controls_layout.addLayout(buttons_layout)

        # Initialisation de la simulation (sans animation)
        self.plot.setup_animation()

        # Masquer les contrôles par défaut
        self.controls_widget.setVisible(False)

        # Raccourcis clavier
        self.setup_shortcuts()

    def setup_shortcuts(self) -> None:
        """Configure les raccourcis clavier."""

        # Raccourci pour pause/reprendre l'animation (Espace)
        self.pause_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.pause_shortcut.activated.connect(self.toggle_pause_animation)

        # Raccourci pour réinitialiser l'animation (Ctrl+R)
        self.reset_shortcut = QShortcut(QKeySequence("R "), self)
        self.reset_shortcut.activated.connect(self.reset_animation)

    def toggle_controls(self) -> None:
        """Affiche ou masque les contrôles."""
        if self.controls_widget.isVisible():
            self.controls_widget.setVisible(False)
            self.toggle_button.setText("Show Controls")
        else:
            self.controls_widget.setVisible(True)
            self.toggle_button.setText("Hide Controls")

    def start_animation(self) -> None:
        """Démarre l'animation."""
        self.plot.stop_animation()
        self.plot.setup_animation()
        self.plot.start_animation()
        self.pause_button.setText("Pause")

    def toggle_pause_animation(self) -> None:
        """Bascule entre pause et reprise de l'animation."""
        if self.plot.animation_timer.isActive():
            self.plot.animation_timer.stop()
            self.pause_button.setText("Resume")
        else:
            self.plot.animation_timer.start()
            self.pause_button.setText("Pause")

    def reset_animation(self) -> None:
        """Réinitialise l'animation."""
        self.plot.reset_animation()
        self.pause_button.setText("Pause")


class SimWidget3d(SimWidget):
    def __init__(self, plot: Plot3d) -> None:
        super().__init__(plot)

        self.plot_params = PlotParams()
        self.sim_params = Simulation3dParams()

        self.param_control = ParamControl3dWidget(
            self.plot_params, self.sim_params, plot
        )

        self.controls_layout.addWidget(self.param_control)
        self.main_layout.addWidget(self.controls_widget)


class SimWidget2d(SimWidget):
    def __init__(self, plot: Plot2d) -> None:
        super().__init__(plot)

        self.sim_params = Simulation2dParams()

        self.param_control = ParamControl2dWidget(self.sim_params, plot)

        self.controls_layout.addWidget(self.param_control)
        self.main_layout.addWidget(self.controls_widget)
