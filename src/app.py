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

import tomllib
from PySide6.QtWidgets import QApplication, QMessageBox

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config.theme import STYLESHEET
from ml.train import train_real
from ui.main_window import MainWindow

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger(__name__)

def _load_configs() -> dict:
    """Charge les 4 fichiers TOML de config."""
    config_dir = ROOT / "config"
    configs = {}
    for name in ("mcu", "cone", "membrane", "ml"):
        with open(config_dir / f"{name}.toml", "rb") as f:
            configs[name] = tomllib.load(f)
    return configs


def _check_prerequisites(cfg: dict) -> list[str]:
    """Retourne la liste des fichiers manquants."""
    missing = []

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

    return missing


def main():
    configs = _load_configs()
    missing = _check_prerequisites(configs)

    if missing:
        app = QApplication(sys.argv)
        msg = "\n".join(missing)
        QMessageBox.critical(
            None,
            "Fichiers manquants",
            f"Les fichiers suivants sont requis avant de lancer l'application :\n\n{msg}\n\n"
            "Générez les données : python src/scripts/generate_data.py\n"
            "Entraînez les modèles : python src/scripts/train_models.py",
        )
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # Entraînement rapide sur les données réelles (en mémoire)
    tracking_path = ROOT / configs["ml"]["paths"]["tracking_data"]
    log.info("Entraînement des modèles réels depuis %s ...", tracking_path)
    lr_real, mlp_real = train_real(tracking_path, configs["ml"]["tracking"])
    log.info("Modèles réels prêts.")

    real_models = {"linear": lr_real, "mlp": mlp_real}
    window = MainWindow(configs, real_models)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
