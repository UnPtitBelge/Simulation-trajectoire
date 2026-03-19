"""Gestionnaire de configurations JSON pour le mode présentation.

Chaque simulation possède son propre fichier JSON dans
``configs/presentation/``.  Les valeurs manquantes ou un fichier absent
sont traités proprement avec repli sur les valeurs par défaut du dataclass.

Usage
-----
    from utils.config_manager import load_params, save_params

    params = load_params("cone")       # → SimulationConeParams
    save_params("cone", new_params)    # → configs/presentation/cone.json
"""
from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import Type

from utils.params import (
    SimulationConeParams,
    SimulationMCUParams,
    SimulationMembraneParams,
    SimulationMLParams,
)

log = logging.getLogger(__name__)

# Répertoire contenant les fichiers JSON de configuration.
_CONFIGS_DIR = Path(__file__).parent.parent / "configs" / "presentation"

# Association clé → type dataclass.
_PARAM_TYPES: dict[str, Type] = {
    "mcu":      SimulationMCUParams,
    "cone":     SimulationConeParams,
    "membrane": SimulationMembraneParams,
    "ml":       SimulationMLParams,
}

# Ordre d'affichage standard (correspond aux touches 1-2-3-4).
SIM_KEYS: list[str] = ["mcu", "cone", "membrane", "ml"]


def load_params(sim_key: str) -> object:
    """Charge les paramètres depuis le fichier JSON, avec repli sur les défauts.

    Parameters
    ----------
    sim_key : str
        Clé de simulation : ``"mcu"``, ``"cone"``, ``"membrane"`` ou ``"ml"``.

    Returns
    -------
    object
        Instance fraîche du dataclass correspondant, initialisée avec les
        valeurs du fichier JSON (champs inconnus ignorés).
    """
    cls = _PARAM_TYPES[sim_key]
    path = _CONFIGS_DIR / f"{sim_key}.json"

    if not path.exists():
        log.debug("Pas de config JSON pour %s — valeurs par défaut utilisées", sim_key)
        return cls()

    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        known = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})
    except Exception:
        log.exception("Échec du chargement de la config %s — valeurs par défaut", sim_key)
        return cls()


def save_params(sim_key: str, params: object) -> None:
    """Persiste les paramètres dans le fichier JSON correspondant.

    Crée le répertoire parent si nécessaire.

    Parameters
    ----------
    sim_key : str
        Clé de simulation.
    params : object
        Instance du dataclass à sauvegarder.
    """
    _CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    path = _CONFIGS_DIR / f"{sim_key}.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(dataclasses.asdict(params), fh, indent=2, ensure_ascii=False)
    log.debug("Config sauvegardée → %s", path)
