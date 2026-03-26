"""Theory overlay — semi-transparent card shown during theory steps."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.core.content.theory import THEORY
from src.utils.theme import (
    CLR_PRIMARY,
    CLR_SURFACE,
    CLR_TEXT,
    CLR_TEXT_SECONDARY,
    FS_LG,
    FS_MD,
    FS_SM,
)


class TheoryOverlay(QWidget):
    """Scrollable theory card that fills the presentation area.

    Call ``show_chapter(theory_key)`` to display the theory content
    for a given chapter. Call ``hide()`` to dismiss.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {CLR_SURFACE};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self._content = QWidget()
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(60, 40, 60, 40)
        self._lay.setSpacing(20)

        scroll.setWidget(self._content)
        outer.addWidget(scroll)

    def show_chapter(self, theory_key: str) -> None:
        """Populate with theory content and show the overlay."""
        # Clear previous content
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        topic = THEORY.get(theory_key)
        if not topic:
            self.hide()
            return

        # Title
        title = QLabel(topic["title"])
        title.setStyleSheet(
            f"color: {CLR_TEXT}; font-size: {FS_LG}; font-weight: 600;"
        )
        title.setWordWrap(True)
        self._lay.addWidget(title)

        # Sections
        for section in topic.get("sections", []):
            subtitle = QLabel(section["subtitle"])
            subtitle.setStyleSheet(
                f"color: {CLR_PRIMARY}; font-size: {FS_MD}; "
                f"font-weight: 500; margin-top: 8px;"
            )
            subtitle.setWordWrap(True)
            self._lay.addWidget(subtitle)

            text = QLabel(section["text"])
            text.setStyleSheet(
                f"color: {CLR_TEXT_SECONDARY}; font-size: {FS_SM}; "
                f"line-height: 1.6;"
            )
            text.setWordWrap(True)
            text.setTextFormat(Qt.TextFormat.PlainText)
            self._lay.addWidget(text)

        self._lay.addStretch()
        self.show()
