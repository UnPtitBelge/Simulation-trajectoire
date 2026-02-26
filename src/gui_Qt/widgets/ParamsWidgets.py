from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QWidget

from utils.params import PlotParams, Simulation2dParams, Simulation3dParams
from utils.ParamsController import ParamsController


class ParamControl3dWidget(QWidget):
    def __init__(self, plot_params, sim_params, plot):
        super().__init__()
        self.plot_params = plot_params
        self.sim_params = sim_params
        self.plot = plot

        # Groupes pour les paramètres
        plot_group = QGroupBox("Plot Parameters")
        sim_group = QGroupBox("Simulation Parameters")

        # Contrôleurs pour chaque groupe
        plot_controller = ParamsController(plot_params, PlotParams, plot)
        sim_controller = ParamsController(sim_params, Simulation3dParams, plot)

        # Layouts pour les groupes
        plot_layout = QHBoxLayout()
        plot_layout.addWidget(plot_controller)
        plot_group.setLayout(plot_layout)

        sim_layout = QHBoxLayout()
        sim_layout.addWidget(sim_controller)
        sim_group.setLayout(sim_layout)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(plot_group)
        main_layout.addWidget(sim_group)
        self.setLayout(main_layout)


class ParamControl2dWidget(QWidget):
    def __init__(self, sim_params, plot):
        super().__init__()
        self.sim_params = sim_params
        self.plot = plot

        # Groupe pour les paramètres
        group_box = QGroupBox("2D Simulation Parameters")

        # Contrôleur pour les paramètres
        controller = ParamsController(sim_params, Simulation2dParams, plot)

        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.addWidget(controller)
        group_box.setLayout(main_layout)

        widget_layout = QVBoxLayout()
        widget_layout.addWidget(group_box)
        self.setLayout(widget_layout)
