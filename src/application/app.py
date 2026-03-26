"""Application entry point and launch logic."""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QProgressDialog

from src.ui import MainWindow
from src.ui.modes import PresentationMode
from src.utils.logging import setup_logger
from src.utils.theme import apply_theme

log = logging.getLogger(__name__)



def _ensure_synthetic_pool(qt_app) -> None:
    """Vérifie que le pool synthétique existe (sans génération automatique)."""
    from src.core.ml.data_utils import pool_is_ready, _SYNTHETIC_NPZ
    
    if not pool_is_ready(_SYNTHETIC_NPZ):
        log.error("Dataset synthétique manquant : %s", _SYNTHETIC_NPZ)
        raise RuntimeError(
            f"Dataset synthétique manquant : {_SYNTHETIC_NPZ}\n"
            "Veuillez générer les données avant de lancer l'application."
        )
    
    log.info("Dataset synthétique vérifié : %s", _SYNTHETIC_NPZ)


def _ensure_presets(qt_app) -> None:
    """Vérifie que les presets et modèles sont prêts (sans génération automatique).

    Nécessite que le pool soit déjà prêt (appeler après _ensure_synthetic_pool).
    """
    from src.core.ml.preset_utils import presets_are_ready
    from src.core.ml.model_utils import models_are_ready
    
    # Vérifier si les presets ET les modèles sont déjà prêts
    if presets_are_ready() and models_are_ready():
        log.info("Presets et modèles ML vérifiés et prêts")
        return
    
    log.error("Presets ou modèles ML manquants")
    raise RuntimeError(
        "Presets ou modèles ML manquants.\n"
        "Veuillez générer les données avant de lancer l'application."
    )


class MainApplication:
    def __init__(self):
        self.qt_app = QApplication.instance() or QApplication([])
        self.logger = setup_logger()
        apply_theme(self.qt_app)

        # Vérification des données (sans génération automatique)
        _ensure_synthetic_pool(self.qt_app)
        _ensure_presets(self.qt_app)

        # Chargement des modèles en mémoire pour accès instantané
        self._load_models_into_memory()

        self.window = MainWindow()
        self.logger.info("Starting app in presentation mode")
    
    def _load_models_into_memory(self):
        """Charge les modèles ML en mémoire au démarrage pour prédictions instantanées."""
        from src.core.ml.model_utils import load_trained_models, set_cached_models
        
        models = load_trained_models()
        if models:
            set_cached_models(models)
            log.info("✅ Modèles ML chargés en mémoire : %d configs", len(models))
        else:
            log.warning("⚠️  Modèles ML non disponibles")

    def run(self):
        PresentationMode().apply(self.window)
        self.qt_app.exec()
