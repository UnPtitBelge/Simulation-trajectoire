"""Presentation mode — navigation entre 4 chapitres de simulation.

Navigation :
  ←→      : chapitre suivant / précédent
  1-4     : aller directement au chapitre N
  Espace  : lecture / pause de la simulation courante
  R       : réinitialiser la simulation courante
  F1-F3   : appliquer un preset (vitesse / position) à la simulation courante
  Ctrl+P  : afficher / masquer le panneau de paramètres
  M       : ajouter un repère (simulations 3D)
  Suppr   : effacer les repères

Contrôles Sim-to-Real uniquement :
  T           : basculer entre les modèles RL et MLP
  Ctrl+1/2/3  : changer la taille du contexte (50 / 45 000 / 90 000 trajectoires)
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

        # Ctrl+1/2/3 : taille du contexte (sim_to_real uniquement)
        if k in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3) and ctrl:
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
    """Présentation en 4 chapitres — une simulation par chapitre."""

    def apply(self, win: Any) -> None:
        filt = _PresentationFilter()
        win._key_filter = filt
        win.installEventFilter(filt)
        win._presentation_mode = True
        win.showFullScreen()
        win.pres_show_guard()
