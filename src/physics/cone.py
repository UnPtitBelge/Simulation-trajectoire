"""Simulation physique du cône — trois intégrateurs au choix.

Intégrateurs disponibles via le paramètre ``method`` :
  "euler"        — Euler explicite (ordre 1) : position mise à jour avec
                   l'ancienne vitesse. Instable à grand dt.
  "euler_cromer" — Euler-Cromer / semi-implicite (ordre 1) : vitesse mise
                   à jour en premier, position avec la nouvelle vitesse.
                   Conserve mieux l'énergie que l'Euler explicite.
  "rk4"          — Runge-Kutta d'ordre 4 : 4 évaluations de f par pas,
                   erreur locale en O(dt⁵), erreur globale en O(dt⁴).
                   4× plus coûteux que les méthodes d'ordre 1.

Surface : z(r) = slope * (r - R_centre),  slope = depth / R
Bille glissante (pas de roulement).
Coordonnées polaires : état = (r, θ, vr, vθ) où vθ = r * dθ/dt.

Équations du mouvement (Newton en coordonnées polaires, bille glissante) :
  dr/dt    = vr
  dθ/dt    = vθ / r
  dvr/dt   = +vθ²/r  -  g·sin(α)  -  μ·g·cos(α)·vr/|v|
  dvθ/dt   = -vr·vθ/r  -  μ·g·cos(α)·vθ/|v|
"""

import numpy as np


def _derivatives(
    r: float, theta: float, vr: float, vtheta: float,
    r_min: float, g_radial: float, g_friction: float,
) -> tuple[float, float, float, float]:
    """Dérivées (dr/dt, dθ/dt, dvr/dt, dvθ/dt) aux coordonnées polaires.

    Utilisée par l'intégrateur RK4 pour les 4 évaluations intermédiaires.
    Le frottement de Coulomb s'annule quand |v| → 0 (régime statique géré
    séparément dans la boucle principale via le snap-to-zero).
    """
    cr = max(r, r_min)
    speed = np.sqrt(vr ** 2 + vtheta ** 2)
    if speed > 0:
        ar = vtheta ** 2 / cr + g_radial - g_friction * vr     / speed
        at =  -vr * vtheta  / cr         - g_friction * vtheta / speed
    elif abs(g_radial) > g_friction:
        # Frottement statique dépassé : la bille glisse radialement vers le bas
        ar, at = g_radial + g_friction, 0.0
    else:
        # Frottement statique tient : la bille reste immobile
        ar, at = 0.0, 0.0
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
) -> np.ndarray:
    """Retourne array (n_steps, 4) : colonnes = r, θ, vr, vθ.

    Paramètres
    ----------
    method : {"euler_cromer", "euler", "rk4"}
        Intégrateur à utiliser. Par défaut "euler_cromer" (semi-implicite,
        bon compromis stabilité/coût). "rk4" est plus précis mais 4× plus
        coûteux. "euler" sert de référence inférieure pour les benchmarks.

    Arrêt anticipé si r ≥ R (sortie du cône), r ≤ center_radius (collision),
    ou |v| = 0 (bille arrêtée par frottement).
    """
    slope = depth / R
    slope_angle = np.arctan(slope)
    g_radial  = -g * np.sin(slope_angle)          # gravité le long du cône (constante)
    g_friction = friction * g * np.cos(slope_angle)  # amplitude frottement Coulomb

    r_min = center_radius

    traj = np.empty((n_steps, 4))
    r, theta, vr, vtheta = r0, theta0, vr0, vtheta0

    for i in range(n_steps):
        traj[i] = (r, theta, vr, vtheta)

        if method == "rk4":
            # ── Runge-Kutta d'ordre 4 ─────────────────────────────────────────
            # 4 évaluations de f = (dr/dt, dθ/dt, dvr/dt, dvθ/dt)
            k1 = _derivatives(r,                     theta,                     vr,                     vtheta,                     r_min, g_radial, g_friction)
            k2 = _derivatives(r + .5*dt*k1[0],       theta + .5*dt*k1[1],       vr + .5*dt*k1[2],       vtheta + .5*dt*k1[3],       r_min, g_radial, g_friction)
            k3 = _derivatives(r + .5*dt*k2[0],       theta + .5*dt*k2[1],       vr + .5*dt*k2[2],       vtheta + .5*dt*k2[3],       r_min, g_radial, g_friction)
            k4 = _derivatives(r +    dt*k3[0],        theta +    dt*k3[1],        vr +    dt*k3[2],        vtheta +    dt*k3[3],        r_min, g_radial, g_friction)
            r      += dt / 6 * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
            theta  += dt / 6 * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
            vr     += dt / 6 * (k1[2] + 2*k2[2] + 2*k3[2] + k4[2])
            vtheta += dt / 6 * (k1[3] + 2*k2[3] + 2*k3[3] + k4[3])
            # Snap-to-zero post-mise à jour
            if np.sqrt(vr**2 + vtheta**2) < g_friction * dt and abs(g_radial) <= g_friction:
                vr = vtheta = 0.0

        else:
            # ── Euler explicite et Euler-Cromer ───────────────────────────────
            # Calcul des accélérations (identique pour les deux variantes)
            curr  = max(r, r_min)
            speed = np.sqrt(vr ** 2 + vtheta ** 2)
            if speed > 0:
                ar = vtheta ** 2 / curr + g_radial - g_friction * vr     / speed
                at =  -vr * vtheta / curr           - g_friction * vtheta / speed
            elif abs(g_radial) > g_friction:
                ar, at = g_radial + g_friction, 0.0
            else:
                ar, at = 0.0, 0.0

            if method == "euler":
                # Position mise à jour avec l'ANCIENNE vitesse (Forward Euler)
                r     += dt * vr
                theta += dt * vtheta / curr
                vr    += dt * ar
                vtheta += dt * at
                # Snap-to-zero après mise à jour complète
                if np.sqrt(vr**2 + vtheta**2) < g_friction * dt and abs(g_radial) <= g_friction:
                    vr = vtheta = 0.0

            elif method == "euler_cromer":
                # Vitesse mise à jour EN PREMIER, puis position avec la nouvelle vitesse
                vr     += dt * ar
                vtheta += dt * at
                # Snap-to-zero entre vitesse et position (conserve la cohérence
                # de la condition d'arrêt avec l'état qui sera enregistré au prochain pas)
                if np.sqrt(vr**2 + vtheta**2) < g_friction * dt and abs(g_radial) <= g_friction:
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
