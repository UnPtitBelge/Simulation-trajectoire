"""Typed simulation keys — single source of truth for sim identifiers."""

from enum import StrEnum


class SimKey(StrEnum):
    MCU = "mcu"
    CONE = "cone"
    MEMBRANE = "membrane"
    ML = "ml"
