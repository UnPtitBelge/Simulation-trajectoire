"""Timeline bar — chapter progress indicator for presentation mode."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from src.core.content.chapters import CHAPTERS
from src.utils.theme import (
    CLR_BADGE_BG,
    CLR_HEADER_BG,
    CLR_PRIMARY,
    CLR_STATUS_TEXT,
    FS_SM,
    FS_XS,
)


class TimelineBar(QWidget):
    """Horizontal bar showing chapter dots and navigation arrows.

    Emits ``chapter_clicked(int)`` when a chapter dot is clicked.
    """

    chapter_clicked = Signal(int)  # chapter index (0-based)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet(
            f"background: {CLR_HEADER_BG}; border-bottom: 1px solid #3C4043;"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 4, 16, 4)
        lay.setSpacing(4)

        # Chapter info label (left side)
        self._info = QLabel("")
        self._info.setStyleSheet(
            f"background: transparent; color: {CLR_STATUS_TEXT}; font-size: {FS_SM};"
        )
        self._info.setFixedWidth(200)
        lay.addWidget(self._info)

        lay.addStretch()

        # Chapter dots
        self._dots: list[QPushButton] = []
        for i, ch in enumerate(CHAPTERS):
            dot = QPushButton(str(ch.number))
            dot.setFixedSize(28, 28)
            dot.setToolTip(ch.title)
            dot.setStyleSheet(self._dot_style(active=False, visited=False))
            dot.clicked.connect(lambda _, idx=i: self.chapter_clicked.emit(idx))
            lay.addWidget(dot)
            self._dots.append(dot)

        lay.addStretch()

        # Step info (right side)
        self._step_info = QLabel("")
        self._step_info.setStyleSheet(
            f"background: transparent; color: {CLR_STATUS_TEXT}; font-size: {FS_XS};"
        )
        self._step_info.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._step_info.setFixedWidth(180)
        lay.addWidget(self._step_info)

        self._current_ch = -1

    def set_chapter(self, ch_idx: int, step_idx: int, total_steps: int) -> None:
        """Update the timeline to show the current chapter and step."""
        ch = CHAPTERS[ch_idx]
        self._info.setText(f"Ch. {ch.number} — {ch.title}")
        self._step_info.setText(f"Étape {step_idx + 1}/{total_steps}")

        for i, dot in enumerate(self._dots):
            dot.setStyleSheet(
                self._dot_style(active=(i == ch_idx), visited=(i < ch_idx))
            )
        self._current_ch = ch_idx

    @staticmethod
    def _dot_style(active: bool, visited: bool) -> str:
        if active:
            return (
                f"QPushButton {{ background: {CLR_PRIMARY}; color: white; "
                f"border-radius: 14px; font-size: {FS_XS}; font-weight: 600; border: none; }}"
            )
        if visited:
            return (
                f"QPushButton {{ background: {CLR_BADGE_BG}; color: {CLR_STATUS_TEXT}; "
                f"border-radius: 14px; font-size: {FS_XS}; border: none; }}"
            )
        return (
            f"QPushButton {{ background: transparent; color: {CLR_STATUS_TEXT}; "
            f"border-radius: 14px; font-size: {FS_XS}; "
            f"border: 1px solid {CLR_BADGE_BG}; }}"
        )
