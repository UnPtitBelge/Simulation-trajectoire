"""Application entry point and launch logic."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QProgressDialog

from src.ui import MainWindow
from src.ui.modes import LibreMode, NormalMode, PresentationMode
from src.utils.logger import setup_logger
from src.utils.theme import apply_theme

_MODES = {
    "normal": NormalMode,
    "presentation": PresentationMode,
    "libre": LibreMode,
}


def _ensure_synthetic_pool(qt_app) -> None:
    """Génère le pool synthétique (100 000 trajectoires) si absent ou incomplet.

    Affiche une QProgressDialog pendant la génération (~10-15 min première fois).
    Les démarrages suivants sont instantanés (fichier .npz déjà présent).
    """
    from src.simulations.sim_to_real import (
        _POOL_SIZE, _SYNTHETIC_NPZ, generate_and_save_pool, pool_is_ready,
    )

    if pool_is_ready(_SYNTHETIC_NPZ, min_n=_POOL_SIZE):
        return

    dlg = QProgressDialog(
        f"Génération du dataset synthétique ({_POOL_SIZE:,} trajectoires)…\n"
        "Cette opération n'a lieu qu'une seule fois.",
        "",            # pas de bouton Annuler (chaîne vide)
        0, _POOL_SIZE,
    )
    dlg.setCancelButton(None)  # supprime vraiment le bouton
    dlg.setWindowTitle("Simulation Trajectoire — Initialisation")
    dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
    dlg.setMinimumWidth(480)
    dlg.setMinimumDuration(0)
    dlg.setValue(0)
    dlg.show()

    def _cb(current: int, total: int) -> None:
        dlg.setValue(current)
        dlg.setLabelText(
            f"Génération du dataset synthétique…\n"
            f"{current:,} / {total:,} trajectoires"
        )
        qt_app.processEvents()

    generate_and_save_pool(progress_cb=_cb)
    dlg.close()


def _ensure_presets(qt_app) -> None:
    """Pré-calcule les 6 presets (3 n_sims × RL/MLP) + sauvegarde les 12 modèles si absents.

    Nécessite que le pool soit déjà prêt (appeler après _ensure_synthetic_pool).
    Chaque preset = entraînement + prédiction sur CI nominale (~2-5 min totaux).
    Les modèles sklearn sont sauvegardés pour chargement instantané au démarrage.
    """
    from src.simulations.sim_to_real import (
        compute_and_save_presets, presets_are_ready, models_are_ready, _PRESET_N_SIMS,
    )

    # Vérifier si les presets ET les modèles sont déjà prêts
    if presets_are_ready() and models_are_ready():
        return

    n_steps = len(_PRESET_N_SIMS)
    dlg = QProgressDialog(
        "Pré-calcul des presets de comparaison…",
        "",
        0, n_steps,
    )
    dlg.setCancelButton(None)
    dlg.setWindowTitle("Simulation Trajectoire — Initialisation")
    dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
    dlg.setMinimumWidth(480)
    dlg.setMinimumDuration(0)
    dlg.setValue(0)
    dlg.show()

    def _cb(current: int, total: int, msg: str = "") -> None:
        dlg.setValue(current)
        if msg:
            dlg.setLabelText(f"Pré-calcul des presets…\n{msg}")
        qt_app.processEvents()

    compute_and_save_presets(progress_cb=_cb)
    dlg.close()


class MainApplication:
    def __init__(self, mode: str = "normal"):
        self.qt_app = QApplication.instance() or QApplication([])
        self.mode = mode
        self.logger = setup_logger()
        apply_theme(self.qt_app)

        # Génération des données si nécessaire (première utilisation)
        _ensure_synthetic_pool(self.qt_app)
        _ensure_presets(self.qt_app)
        
        # Chargement des modèles en mémoire pour accès instantané
        self._load_models_into_memory()

        self.window = MainWindow()
        self.logger.info("Starting app mode=%s", mode)
    
    def _load_models_into_memory(self):
        """Charge les modèles ML en mémoire au démarrage pour prédictions instantanées."""
        from src.simulations.sim_to_real import load_trained_models, set_cached_models
        
        models = load_trained_models()
        if models:
            set_cached_models(models)
            self.logger.info("✅ Modèles ML chargés en mémoire : %d configs", len(models))
        else:
            self.logger.warning("⚠️  Modèles ML non disponibles")

    def run(self):
        mode_cls = _MODES.get(self.mode, NormalMode)
        mode_cls().apply(self.window)
        self.qt_app.exec()
