"""Point d'entrée de l'application.

Au démarrage :
  1. Vérifie que les données de tracking et les 6 modèles synthétiques sont présents.
  2. Entraîne les modèles "réels" en mémoire depuis tracking_data.csv.
  3. Lance la fenêtre principale.

Usage :
    python src/app.py
"""

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from config.theme import STYLESHEET
from ml.models import LinearStepModel, MLPStepModel, N_FEATURES
from ml.train import train_real
from ui.main_window import MainWindow

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger(__name__)

def _load_configs() -> dict:
    """Charge les 4 configs TOML fusionnées avec common.toml."""
    return {name: load_config(name) for name in ("mcu", "cone", "membrane", "ml")}


def _check_prerequisites(cfg: dict) -> tuple[list[str], list[str]]:
    """Retourne (manquants, incompatibles) — fichiers absents ou avec N_FEATURES obsolète."""
    missing:      list[str] = []
    incompatible: list[str] = []

    tracking = ROOT / cfg["ml"]["paths"]["tracking_data"]
    if not tracking.exists():
        missing.append(str(tracking))

    models_dir = ROOT / cfg["ml"]["paths"]["models_dir"]
    ctx_names  = cfg["ml"]["synth"]["contexts"]["names"]
    for ctx in ctx_names:
        for algo in ("linear", "mlp"):
            p = models_dir / f"synth_{algo}_{ctx}.pkl"
            if not p.exists():
                missing.append(str(p))
                continue
            try:
                m = (LinearStepModel if algo == "linear" else MLPStepModel).load(p)
                n = getattr(m.scaler_X, "n_features_in_", None)
                if n is not None and n != N_FEATURES:
                    incompatible.append(f"{p.name}  ({n} features → attendu {N_FEATURES})")
            except Exception as exc:
                incompatible.append(f"{p.name}  (erreur chargement : {exc})")

    return missing, incompatible


def _check_config_consistency(configs: dict) -> None:
    """Vérifie que les constantes partagées entre configs sont cohérentes."""
    cone_depth = configs["cone"]["physics"]["depth"]
    ml_depth   = configs["ml"]["synth"]["physics"]["depth"]
    assert cone_depth == ml_depth, (
        f"Incohérence de config : cone.toml physics.depth={cone_depth} "
        f"≠ ml.toml synth.physics.depth={ml_depth} — "
        "les modèles ML seraient entraînés sur un cône différent de celui simulé"
    )


def main():
    configs = _load_configs()
    _check_config_consistency(configs)
    missing, incompatible = _check_prerequisites(configs)

    if missing or incompatible:
        app = QApplication(sys.argv)
        body = ""
        if missing:
            body += "Fichiers manquants :\n" + "\n".join(f"  {f}" for f in missing) + "\n\n"
        if incompatible:
            body += "Modèles incompatibles (N_FEATURES obsolète) :\n"
            body += "\n".join(f"  {f}" for f in incompatible) + "\n\n"
        body += (
            "Pour régénérer :\n"
            "  python src/scripts/generate_data.py\n"
            "  python src/scripts/train_models.py"
        )
        QMessageBox.critical(None, "Prérequis manquants", body)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # Entraînement rapide sur les données réelles (en mémoire)
    tracking_path = ROOT / configs["ml"]["paths"]["tracking_data"]
    log.info("Entraînement des modèles réels depuis %s ...", tracking_path)
    n_passes = configs["ml"]["tracking"]["n_passes"]
    lr_real, mlp_real = train_real(tracking_path, configs["ml"]["tracking"], n_passes=n_passes)
    log.info("Modèles réels prêts.")

    real_models = {"linear": lr_real, "mlp": mlp_real}
    window = MainWindow(configs, real_models)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
