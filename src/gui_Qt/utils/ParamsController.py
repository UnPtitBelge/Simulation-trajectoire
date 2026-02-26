from dataclasses import fields

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
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
    value_changed = Signal(str, float)

    def __init__(self, param_name, default_value, min_value, max_value, step):
        super().__init__()
        self.param_name = param_name
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

        # Label pour le nom du paramètre
        self.label = QLabel(param_name)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # QDoubleSpinBox pour l'entrée manuelle
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setRange(min_value, max_value)
        self.spin_box.setSingleStep(step)
        self.spin_box.setValue(default_value)
        self.spin_box.setDecimals(3)
        self.spin_box.setMaximumWidth(80)
        self.spin_box.valueChanged.connect(self.emit_value_changed)

        # Boutons pour incrémenter/décrémenter
        self.increment_button = QPushButton("+")
        self.increment_button.setFixedSize(20, 20)
        self.increment_button.clicked.connect(self.spin_box.stepUp)

        self.decrement_button = QPushButton("-")
        self.decrement_button.setFixedSize(20, 20)
        self.decrement_button.clicked.connect(self.spin_box.stepDown)

        # Layout horizontal pour les boutons et la QDoubleSpinBox
        spin_box_layout = QHBoxLayout()
        spin_box_layout.setContentsMargins(0, 0, 0, 0)
        spin_box_layout.setSpacing(2)
        spin_box_layout.addWidget(self.decrement_button)
        spin_box_layout.addWidget(self.spin_box)
        spin_box_layout.addWidget(self.increment_button)

        # Layout principal pour le label et le complexe (boutons + QDoubleSpinBox)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # Ajouter le label
        main_layout.addWidget(self.label)

        # Ajouter un espaceur élastique pour pousser le complexe à droite
        main_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        # Ajouter le complexe (boutons + QDoubleSpinBox)
        main_layout.addLayout(spin_box_layout)

        self.setLayout(main_layout)

    def emit_value_changed(self, value):
        self.value_changed.emit(self.param_name, value)

    def get_value(self):
        return self.spin_box.value()


class ParamsController(QWidget):
    def __init__(self, params, param_type, plot=None):
        super().__init__()
        self.params = params
        self.param_type = param_type
        self.plot = plot
        self.default_params = param_type()
        self.param_controls = {}

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges
        self.layout.setSpacing(2)  # Espacement réduit
        self.setLayout(self.layout)

        # Créer un contrôle pour chaque paramètre
        for field in fields(self.params):
            param_name = field.name
            default_value = getattr(self.params, param_name)
            step = self.calculate_step(default_value)
            min_value = default_value * 0.1
            max_value = default_value * 10

            control = ParamControlWidget(
                param_name, default_value, min_value, max_value, step
            )
            control.value_changed.connect(self.on_value_changed)
            self.param_controls[param_name] = control
            self.layout.addWidget(control)

        # Bouton de réinitialisation
        reset_button = QPushButton("Reset")
        reset_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        reset_button.setFixedSize(60, 20)  # Taille fixe pour le bouton
        reset_button.clicked.connect(self._reset_to_default)
        self.layout.addWidget(reset_button)

    def calculate_step(self, default_value):
        if default_value < 1:
            return 0.01
        elif default_value < 10:
            return 0.1
        elif default_value < 100:
            return 1
        else:
            return 10

    def on_value_changed(self, param_name, value):
        setattr(self.params, param_name, value)
        if self.plot is not None:
            self.plot.update_params(**{param_name: value})

    def _reset_to_default(self):
        for field in fields(self.params):
            param_name = field.name
            default_value = getattr(self.default_params, param_name)
            setattr(self.params, param_name, default_value)
            self.param_controls[param_name].spin_box.setValue(default_value)
            if self.plot is not None:
                self.plot.update_params(**{param_name: default_value})
