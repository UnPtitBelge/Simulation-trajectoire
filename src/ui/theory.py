"""Theory page — scrollable educational articles for libre mode."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.core.content.theory import THEORY
from src.utils.theme import CLR_TEXT_SECONDARY, FS_MD, FS_SM, FS_2XL


def _make_section(subtitle: str, text: str) -> QFrame:
    """Build a single section card."""
    card = QFrame()
    card.setProperty("card", True)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 12, 16, 12)
    lay.setSpacing(6)

    title = QLabel(f"<b>{subtitle}</b>")
    title.setStyleSheet(f"font-size: {FS_MD};")
    lay.addWidget(title)

    body = QLabel(text)
    body.setWordWrap(True)
    body.setStyleSheet(f"font-size: {FS_SM}; color: {CLR_TEXT_SECONDARY}; line-height: 1.5;")
    lay.addWidget(body)
    return card


class TheoryPage(QWidget):
    """Full-page scrollable view showing all theory topics."""

    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(24)

        # Back button
        back = QPushButton("← Retour au menu")
        back.setProperty("flat", True)
        back.clicked.connect(on_back)
        lay.addWidget(back, alignment=Qt.AlignmentFlag.AlignLeft)

        # Page title
        title = QLabel("Théorie de la modélisation")
        title.setStyleSheet(f"font-size: {FS_2XL}; font-weight: 500;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        subtitle = QLabel("Concepts fondamentaux pour comprendre les simulations")
        subtitle.setStyleSheet(f"font-size: {FS_MD}; color: {CLR_TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(subtitle)

        # Build one block per theory topic
        for _key, topic in THEORY.items():
            lay.addWidget(self._build_topic(topic))

        lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    @staticmethod
    def _build_topic(topic: dict) -> QFrame:
        """Build a framed block for one theory topic."""
        block = QFrame()
        block.setProperty("card", True)
        lay = QVBoxLayout(block)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        header = QLabel(topic["title"])
        header.setProperty("role", "section")
        lay.addWidget(header)

        for section in topic["sections"]:
            lay.addWidget(_make_section(section["subtitle"], section["text"]))

        return block
