"""Point d'entrée et fenêtre principale de l'application.

Modes
-----
Normal (défaut)     Fenêtre maximisée, onglets LazyTabWidget.
``--presentation``  Plein écran, simulation seule (aucun chrome),
                    touches 1–4 pour naviguer, Ctrl+P pour les paramètres,
                    Espace pour lancer/pause.
``--libre``         Plein écran, interface MD3 avec rail de navigation,
                    tableau de bord en temps réel, page scénarios.
``--light``         Thème clair (forcé en mode libre).
``--debug``         Journalisation détaillée.

Architecture des modes
----------------------
Mode présentation
    ``_PresentationSlot`` × 4 — chaque slot contient un plot + overlay
    de chargement.  Les slots sont créés et préparés à la demande (lazy).
    Aucune barre d'outils, aucun panneau de contrôle visible.

Mode libre
    ``LibreNavRail`` (80 px, gauche) + ``QStackedWidget`` (droite).
    Stack : 4 × ``LibreSimPage`` + 1 × ``ScenariosPage`` (toutes lazy).
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from utils import stylesheet as _ss
from utils.logger import get_log_path, setup_logging
from utils.ui_constants import (
    TOPBAR_H, TOPBAR_TITLE_PT, TOPBAR_LETTER_SP, TOPBAR_MARGINS,
    CLOSE_W, CLOSE_H, APP_FONT_FAMILY, APP_FONT_PT,
)
from utils.ui_strings import WINDOW_TITLE, TOPBAR_TITLE, CLOSE_BTN, TAB_MCU, TAB_CONE, TAB_MEMBRANE, TAB_ML

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mode présentation — slot de simulation (plot + overlay)
# ---------------------------------------------------------------------------

class _PrepareWorker(QThread):
    """Exécute ``_prepare_simulation()`` hors du thread principal."""

    done = Signal()

    def __init__(self, plot) -> None:
        super().__init__()
        self._plot = plot

    def run(self) -> None:
        self._plot._prepare_simulation()
        self.done.emit()


class _PresentationSlot(QWidget):
    """Slot de simulation pour le mode présentation.

    Affiche uniquement le ``plot.widget`` (plein espace), sans aucun
    chrome applicatif.  Une barre de chargement semi-transparente couvre
    la zone jusqu'à la fin de la préparation.

    Attributs publics
    -----------------
    plot : Plot
        Backend de simulation.
    sim_key : str
        Clé JSON du slot (``"mcu"``, ``"cone"``, ``"membrane"``, ``"ml"``).
    """

    def __init__(self, sim_key: str, plot) -> None:
        super().__init__()
        self.sim_key = sim_key
        self.plot = plot
        self.setStyleSheet("background: #000000;")

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(self.plot.widget, 0, 0)

        self._loading = QWidget()
        self._loading.setStyleSheet("background: rgba(0,0,0,220);")
        ll = QVBoxLayout(self._loading)
        ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("Calcul en cours…")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #ffffff; font-size: 16px; background: transparent;")
        ll.addWidget(lbl)
        grid.addWidget(self._loading, 0, 0)

        self._worker = _PrepareWorker(self.plot)
        self._worker.done.connect(self._on_ready)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_ready(self) -> None:
        self.plot._prepared = True
        self.plot.current_frame = 0
        self.plot._draw_initial_frame()
        self._loading.setVisible(False)
        self._worker = None
        log.info("_PresentationSlot prêt — %s", self.sim_key)

    def space_pressed(self) -> None:
        """Gère Espace : lance/pause selon l'état courant.

        Si le plot n'est pas encore préparé (paramètres modifiés avec
        Ctrl+P), recalcule la simulation en synchrone avant de démarrer.
        """
        if not self.plot._prepared:
            # Paramètres ont changé → recalcul synchrone (acceptable en
            # mode présentation où le présentateur contrôle l'exécution).
            self.plot.setup_animation()
            self.plot._prepared = True
            self._loading.setVisible(False)
            self.plot.start_animation()
            return

        if self.plot.animation_timer.isActive():
            self.plot.stop_animation()
        else:
            # Redémarre depuis le début
            self.plot.reset_animation()
            self.plot.start_animation()

    def activate(self) -> None:
        """Appelé lors du passage vers ce slot (optionnel : auto-start)."""
        pass  # Le démarrage est volontaire (Espace)

    def deactivate(self) -> None:
        """Arrête l'animation quand on quitte ce slot."""
        self.plot.stop_animation()


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Fenêtre principale gérant les trois modes d'affichage."""

    def __init__(
        self,
        presentation_mode: bool = False,
        libre_mode: bool = False,
    ) -> None:
        super().__init__()
        self.presentation_mode = presentation_mode
        self.libre_mode = libre_mode
        self.setWindowTitle(WINDOW_TITLE)

        container = QWidget()
        self.setCentralWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        if presentation_mode:
            self._build_presentation_mode(root)
        elif libre_mode:
            self._build_libre_mode(root)
        else:
            self._build_normal_mode(root)

        log.info(
            "MainWindow prête — presentation=%s libre=%s",
            presentation_mode, libre_mode,
        )

    # =========================================================================
    # Mode présentation
    # =========================================================================

    def _build_presentation_mode(self, root: QVBoxLayout) -> None:
        """Construit l'interface de présentation : simulation seule + raccourcis."""
        from utils import config_manager as _cfg
        from simulations.sim2d.PlotMCU import PlotMCU
        from simulations.sim3d.PlotCone import PlotCone
        from simulations.sim3d.PlotMembrane import PlotMembrane
        from simulations.simML.PlotML import PlotML

        # Créer les 4 plots depuis les fichiers de config JSON.
        plots = [
            PlotMCU(_cfg.load_params("mcu")),
            PlotCone(_cfg.load_params("cone")),
            PlotMembrane(_cfg.load_params("membrane")),
            PlotML(_cfg.load_params("ml")),
        ]
        keys = ["mcu", "cone", "membrane", "ml"]

        # Un QStackedWidget avec 4 slots.
        self._pres_stack = QStackedWidget()
        self._pres_slots: list[_PresentationSlot] = []
        for key, plot in zip(keys, plots):
            slot = _PresentationSlot(key, plot)
            self._pres_slots.append(slot)
            self._pres_stack.addWidget(slot)

        root.addWidget(self._pres_stack, stretch=1)
        self._pres_current_idx = 0

        self._setup_presentation_shortcuts()
        log.info("Mode présentation — 4 slots créés")

    def _setup_presentation_shortcuts(self) -> None:
        ctx = Qt.ShortcutContext.ApplicationShortcut

        # 1–4 : changer de simulation
        for key, idx in [("1", 0), ("2", 1), ("3", 2), ("4", 3)]:
            QShortcut(QKeySequence(key), self, context=ctx).activated.connect(
                lambda i=idx: self._pres_switch(i)
            )

        # Espace : lancer / pause
        QShortcut(QKeySequence("Space"), self, context=ctx).activated.connect(
            self._pres_space
        )

        # Ctrl+P : dialogue de paramètres
        QShortcut(QKeySequence("Ctrl+P"), self, context=ctx).activated.connect(
            self._pres_open_config
        )

        # Échap : quitter
        QShortcut(QKeySequence("Esc"), self, context=ctx).activated.connect(
            QApplication.quit
        )

    def _pres_switch(self, idx: int) -> None:
        """Passe au slot *idx* (0-basé) en arrêtant l'animation courante."""
        if idx == self._pres_current_idx:
            return
        self._pres_slots[self._pres_current_idx].deactivate()
        self._pres_current_idx = idx
        self._pres_stack.setCurrentIndex(idx)
        self._pres_slots[idx].activate()
        log.debug("Présentation — slot actif : %d", idx)

    def _pres_space(self) -> None:
        """Délègue la pression d'Espace au slot courant."""
        self._pres_slots[self._pres_current_idx].space_pressed()

    def _pres_open_config(self) -> None:
        """Ouvre le dialogue Ctrl+P pour les conditions initiales."""
        from widgets.PresentationConfigDialog import PresentationConfigDialog
        slot = self._pres_slots[self._pres_current_idx]
        dlg = PresentationConfigDialog(slot.sim_key, slot.plot, parent=self)
        dlg.exec()
        # Après "Appliquer" : _prepared = False (mis par le dialogue).
        # L'utilisateur appuie sur Espace pour relancer.

    # =========================================================================
    # Mode libre (MD3)
    # =========================================================================

    def _build_libre_mode(self, root: QVBoxLayout) -> None:
        """Construit l'interface MD3 : rail de navigation + pages lazy."""
        from utils import libre_config
        from utils.libre_config import SCENARIOS, SIM_TYPE_ORDER, CONTENT
        from widgets.LibreNavRail import LibreNavRail

        # Le mode libre impose le thème clair MD3.
        _ss.set_theme(light=True)

        content_area = QWidget()
        content_area.setStyleSheet(f"background: {_ss.MD3_BG};")
        outer = QHBoxLayout(content_area)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Rail de navigation gauche
        self._nav_rail = LibreNavRail()
        outer.addWidget(self._nav_rail)

        # Stack de contenu (4 pages sim + 1 page scénarios)
        self._lib_stack = QStackedWidget()
        self._lib_stack.setStyleSheet(f"background: {_ss.MD3_BG};")
        outer.addWidget(self._lib_stack, stretch=1)

        root.addWidget(content_area, stretch=1)

        # Pages lazies — None jusqu'au premier accès.
        self._libre_pages: list[object | None] = [None] * 4  # sim pages
        self._scenarios_page = None
        self._lib_placeholders: list[QWidget] = []

        # Créer des placeholders légers dans le stack.
        for _ in range(5):
            ph = QWidget()
            ph.setStyleSheet(f"background: {_ss.MD3_BG};")
            self._lib_stack.addWidget(ph)
            self._lib_placeholders.append(ph)

        # Connexions rail ↔ stack
        self._nav_rail.page_selected.connect(self._libre_switch)
        self._nav_rail.exit_requested.connect(QApplication.quit)

        # Raccourcis clavier
        ctx = Qt.ShortcutContext.ApplicationShortcut
        for key, idx in [("1", 0), ("2", 1), ("3", 2), ("4", 3)]:
            QShortcut(QKeySequence(key), self, context=ctx).activated.connect(
                lambda i=idx: self._libre_switch(i)
            )
        QShortcut(QKeySequence("Esc"), self, context=ctx).activated.connect(
            QApplication.quit
        )

        # Charger la première page de simulation par défaut.
        self._libre_switch(0)
        log.info("Mode libre — interface MD3 construite")

    def _libre_switch(self, page_idx: int) -> None:
        """Navigue vers la page *page_idx* (0–3 = sim, 4 = scénarios)."""
        from utils import libre_config
        from utils.libre_config import SCENARIOS, SIM_TYPE_ORDER, CONTENT

        self._nav_rail.set_active(page_idx)

        if page_idx < 4:
            # Page simulation
            if self._libre_pages[page_idx] is None:
                stype = SIM_TYPE_ORDER[page_idx]
                params = libre_config.fresh(
                    [libre_config.MCU, libre_config.CONE,
                     libre_config.MEMBRANE, libre_config.ML][page_idx]
                )
                from widgets.LibreSimPage import LibreSimPage
                page = LibreSimPage(stype, params, CONTENT[stype])
                self._libre_pages[page_idx] = page
                # Remplacer le placeholder dans le stack
                ph = self._lib_placeholders[page_idx]
                idx_in_stack = self._lib_stack.indexOf(ph)
                self._lib_stack.removeWidget(ph)
                self._lib_stack.insertWidget(idx_in_stack, page)
                ph.deleteLater()
                self._lib_placeholders[page_idx] = page  # keep ref
                log.debug("LibreSimPage créée — type=%s", stype)

            self._lib_stack.setCurrentWidget(self._libre_pages[page_idx])

        else:
            # Page scénarios
            if self._scenarios_page is None:
                from widgets.ScenariosPage import ScenariosPage
                self._scenarios_page = ScenariosPage(SCENARIOS, SIM_TYPE_ORDER)
                self._scenarios_page.scenario_launch_requested.connect(
                    self._on_scenario_launch
                )
                ph = self._lib_placeholders[4]
                idx_in_stack = self._lib_stack.indexOf(ph)
                self._lib_stack.removeWidget(ph)
                self._lib_stack.insertWidget(idx_in_stack, self._scenarios_page)
                ph.deleteLater()
                self._lib_placeholders[4] = self._scenarios_page
                log.debug("ScenariosPage créée")

            self._lib_stack.setCurrentWidget(self._scenarios_page)

    def _on_scenario_launch(self, type_idx: int, scen_idx: int) -> None:
        """Charge le scénario dans la page de simulation et y navigue.

        Parameters
        ----------
        type_idx : int
            Index du type de simulation (0 = MCU, 1 = Cône, …).
        scen_idx : int
            Index du scénario au sein du groupe de ce type.
        """
        from utils.libre_config import SCENARIOS, SIM_TYPE_ORDER
        import dataclasses

        stype = SIM_TYPE_ORDER[type_idx]
        type_scenarios = [s for s in SCENARIOS if s.sim_type == stype]
        if scen_idx >= len(type_scenarios):
            return

        scenario = type_scenarios[scen_idx]
        params = dataclasses.replace(scenario.params)

        # S'assurer que la page est construite, puis recharger.
        self._libre_switch(type_idx)
        page = self._libre_pages[type_idx]
        if page is not None:
            page.reload_with_params(params)

        log.info(
            "Scénario lancé — %s / %s", stype, scenario.title
        )

    # =========================================================================
    # Mode normal (onglets)
    # =========================================================================

    def _build_normal_mode(self, root: QVBoxLayout) -> None:
        """Construit l'interface normale avec barre supérieure et onglets."""
        # Barre supérieure
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(TOPBAR_H)

        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(*TOPBAR_MARGINS)
        tb_layout.setSpacing(0)

        title_label = QLabel(TOPBAR_TITLE)
        title_label.setObjectName("topBarTitle")
        title_font = QFont()
        title_font.setPointSize(TOPBAR_TITLE_PT)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, TOPBAR_LETTER_SP)
        title_label.setFont(title_font)
        tb_layout.addWidget(title_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb_layout.addWidget(spacer)

        close_btn = QPushButton(CLOSE_BTN)
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(CLOSE_W, CLOSE_H)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.clicked.connect(QApplication.quit)
        tb_layout.addWidget(close_btn)

        root.addWidget(top_bar)

        # Onglets lazy
        from widgets.ScenarioHub import LazyTabWidget
        self.tabs = LazyTabWidget()
        self.tabs.addLazyTab(self._make_mcu,      TAB_MCU)
        self.tabs.addLazyTab(self._make_cone,     TAB_CONE)
        self.tabs.addLazyTab(self._make_membrane, TAB_MEMBRANE)
        self.tabs.addLazyTab(self._make_ml,       TAB_ML)
        root.addWidget(self.tabs, stretch=1)
        self.tabs._on_tab_changed(1)  # Cône par défaut

        ctx = Qt.ShortcutContext.ApplicationShortcut
        QShortcut(QKeySequence("Esc"), self, context=ctx).activated.connect(
            QApplication.quit
        )

    # ── Factories onglets normaux ──────────────────────────────────────────

    def _make_mcu(self) -> QWidget:
        from utils import presentation_config as pc
        from simulations.sim2d.PlotMCU import PlotMCU
        from widgets.SimWidget import SimWidgetMCU
        return SimWidgetMCU(PlotMCU(pc.fresh(pc.MCU)))

    def _make_cone(self) -> QWidget:
        from utils import presentation_config as pc
        from simulations.sim3d.PlotCone import PlotCone
        from widgets.SimWidget import SimWidget3d
        return SimWidget3d(PlotCone(pc.fresh(pc.CONE)))

    def _make_membrane(self) -> QWidget:
        from utils import presentation_config as pc
        from simulations.sim3d.PlotMembrane import PlotMembrane
        from widgets.SimWidget import SimWidget3d
        return SimWidget3d(PlotMembrane(pc.fresh(pc.MEMBRANE)))

    def _make_ml(self) -> QWidget:
        from utils import presentation_config as pc
        from simulations.simML.PlotML import PlotML
        from widgets.SimWidget import SimWidgetML
        return SimWidgetML(PlotML(pc.fresh(pc.ML)))


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def handle_interrupt(signum, frame) -> None:
    log.info("SIGINT reçu — fermeture")
    print("\nFermeture…")
    QApplication.quit()


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--debug",        action="store_true")
    parser.add_argument("--presentation", action="store_true")
    parser.add_argument("--libre",        action="store_true")
    parser.add_argument("--light",        action="store_true")
    args, remaining = parser.parse_known_args()

    setup_logging(debug=args.debug)
    log.info(
        "Démarrage — debug=%s presentation=%s libre=%s light=%s  log=%s",
        args.debug, args.presentation, args.libre, args.light, get_log_path(),
    )

    # Appliquer le thème AVANT toute création de widget.
    # Le mode libre force toujours le thème clair (MD3).
    _ss.set_theme(light=args.light or args.libre)

    app = QApplication(remaining)
    app.setStyleSheet(_ss.APP_STYLESHEET)

    font = QFont(APP_FONT_FAMILY, APP_FONT_PT)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    signal.signal(signal.SIGINT, handle_interrupt)

    window = MainWindow(
        presentation_mode=args.presentation,
        libre_mode=args.libre,
    )
    if args.presentation or args.libre:
        window.showFullScreen()
    else:
        window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
