"""Base parameter class with common functionality."""

from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass
class BaseParams:
    """Base class for all simulation parameters with common functionality."""

    PRESETS: ClassVar[dict[str, Any]] = {}
    # Controls shown in the param panel: {field: {label, min, max, step}}
    # Empty by default — each concrete class overrides with its physics fields.
    PARAM_RANGES: ClassVar[dict[str, dict]] = {}

    @classmethod
    def from_preset(cls, name: str) -> Any:
        """Create parameter instance from a preset configuration."""
        presets = cls.PRESETS
        if name not in presets:
            raise ValueError(f"Preset '{name}' not found for {cls.__name__}")
        p = presets[name]
        init_params = {k: v for k, v in p.items() if k in cls.__dataclass_fields__}
        return cls(**init_params)
