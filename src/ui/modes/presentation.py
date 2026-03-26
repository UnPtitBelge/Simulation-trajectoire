"""Presentation mode — chapter-based navigation through the fiche théorique.

Navigation:
  ←→      : next/previous step
  1-9     : jump to chapter (by number)
  Space   : play/pause current simulation
  R       : reset current simulation
  F1-F3   : apply preset to current simulation
  Ctrl+P  : toggle parameter panel
  M       : add marker (3D sims)
  Suppr   : clear markers
  Échap   : return to guard page, or quit if already on guard page
"""

from typing import Any

from PySide6.QtCore import QEvent, QObject, Qt

from src.core.content.chapters import CHAPTERS
from src.ui.modes.base import BaseMode


class _PresentationFilter(QObject):
    """Keyboard handler for chapter-based presentation mode."""

    def eventFilter(self, win, event):
        if event.type() != QEvent.Type.KeyPress:
            return False
        k = event.key()

        if k == Qt.Key.Key_Escape:
            # Check if we're on the guard page
            if win._guard.isVisible():
                # Already on guard page → quit application
                win._allow_close = True
                win.close()
            else:
                # In a chapter → return to guard page
                win.pres_show_guard()
            return True

        if k == Qt.Key.Key_P and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            win.toggle_param_panel()
            return True

        if k in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            win.pres_next_step()
            return True

        if k in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            win.pres_prev_step()
            return True

        if Qt.Key.Key_1 <= k <= Qt.Key.Key_9:
            ch_idx = k - Qt.Key.Key_1
            if ch_idx < len(CHAPTERS):
                win.pres_goto_chapter(ch_idx)
            return True

        if k == Qt.Key.Key_Space:
            p = win.current_plot()
            if p:
                if p.timer.isActive():
                    p.stop()
                    win.set_status("En pause")
                else:
                    p.start()
                    win.set_status("Lecture...")
            return True

        if k == Qt.Key.Key_R:
            p = win.current_plot()
            if p:
                p.reset()
                win.set_status("Réinitialisé")
            return True

        if k in (Qt.Key.Key_F1, Qt.Key.Key_F2, Qt.Key.Key_F3):
            win.apply_current_preset(k - Qt.Key.Key_F1)
            return True

        if k == Qt.Key.Key_M:
            win.add_pres_marker()
            return True

        if k == Qt.Key.Key_Delete:
            win.clear_pres_markers()
            return True

        return False


class PresentationMode(BaseMode):
    """Chapter-based presentation following the 13-chapter fiche théorique."""

    def apply(self, win: Any) -> None:
        filt = _PresentationFilter()
        win._key_filter = filt
        win.installEventFilter(filt)
        win._presentation_mode = True
        win.showFullScreen()
        win.pres_show_guard()
