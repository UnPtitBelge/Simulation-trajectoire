"""Main package for the Simulation Trajectoire application."""

# Provide easy access to main components
from src.application.app import MainApplication
from src.simulations import SIMULATIONS
from src.ui import MainWindow

__all__ = [
    "MainApplication",
    "MainWindow",
    "SIMULATIONS",
]
