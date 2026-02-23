import sys

from PySide6.QtWidgets import QApplication, QLabel


def run():
    app = QApplication(sys.argv)
    label = QLabel("Placeholder")
    label.show()
    app.exec()
