"""Presentation mode — navigation between 4 simulation chapters.

Navigation:
  ←→      : next/previous chapter
  1-4     : go directly to chapter N
  Space   : play/pause current simulation
  R       : reset current simulation
  F1-F3   : apply preset (speed/position) to current simulation
  Ctrl+P  : show/hide parameter panel
  M       : add marker (3D simulations)
  Delete  : clear markers

Sim-to-Real controls only:
  T           : toggle between RL and MLP models
  Ctrl+1/2/3/4: change context size (50 / 45k / 90k / 1M trajectories)
"""

from typing import Any

from PySide6.QtCore import QEvent, QObject, Qt

from src.content.chapters import CHAPTERS
from src.model.params.integrators import MLModel
from src.model.ml.sim_to_real.data_utils import _CONTEXT_LABELS
from src.view.modes.base import BaseMode


class _PresentationFilter(QObject):
    """Keyboard handler for chapter-based presentation mode."""

    def eventFilter(self, win, event):
        if event.type() != QEvent.Type.KeyPress:
            return False
        k = event.key()
        mods = event.modifiers()
        ctrl = mods == Qt.KeyboardModifier.ControlModifier

        if k == Qt.Key.Key_Escape:
            if win._guard.isVisible():
                win._allow_close = True
                win.close()
            else:
                win.pres_show_guard()
            return True

        if k == Qt.Key.Key_P and ctrl:
            win.toggle_param_panel()
            return True

        if k in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            win.pres_next_step()
            return True

        if k in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            win.pres_prev_step()
            return True

        # Ctrl+1/2/3/4 : taille du contexte (sim_to_real uniquement)
        if k in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4) and ctrl:
            p = win.current_plot()
            if p is not None and hasattr(p, "apply_context_preset"):
                idx = k - Qt.Key.Key_1
                p.apply_context_preset(idx)
                win.set_status(f"Contexte : {_CONTEXT_LABELS[idx]}")
            return True

        # 1-4 sans modificateur : navigation chapitres
        if Qt.Key.Key_1 <= k <= Qt.Key.Key_9:
            if mods == Qt.KeyboardModifier.NoModifier:
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

        # T : toggle RL/MLP (sim_to_real uniquement)
        if k == Qt.Key.Key_T:
            p = win.current_plot()
            if p is not None and hasattr(p, "toggle_model"):
                p.toggle_model()
                name = "MLP" if p.params.model_type == MLModel.MLP else "RL"
                win.set_status(f"Modèle : {name}")
            return True

        if k == Qt.Key.Key_M:
            win.add_pres_marker()
            return True

        if k == Qt.Key.Key_Delete:
            win.clear_pres_markers()
            return True

        return False


class PresentationMode(BaseMode):
    """Presentation mode with 4 chapters — one simulation per chapter."""

    def apply(self, win: Any) -> None:
        filt = _PresentationFilter()
        win._key_filter = filt
        win.installEventFilter(filt)
        win.showFullScreen()
        win.show_guard()
