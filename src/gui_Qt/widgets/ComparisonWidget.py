"""Widget de comparaison côte à côte pour le mode libre.

Permet de placer deux simulations l'une à côté de l'autre avec les
mêmes conditions initiales (ou des conditions distinctes choisies par
l'utilisateur).  Les deux animations tournent en simultané.

Architecture
------------
Deux ``_ComparisonSlot`` (gauche / droite), chacun contenant :
- Un QComboBox pour choisir le type de simulation.
- Un QComboBox pour choisir le scénario dans ce type.
- Le ``plot.widget`` qui occupe tout l'espace restant.

La sélection d'un nouveau scénario recrée le plot correspondant et
relance la préparation en arrière-plan.

Classes publiques
-----------------
ComparisonWidget
    Widget principal : deux slots + barre de contrôle partagée.
"""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from utils import stylesheet as _ss
from utils.ui_constants import (
    MD3_CARD_RADIUS, MD3_CMP_HEADER_H, MD3_CMP_COMBO_H,
)
from utils.ui_strings import (
    MD3_CMP_LAUNCH_BTN, MD3_CMP_STOP_BTN, MD3_CMP_LOADING,
    MD3_CMP_SELECT_SIM, MD3_SCEN_SIM_NAMES,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background worker (même pattern que LibreSimPage)
# ---------------------------------------------------------------------------

class _PrepareWorker(QThread):
    done = Signal()

    def __init__(self, plot) -> None:
        super().__init__()
        self._plot = plot

    def run(self) -> None:
        self._plot._prepare_simulation()
        self.done.emit()


# ---------------------------------------------------------------------------
# _ComparisonSlot — un emplacement (gauche ou droite)
# ---------------------------------------------------------------------------

class _ComparisonSlot(QWidget):
    """Un emplacement de comparaison : sélecteurs + zone de simulation.

    Parameters
    ----------
    scenarios_by_type : dict[str, list]
        Clé = sim_type, valeur = liste de ScenarioConfig.
    label : str
        Libellé affiché dans la barre d'en-tête (ex. « Simulation A »).
    """

    def __init__(self, scenarios_by_type: dict[str, list], label: str) -> None:
        super().__init__()
        self._by_type = scenarios_by_type
        self._plot = None
        self._worker = None
        self._running = False

        self.setStyleSheet(f"background: {_ss.MD3_BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── En-tête ─────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(MD3_CMP_HEADER_H)
        header.setStyleSheet(
            f"background: {_ss.MD3_SURFACE}; "
            f"border-bottom: 1px solid {_ss.MD3_OUTLINE_VAR};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 6, 12, 6)
        hl.setSpacing(10)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: 12px; "
            f"font-weight: 600; background: transparent;"
        )
        hl.addWidget(lbl)

        # Sélecteur de type de simulation
        sim_lbl = QLabel(MD3_CMP_SELECT_SIM)
        sim_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: 12px; background: transparent;"
        )
        hl.addWidget(sim_lbl)

        self._sim_combo = QComboBox()
        self._sim_combo.setFixedHeight(MD3_CMP_COMBO_H)
        self._sim_combo.setStyleSheet(self._combo_style())
        for stype in scenarios_by_type:
            self._sim_combo.addItem(MD3_SCEN_SIM_NAMES.get(stype, stype), stype)
        self._sim_combo.currentIndexChanged.connect(self._on_sim_changed)
        hl.addWidget(self._sim_combo)

        # Sélecteur de scénario
        scen_lbl = QLabel("Scénario :")
        scen_lbl.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: 12px; background: transparent;"
        )
        hl.addWidget(scen_lbl)

        self._scen_combo = QComboBox()
        self._scen_combo.setFixedHeight(MD3_CMP_COMBO_H)
        self._scen_combo.setStyleSheet(self._combo_style())
        self._scen_combo.currentIndexChanged.connect(self._on_scenario_changed)
        hl.addWidget(self._scen_combo, stretch=1)

        root.addWidget(header)

        # ── Zone de simulation (plot + overlay) ────────────────────────
        self._sim_area = QWidget()
        self._sim_area.setStyleSheet("background: #000000;")
        self._grid = QGridLayout(self._sim_area)
        self._grid.setContentsMargins(0, 0, 0, 0)

        self._loading = QWidget()
        self._loading.setStyleSheet("background: rgba(0,0,0,180);")
        _ll = QVBoxLayout(self._loading)
        _ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _lbl = QLabel(MD3_CMP_LOADING)
        _lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _lbl.setStyleSheet("color: #ffffff; font-size: 15px; background: transparent;")
        _ll.addWidget(_lbl)
        self._grid.addWidget(self._loading, 0, 0)
        root.addWidget(self._sim_area, stretch=1)

        # Initialisation avec le premier type et scénario
        self._on_sim_changed(0)

    # ── Style QComboBox ────────────────────────────────────────────────────

    @staticmethod
    def _combo_style() -> str:
        return (
            f"QComboBox {{ background: {_ss.MD3_SURFACE_VAR}; "
            f"color: {_ss.MD3_ON_SURFACE}; "
            f"border: 1px solid {_ss.MD3_OUTLINE}; border-radius: 6px; "
            f"padding: 2px 8px; font-size: 13px; }}"
            f"QComboBox::drop-down {{ border: none; width: 20px; }}"
            f"QComboBox QAbstractItemView {{ background: {_ss.MD3_SURFACE}; "
            f"color: {_ss.MD3_ON_SURFACE}; selection-background-color: {_ss.MD3_PRIMARY_CONT}; }}"
        )

    # ── Gestion des sélecteurs ─────────────────────────────────────────────

    def _on_sim_changed(self, _idx: int) -> None:
        """Met à jour la liste des scénarios quand le type change."""
        stype = self._sim_combo.currentData()
        if stype is None:
            return
        self._scen_combo.blockSignals(True)
        self._scen_combo.clear()
        for sc in self._by_type.get(stype, []):
            self._scen_combo.addItem(sc.title, sc)
        self._scen_combo.blockSignals(False)
        self._load_current_scenario()

    def _on_scenario_changed(self, _idx: int) -> None:
        self._load_current_scenario()

    def _load_current_scenario(self) -> None:
        """Recrée le plot avec le scénario sélectionné."""
        scenario = self._scen_combo.currentData()
        if scenario is None:
            return

        # Arrêter et nettoyer le plot précédent
        if self._plot is not None:
            self._plot.stop_animation()
        if self._worker is not None:
            self._worker.quit()
            self._worker.wait()
            self._worker = None

        # Supprimer l'ancien widget de plot du grid
        for i in range(self._grid.count() - 1, -1, -1):
            item = self._grid.itemAt(i)
            if item and item.widget() is not self._loading:
                w = item.widget()
                self._grid.removeWidget(w)
                w.setParent(None)

        # Créer le nouveau plot
        import dataclasses
        params = dataclasses.replace(scenario.params)
        self._plot = _make_plot(scenario.sim_type, params)
        self._grid.addWidget(self._plot.widget, 0, 0)
        self._loading.raise_()
        self._loading.setVisible(True)
        self._running = False

        # Préparer en arrière-plan
        self._worker = _PrepareWorker(self._plot)
        self._worker.done.connect(self._on_ready)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()
        log.debug(
            "_ComparisonSlot — chargement : %s / %s",
            scenario.sim_type, scenario.title,
        )

    def _on_ready(self) -> None:
        self._plot._prepared = True
        self._plot.current_frame = 0
        self._plot._draw_initial_frame()
        self._loading.setVisible(False)
        self._worker = None
        log.debug("_ComparisonSlot — prêt")

    # ── Contrôle externe ───────────────────────────────────────────────────

    def start(self) -> None:
        """Lance l'animation si le plot est prêt."""
        if self._plot and self._plot._prepared:
            self._plot.stop_animation()
            self._plot.start_animation()
            self._running = True

    def stop(self) -> None:
        """Arrête l'animation."""
        if self._plot:
            self._plot.stop_animation()
            self._running = False


# ---------------------------------------------------------------------------
# Factory plots (même que LibreSimPage)
# ---------------------------------------------------------------------------

def _make_plot(sim_type: str, params) -> object:
    if sim_type == "2d_mcu":
        from simulations.sim2d.PlotMCU import PlotMCU
        return PlotMCU(params)
    elif sim_type == "3d_cone":
        from simulations.sim3d.PlotCone import PlotCone
        return PlotCone(params)
    elif sim_type == "3d_membrane":
        from simulations.sim3d.PlotMembrane import PlotMembrane
        return PlotMembrane(params)
    elif sim_type == "ml":
        from simulations.simML.PlotML import PlotML
        return PlotML(params)
    raise ValueError(f"Type de simulation inconnu : {sim_type!r}")


# ---------------------------------------------------------------------------
# ComparisonWidget — widget principal
# ---------------------------------------------------------------------------

class ComparisonWidget(QWidget):
    """Comparaison côte à côte de deux simulations.

    Affiche deux ``_ComparisonSlot`` séparés par un trait vertical.
    Une barre de contrôle partagée permet de lancer ou arrêter les deux
    simulations simultanément.

    Parameters
    ----------
    scenarios : list[ScenarioConfig]
        Liste complète des scénarios (tous types confondus).
    """

    def __init__(self, scenarios: list) -> None:
        super().__init__()
        self.setStyleSheet(f"background: {_ss.MD3_BG};")

        # Regrouper les scénarios par sim_type
        from utils.libre_config import SIM_TYPE_ORDER
        by_type: dict[str, list] = {t: [] for t in SIM_TYPE_ORDER}
        for sc in scenarios:
            if sc.sim_type in by_type:
                by_type[sc.sim_type].append(sc)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Barre de contrôle partagée
        ctrl_bar = QWidget()
        ctrl_bar.setFixedHeight(52)
        ctrl_bar.setStyleSheet(
            f"background: {_ss.MD3_SURFACE}; "
            f"border-bottom: 1px solid {_ss.MD3_OUTLINE_VAR};"
        )
        cl = QHBoxLayout(ctrl_bar)
        cl.setContentsMargins(16, 8, 16, 8)
        cl.setSpacing(12)

        info = QLabel(
            "Choisissez deux simulations et cliquez Démarrer pour les comparer."
        )
        info.setStyleSheet(
            f"color: {_ss.MD3_ON_SURFACE_VAR}; font-size: 13px; background: transparent;"
        )
        cl.addWidget(info, stretch=1)

        self._launch_btn = QPushButton(MD3_CMP_LAUNCH_BTN)
        self._launch_btn.setFixedHeight(36)
        self._launch_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._launch_btn.setStyleSheet(
            f"QPushButton {{ background: {_ss.MD3_PRIMARY}; color: {_ss.MD3_ON_PRIMARY}; "
            f"border: none; border-radius: 18px; padding: 0 20px; "
            f"font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #1557B0; }}"
        )
        self._launch_btn.clicked.connect(self._toggle)
        cl.addWidget(self._launch_btn)
        root.addWidget(ctrl_bar)

        # Zone à deux colonnes
        cols = QWidget()
        cols_lay = QHBoxLayout(cols)
        cols_lay.setContentsMargins(0, 0, 0, 0)
        cols_lay.setSpacing(0)

        self._slot_a = _ComparisonSlot(by_type, "Simulation A")
        cols_lay.addWidget(self._slot_a, stretch=1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background: {_ss.MD3_OUTLINE_VAR}; border: none; max-width: 2px;")
        cols_lay.addWidget(sep)

        self._slot_b = _ComparisonSlot(by_type, "Simulation B")
        cols_lay.addWidget(self._slot_b, stretch=1)

        root.addWidget(cols, stretch=1)
        self._running = False

    def _toggle(self) -> None:
        if not self._running:
            self._slot_a.start()
            self._slot_b.start()
            self._launch_btn.setText(MD3_CMP_STOP_BTN)
            self._running = True
        else:
            self._slot_a.stop()
            self._slot_b.stop()
            self._launch_btn.setText(MD3_CMP_LAUNCH_BTN)
            self._running = False

    def stop_all(self) -> None:
        """Arrête les deux simulations (appelé quand on quitte la page)."""
        self._slot_a.stop()
        self._slot_b.stop()
        self._running = False
        self._launch_btn.setText(MD3_CMP_LAUNCH_BTN)
