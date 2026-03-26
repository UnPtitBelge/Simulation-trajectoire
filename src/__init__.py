"""Main package for the Simulation Trajectoire application."""

# Provide easy access to main components
from src.app import MainApplication
from src.model.simulation import SIMULATIONS
from src.view import MainWindow

__all__ = [
    "MainApplication",
    "MainWindow",
    "SIMULATIONS",
]