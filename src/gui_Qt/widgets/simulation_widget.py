import PySide6.QtWidgets as QtW
from PySide6 import QtGui as QtG


class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modèles & Simulations")
