"""Simulation physique du cône — trois intégrateurs, trois niveaux de précision.

Intégrateurs disponibles via le paramètre ``method`` :
  "euler"        — Euler explicite (ordre 1) : position mise à jour avec
                   l'ancienne vitesse. Instable à grand dt.
  "euler_cromer" — Euler-Cromer / semi-implicite (ordre 1) : vitesse mise
                   à jour en premier, position avec la nouvelle vitesse.
                   Conserve mieux l'énergie que l'Euler explicite.
  "rk4"          — Runge-Kutta d'ordre 4 : 4 évaluations de f par pas,
                   erreur locale en O(dt⁵), erreur globale en O(dt⁴).
                   4× plus coûteux que les méthodes d'ordre 1.

Niveaux de précision physique (combinables) :
  Niveau 0 — Glissement (défaut) : frottement de Coulomb cinétique μ constant.
  Niveau 1 — Roulement pur (rolling=True) : facteur de masse effective f=5/7
             (sphère pleine, I=2/5·m·r²), pas de terme de Coulomb.
  Niveau 2 — Roulement + résistance au roulement (rolling_resistance > 0) :
             force μ_r·m·g·cos(α), beaucoup plus faible que le Coulomb.
             Valeurs typiques : 0.001–0.005 vs μ ≈ 0.01–0.05.
  Niveau 3 — + Traînée aérodynamique (drag_coeff > 0) :
             force k·|v|², avec k = ρ_air·C_d·A/(2m).

Surface : z(r) = slope * (r - R_centre),  slope = depth / R
Coordonnées polaires : état = (r, θ, vr, vθ) où vθ = r * dθ/dt.

Équations du mouvement — bille glissante (Niveau 0) :
  dvr/dt   = +vθ²/r  -  g·sin(α)  -  μ·g·cos(α)·vr/|v|
  dvθ/dt   = -vr·vθ/r  -  μ·g·cos(α)·vθ/|v|

Équations du mouvement — roulement pur (Niveau 1, rolling_factor f=5/7) :
  dvr/dt   = (vθ²/r  -  g·sin(α)) · f
  dvθ/dt   = (-vr·vθ/r) · f
"""

import numpy as np

# Facteur de masse effective pour une sphère pleine en roulement pur.
# Dérivé de I = 2/5·m·r²  →  (1 + I/(m·r²))⁻¹ = 1/(1 + 2/5) = 5/7.
_ROLLING_FACTOR = 5.0 / 7.0


def _derivatives(
    r: float, theta: float, vr: float, vtheta: float,
    r_min: float, g_radial: float, g_friction: float,
    rolling: bool = False,
    rolling_resistance_force: float = 0.0,
    drag_coeff: float = 0.0,
) -> tuple[float, float, float, float]:
    """Dérivées (dr/dt, dθ/dt, dvr/dt, dvθ/dt) aux coordonnées polaires.

    Utilisée par l'intégrateur RK4 pour les 4 évaluations intermédiaires.
    ``rolling_resistance_force`` doit être préconverti en accélération
    (= rolling_resistance * g * cos(α)), de même que ``g_friction``.
    """
    cr = max(r, r_min)
    speed = np.sqrt(vr ** 2 + vtheta ** 2)
    ar_cent = vtheta ** 2 / cr + g_radial   # centrifuge + gravité radiale
    at_cor  = -vr * vtheta / cr             # correction de Coriolis (dvθ/dt)

    if rolling:
        if speed > 0:
            ar = ar_cent * _ROLLING_FACTOR
            at = at_cor  * _ROLLING_FACTOR
            if rolling_resistance_force > 0:
                ar -= rolling_resistance_force * vr     / speed
                at -= rolling_resistance_force * vtheta / speed
        else:
            # Repos : démarre si la gravité dépasse la résistance statique
            if abs(g_radial) * _ROLLING_FACTOR > rolling_resistance_force:
                ar = g_radial * _ROLLING_FACTOR
                at = 0.0
            else:
                ar = at = 0.0
    else:
        # Glissement — frottement de Coulomb
        if speed > 0:
            ar = ar_cent - g_friction * vr     / speed
            at = at_cor  - g_friction * vtheta / speed
        elif abs(g_radial) > g_friction:
            ar, at = g_radial + g_friction, 0.0
        else:
            ar, at = 0.0, 0.0

    # Traînée aérodynamique (quadratique en vitesse)
    if drag_coeff > 0.0 and speed > 0.0:
        ar -= drag_coeff * speed * vr
        at -= drag_coeff * speed * vtheta

    return vr, vtheta / cr, ar, at


def compute_cone(
    r0: float,
    theta0: float,
    vr0: float,
    vtheta0: float,
    R: float,
    depth: float,
    friction: float,
    g: float,
    dt: float,
    n_steps: int,
    center_radius: float = 0.03,
    method: str = "euler_cromer",
    rolling: bool = False,
    rolling_resistance: float = 0.0,
    drag_coeff: float = 0.0,
) -> np.ndarray:
    """Retourne array (n_steps, 4) : colonnes = r, θ, vr, vθ.

    Paramètres
    ----------
    method : {"euler_cromer", "euler", "rk4"}
        Intégrateur à utiliser.
    rolling : bool
        True → roulement pur (f=5/7). False → glissement Coulomb.
    rolling_resistance : float
        Coefficient de résistance au roulement μ_r (sans unité, ≈ 0.001–0.005).
        Ignoré si rolling=False.
    drag_coeff : float
        Coefficient de traînée aérodynamique k = ρ·C_d·A/(2m) (m⁻¹).
        S'applique à tous les modes.

    Arrêt anticipé si r ≥ R (sortie), r ≤ center_radius (collision),
    ou |v| = 0 (bille arrêtée).
    """
    slope       = depth / R
    slope_angle = np.arctan(slope)
    cos_alpha   = np.cos(slope_angle)               # = 1/√(1+slope²)
    g_radial    = -g * np.sin(slope_angle)          # gravité radiale (constante)
    g_friction  = friction * g * cos_alpha          # amplitude Coulomb (glissement)

    # Préconversion : rolling_resistance exprimé en accélération (m/s²)
    rolling_resistance_force = rolling_resistance * g * cos_alpha

    # Seuil d'arrêt : force de freinage pertinente selon le mode
    decel_force = rolling_resistance_force if rolling else g_friction
    # La bille peut rester immobile si la gravité ne dépasse pas la force de freinage
    can_stop_fn = (
        (lambda: abs(g_radial) * _ROLLING_FACTOR <= rolling_resistance_force)
        if rolling
        else (lambda: abs(g_radial) <= g_friction)
    )

    r_min = center_radius

    # Arguments supplémentaires passés à _derivatives (identiques à tous les appels RK4)
    _extra = dict(
        rolling=rolling,
        rolling_resistance_force=rolling_resistance_force,
        drag_coeff=drag_coeff,
    )

    traj = np.empty((n_steps, 4))
    r, theta, vr, vtheta = r0, theta0, vr0, vtheta0

    for i in range(n_steps):
        traj[i] = (r, theta, vr, vtheta)

        if method == "rk4":
            # ── Runge-Kutta d'ordre 4 ─────────────────────────────────────────
            k1 = _derivatives(r,                   theta,                   vr,                   vtheta,                   r_min, g_radial, g_friction, **_extra)
            k2 = _derivatives(r + .5*dt*k1[0],     theta + .5*dt*k1[1],     vr + .5*dt*k1[2],     vtheta + .5*dt*k1[3],     r_min, g_radial, g_friction, **_extra)
            k3 = _derivatives(r + .5*dt*k2[0],     theta + .5*dt*k2[1],     vr + .5*dt*k2[2],     vtheta + .5*dt*k2[3],     r_min, g_radial, g_friction, **_extra)
            k4 = _derivatives(r +    dt*k3[0],      theta +    dt*k3[1],      vr +    dt*k3[2],      vtheta +    dt*k3[3],      r_min, g_radial, g_friction, **_extra)
            r      += dt / 6 * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
            theta  += dt / 6 * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
            vr     += dt / 6 * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
            vtheta += dt / 6 * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])
            speed = np.sqrt(vr**2 + vtheta**2)
            if speed < decel_force * dt and can_stop_fn():
                vr = vtheta = 0.0

        else:
            # ── Euler explicite et Euler-Cromer ───────────────────────────────
            curr  = max(r, r_min)
            speed = np.sqrt(vr ** 2 + vtheta ** 2)

            _, _, ar, at = _derivatives(r, theta, vr, vtheta,
                                        r_min, g_radial, g_friction, **_extra)

            if method == "euler":
                r      += dt * vr
                theta  += dt * vtheta / curr
                vr     += dt * ar
                vtheta += dt * at
                speed2 = np.sqrt(vr**2 + vtheta**2)
                if speed2 < decel_force * dt and can_stop_fn():
                    vr = vtheta = 0.0

            elif method == "euler_cromer":
                vr     += dt * ar
                vtheta += dt * at
                speed2 = np.sqrt(vr**2 + vtheta**2)
                if speed2 < decel_force * dt and can_stop_fn():
                    vr = vtheta = 0.0
                r     += dt * vr
                theta += dt * vtheta / curr

            else:
                raise ValueError(
                    f"Intégrateur inconnu : {method!r} — "
                    "choisir 'euler', 'euler_cromer' ou 'rk4'"
                )

        if r >= R or r <= r_min:
            return traj[:i + 1]

        if np.sqrt(vr ** 2 + vtheta ** 2) == 0.0:
            return traj[:i + 1]

    return traj
