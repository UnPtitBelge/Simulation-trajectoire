"""Dialogue modal d'édition des conditions initiales (mode présentation).

Ouvert avec Ctrl+P pendant une simulation en mode présentation.
Les modifications sont appliquées au plot **et** persistées en JSON
uniquement à la confirmation (bouton « Appliquer »).

La simulation n'est PAS relancée automatiquement : l'utilisateur doit
appuyer sur Espace pour redémarrer.

Classe publique
---------------
PresentationConfigDialog
    Dialogue modal qui contient un ParamsController sans plot attaché.
    Sur confirmation, applique les changements et sauvegarde en JSON.
"""
from __future__ import annotations

import dataclasses
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from utils import config_manager as _cfg
from utils import stylesheet as _ss
from utils.params_controller import ParamsController

log = logging.getLogger(__name__)

# Noms d'affichage pour le titre du dialogue.
_SIM_TITLES: dict[str, str] = {
    "mcu":      "2D MCU — Mouvement Circulaire Uniforme",
    "cone":     "3D Cône — Surface de Newton",
    "membrane": "3D Membrane — Surface de Laplace",
    "ml":       "Machine Learning — Prédiction de trajectoire",
}


class PresentationConfigDialog(QDialog):
    """Dialogue modal pour éditer les conditions initiales d'une simulation.

    Le dialogue affiche un :class:`ParamsController` initialisé sur une copie
    des paramètres courants.  Les changements restent locaux jusqu'à la
    confirmation : ils ne sont jamais appliqués « en direct ».

    À la confirmation :

    1. Chaque champ modifié est copié dans ``plot.sim_params``.
    2. ``plot._prepared`` est mis à ``False`` pour signaler que la simulation
       doit être recalculée avant le prochain lancement.
    3. Les paramètres sont persistés en JSON via :func:`config_manager.save_params`.

    Parameters
    ----------
    sim_key : str
        Clé de simulation (``"mcu"``, ``"cone"``, ``"membrane"``, ``"ml"``).
    plot : Plot
        Backend de la simulation courante.  Son ``sim_params`` est lu en
        entrée et mis à jour en sortie.
    parent : QWidget, optional
        Widget parent pour la gestion mémoire Qt.
    """

    def __init__(
        self,
        sim_key: str,
        plot,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._sim_key = sim_key
        self._plot = plot

        self.setWindowTitle(_SIM_TITLES.get(sim_key, sim_key.upper()))
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)
        self.setStyleSheet(f"background-color: {_ss.CLR_BASE}; color: {_ss.CLR_TEXT};")

        # Copie de travail — jamais mutée en dehors du contrôleur.
        self._edit_params = dataclasses.replace(plot.sim_params)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # Indications en haut du dialogue.
        hint = QLabel(
            "Modifiez les paramètres puis cliquez « Appliquer ».\n"
            "La simulation sera recalculée — appuyez sur Espace pour la relancer."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {_ss.CLR_SUBTEXT}; font-size: 13px; "
            f"background: {_ss.CLR_SURFACE0}; border-radius: 6px; padding: 8px 12px;"
        )
        root.addWidget(hint)

        # Contrôleur de paramètres sans plot attaché (pas d'application en direct).
        self._ctrl = ParamsController(
            self._edit_params,
            type(self._edit_params),
            plot=None,
        )
        scroll = QScrollArea()
        scroll.setWidget(self._ctrl)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")
        root.addWidget(scroll, stretch=1)

        # Boutons OK / Annuler.
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("Appliquer")
        ok_btn.setStyleSheet(
            f"QPushButton {{ background: {_ss.CLR_ACCENT}; color: #fff; "
            f"border: none; border-radius: 6px; padding: 6px 20px; font-weight: 700; }}"
            f"QPushButton:hover {{ background: {_ss.CLR_ACCENT_HOVER}; }}"
        )
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("Annuler")
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background: {_ss.CLR_SURFACE1}; color: {_ss.CLR_TEXT}; "
            f"border: 1px solid {_ss.CLR_BORDER}; border-radius: 6px; padding: 6px 20px; }}"
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        log.debug(
            "PresentationConfigDialog ouvert pour %s (params: %s)",
            sim_key,
            type(self._edit_params).__name__,
        )

    def _apply(self) -> None:
        """Applique les modifications et persiste la configuration.

        Copie chaque champ de ``_edit_params`` dans ``plot.sim_params``,
        marque le plot comme non préparé, et sauvegarde en JSON.
        """
        for f in dataclasses.fields(self._edit_params):
            setattr(self._plot.sim_params, f.name, getattr(self._edit_params, f.name))

        # Signaler que la simulation doit être recalculée.
        self._plot._prepared = False
        self._plot.stop_animation()

        _cfg.save_params(self._sim_key, self._edit_params)
        log.info(
            "PresentationConfigDialog — paramètres appliqués pour %s", self._sim_key
        )
        self.accept()
