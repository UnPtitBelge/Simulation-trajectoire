"""Guard page — splash screen to start the application."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.content import APP_TITLE
from src.util.theme import (
    CLR_BG,
    CLR_PRIMARY,
    CLR_TEXT,
    CLR_TEXT_SECONDARY,
    CLR_WHITE,
    FS_LG,
    FS_MD,
    FS_3XL,
)


class GuardPage(QWidget):
    """Full-screen welcome page with a start button.

    Emits ``started`` when the user clicks 'Commencer' or presses Enter/Space.
    """

    started = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {CLR_BG};")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(20)

        title = QLabel(APP_TITLE)
        title.setStyleSheet(
            f"color: {CLR_TEXT}; font-size: {FS_3XL}; font-weight: 600;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        subtitle = QLabel(
            "Modélisation, Simulation & Prédiction de Trajectoires"
        )
        subtitle.setStyleSheet(
            f"color: {CLR_TEXT_SECONDARY}; font-size: {FS_LG};"
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(subtitle)

        desc = QLabel(
            "Comprendre la simulation de la réalité par ordinateur\n"
            "Expérience : trajectoire d'une bille sur une membrane déformée"
        )
        desc.setStyleSheet(
            f"color: {CLR_TEXT_SECONDARY}; font-size: {FS_MD};"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        lay.addWidget(desc)

        lay.addSpacing(30)

        btn = QPushButton("Commencer")
        btn.setFixedSize(220, 50)
        btn.setStyleSheet(
            f"QPushButton {{ background: {CLR_PRIMARY}; color: {CLR_WHITE}; "
            f"font-size: {FS_LG}; font-weight: 500; border-radius: 8px; border: none; }}"
            f"QPushButton:hover {{ background: #1557B0; }}"
        )
        btn.clicked.connect(self.started.emit)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        hint = QLabel("Appuyez sur Entrée ou Espace pour commencer")
        hint.setStyleSheet(
            f"color: {CLR_TEXT_SECONDARY}; font-size: 11px; margin-top: 10px;"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(hint)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.started.emit()
        else:
            super().keyPressEvent(event)
