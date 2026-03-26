"""Libre mode with menu navigation and simulation controls."""

from typing import Any

from PySide6.QtCore import QEvent, QObject, Qt

from src.ui.modes.base import BaseMode
from src.utils.shortcuts import PRESENTATION_KEYS as PK


class _LibreFilter(QObject):
    """Keyboard handler for libre mode."""

    def eventFilter(self, win, event):
        if event.type() != QEvent.Type.KeyPress:
            return False
        k = event.key()

        if k == Qt.Key.Key_Escape:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                win.force_close()
            else:
                win.show_menu()
            return True

        if k == Qt.Key.Key_P and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            win.toggle_param_panel()
            return True

        if k == PK["play_pause"]:
            p = win.current_plot()
            if p:
                p.stop() if p.timer.isActive() else p.start()
            return True

        if k == PK["reset"]:
            p = win.current_plot()
            if p:
                p.reset()
            return True

        if k in (PK["preset_1"], PK["preset_2"], PK["preset_3"]):
            win.apply_current_preset(k - Qt.Key.Key_F1)
            return True

        return False


class LibreMode(BaseMode):
    def apply(self, win: Any) -> None:
        filt = _LibreFilter()
        win._key_filter = filt
        win.installEventFilter(filt)
        win._allow_close = False
        win.show_menu()
        win.showFullScreen()
