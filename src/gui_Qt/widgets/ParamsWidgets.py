"""Widgets that expose simulation and plot parameter controls.

This module provides two widgets that generate grouped parameter controls
for 3D and 2D simulations respectively. Each widget builds a small layout
and uses the generic `ParamsController` to generate controls from a
dataclass describing parameters.
"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QWidget
from utils.params import PlotParams, Simulation2dParams, Simulation3dParams
from utils.params_controller import ParamsController


class ParamControl3dWidget(QWidget):
    """Control panel grouping plot and 3D simulation parameters.

    The widget creates two group boxes: one for plot parameters and one for
    simulation parameters. Each group hosts a `ParamsController` instance
    which builds individual parameter controls from the corresponding dataclass.
    """

    def __init__(self, plot_params, sim_params, plot):
        super().__init__()
        self.plot_params = plot_params
        self.sim_params = sim_params
        self.plot = plot

        # Groups for parameters
        plot_group = QGroupBox("Plot Parameters")
        sim_group = QGroupBox("Simulation Parameters")

        # Controllers for each group (generate controls from dataclasses)
        plot_controller = ParamsController(plot_params, PlotParams, plot)
        sim_controller = ParamsController(sim_params, Simulation3dParams, plot)

        # Layouts for the groups
        plot_layout = QHBoxLayout()
        plot_layout.addWidget(plot_controller)
        plot_group.setLayout(plot_layout)

        sim_layout = QHBoxLayout()
        sim_layout.addWidget(sim_controller)
        sim_group.setLayout(sim_layout)

        # Main layout: place plot and simulation groups vertically
        main_layout = QVBoxLayout()
        main_layout.addWidget(plot_group)
        main_layout.addWidget(sim_group)
        self.setLayout(main_layout)


class ParamControl2dWidget(QWidget):
    """Control panel for 2D simulation parameters.

    This widget builds a single group containing the 2D simulation parameter
    controls produced by `ParamsController`. It mirrors the structure used by
    the 3D control widget but only exposes the simulation parameters.
    """

    def __init__(self, sim_params, plot):
        super().__init__()
        self.sim_params = sim_params
        self.plot = plot

        # Group box for the 2D simulation parameters
        group_box = QGroupBox("2D Simulation Parameters")

        # Controller that generates parameter controls from the Simulation2dParams dataclass
        controller = ParamsController(sim_params, Simulation2dParams, plot)

        # Main layout: horizontal container inside the group box
        main_layout = QHBoxLayout()
        main_layout.addWidget(controller)
        group_box.setLayout(main_layout)

        # Outer layout: vertical container holding the group box
        widget_layout = QVBoxLayout()
        widget_layout.addWidget(group_box)
        self.setLayout(widget_layout)
