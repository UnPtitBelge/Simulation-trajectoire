"""Conversions d'angles — degrés ↔ radians, et CI vitesse."""

import math


def deg_to_rad(deg: float) -> float:
    """Convertit un angle en degrés vers radians."""
    return deg * math.pi / 180.0


def rad_to_deg(rad: float) -> float:
    """Convertit un angle en radians vers degrés."""
    return rad * 180.0 / math.pi


def v0_dir_to_vr_vtheta(v0: float, direction_deg: float) -> tuple[float, float]:
    """Convertit (v0, direction) en composantes polaires (vr, vθ).

    Convention :
        0°   → purement tangentiel (sens trigonométrique) : vr=0,   vθ=+v0
        90°  → purement radial sortant                    : vr=+v0,  vθ=0
        180° → purement tangentiel (sens horaire)         : vr=0,   vθ=-v0
        -90° → purement radial entrant                    : vr=-v0, vθ=0

    Retourne (vr, vθ).
    """
    rad = deg_to_rad(direction_deg)
    return v0 * math.sin(rad), v0 * math.cos(rad)
