"""Simulation physique de la membrane — trois niveaux de précision physique.

Intégrateur : Euler-Cromer (semi-implicite, ordre 1).

Niveaux de précision physique (combinables) :
  Niveau 0 — Glissement (défaut) : frottement de Coulomb cinétique μ.
             La normale N = m·g·cos(β(r)) varie avec r (pente locale).
  Niveau 1 — Roulement pur (rolling=True) : facteur de masse effective f=5/7,
             pas de Coulomb. La bille roule sans glisser.
  Niveau 2 — Roulement + résistance au roulement (rolling_resistance > 0) :
             force μ_r·m·g·cos(β(r)) — variable avec r comme la normale.
  Niveau 3 — + Traînée aérodynamique (drag_coeff > 0) : k·|v|².

Surface : z(r) = k · ln(r/R),  k = F/(2πT)
La surface est concave (bord le plus haut, centre le plus bas).
Coordonnées polaires : état = (r, θ, vr, vθ) où vθ = r * dθ/dt.

Équations du mouvement — bille glissante (Niveau 0) :
  dvr/dt = +vθ²/r  -  g·(k/r)/√(1+(k/r)²)  -  μ·g/√(1+(k/r)²)·vr/|v|
  dvθ/dt = -vr·vθ/r  -  μ·g/√(1+(k/r)²)·vθ/|v|

Note : cos(β(r)) = 1/√(1+(k/r)²) varie avec r, contrairement au cône.
"""

import numpy as np

# Facteur de masse effective pour sphère pleine en roulement pur : f = 5/7
_ROLLING_FACTOR = 5.0 / 7.0


def compute_membrane(
    r0: float,
    theta0: float,
    vr0: float,
    vtheta0: float,
    R: float,
    k: float,
    r_min: float,
    friction: float,
    g: float,
    dt: float,
    n_steps: int,
    center_radius: float = 0.03,
    rolling: bool = False,
    rolling_resistance: float = 0.0,
    drag_coeff: float = 0.0,
) -> np.ndarray:
    """Retourne array (n_steps, 4) : colonnes = r, θ, vr, vθ.

    Paramètres
    ----------
    rolling : bool
        True → roulement pur (f=5/7). False → glissement Coulomb.
    rolling_resistance : float
        Coefficient de résistance au roulement μ_r (≈ 0.001–0.005).
        Ignoré si rolling=False. La force est μ_r·g·cos(β(r)) (variable avec r).
    drag_coeff : float
        Coefficient de traînée k = ρ·C_d·A/(2m) (m⁻¹). Tous modes.

    ``r_min`` doit être ≥ center_radius pour éviter la collision centrale.
    """
    assert center_radius > 0, f"center_radius doit être > 0, reçu {center_radius}"
    assert r_min <= R, f"r_min ({r_min}) doit être ≤ R ({R})"
    traj = np.empty((n_steps, 4))
    r, theta, vr, vtheta = r0, theta0, vr0, vtheta0
    r_min = max(r_min, center_radius)

    for i in range(n_steps):
        traj[i] = (r, theta, vr, vtheta)

        current_r   = max(r, r_min)
        local_slope = k / current_r
        inv_norm    = 1.0 / np.sqrt(1.0 + local_slope ** 2)  # cos(β(r))

        # Gravité radiale : -g·sin(β) = -g·(k/r)·cos(β)
        a_gravity = -g * local_slope * inv_norm

        # Forces de freinage — toutes dépendent de cos(β(r)) = inv_norm
        g_friction              = friction          * g * inv_norm  # Coulomb (glissement)
        rolling_resistance_force = rolling_resistance * g * inv_norm  # résistance roulement

        speed = np.sqrt(vr ** 2 + vtheta ** 2)
        ar_cent = vtheta ** 2 / current_r + a_gravity
        at_cor  = -vr * vtheta / current_r

        if rolling:
            if speed > 0:
                ar = ar_cent * _ROLLING_FACTOR
                at = at_cor  * _ROLLING_FACTOR
                if rolling_resistance_force > 0:
                    ar -= rolling_resistance_force * vr     / speed
                    at -= rolling_resistance_force * vtheta / speed
            else:
                if abs(a_gravity) * _ROLLING_FACTOR > rolling_resistance_force:
                    ar = a_gravity * _ROLLING_FACTOR
                    at = 0.0
                else:
                    ar = at = 0.0
        else:
            # Glissement — frottement de Coulomb
            if speed > 0:
                ar = ar_cent - g_friction * vr     / speed
                at = at_cor  - g_friction * vtheta / speed
            elif abs(a_gravity) > g_friction:
                ar = a_gravity + g_friction   # friction s'oppose au mouvement inward
                at = 0.0
            else:
                ar = at = 0.0

        # Traînée aérodynamique
        if drag_coeff > 0.0 and speed > 0.0:
            ar -= drag_coeff * speed * vr
            at -= drag_coeff * speed * vtheta

        vr     += dt * ar
        vtheta += dt * at

        # Snap-to-zero
        decel_force = rolling_resistance_force if rolling else g_friction
        gravity_ref = a_gravity
        if rolling:
            can_stop = abs(gravity_ref) * _ROLLING_FACTOR <= rolling_resistance_force
        else:
            can_stop = abs(gravity_ref) <= g_friction
        if np.sqrt(vr ** 2 + vtheta ** 2) < decel_force * dt and can_stop:
            vr = vtheta = 0.0

        r     += dt * vr
        theta += dt * vtheta / current_r

        if r >= R or r <= r_min:
            return traj[:i + 1]

        if np.sqrt(vr ** 2 + vtheta ** 2) == 0.0:
            return traj[:i + 1]

    return traj
