"""Chargement des configs TOML avec fusion depuis common.toml.

Stratégie de fusion (depth=1) :
  - Pour chaque clé de l'override dont la valeur est un dict :
      result[key] = {**common[key], **override[key]}   ← merge superficiel
  - Sinon : result[key] = override[key]                ← remplacement direct

Conséquences :
  - [physics] : les clés de l'override s'ajoutent/écrasent common, le reste
    de common est conservé (ex. cone ajoute depth=0.09 sans perdre R, g…)
  - [preset] : si l'override redéfinit [preset], ses sub-tables (default/1/2)
    remplacent entièrement celles de common (ex. mcu a ses propres presets)
  - [ranges] : idem — les clés de l'override s'ajoutent à celles de common,
    mais comme ControlsPanel itère les clés du preset (pas de ranges),
    les clés supplémentaires ne génèrent pas de spinboxes inutiles.
"""

import tomllib
from pathlib import Path

_CONFIG_DIR = Path(__file__).resolve().parent


def _merge(base: dict, override: dict) -> dict:
    """Fusionne override dans base (depth=1)."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = {**result[key], **val}
        else:
            result[key] = val
    return result


def load_config(name: str) -> dict:
    """Charge common.toml puis le fusionne avec <name>.toml."""
    with open(_CONFIG_DIR / "common.toml", "rb") as f:
        common = tomllib.load(f)
    with open(_CONFIG_DIR / f"{name}.toml", "rb") as f:
        specific = tomllib.load(f)
    return _merge(common, specific)
