"""
Intégration numérique du mouvement lagrangien d'une masse sur une surface de révolution.

Système : coordonnées généralisées (r, θ), avec contrainte z = z(r) connue.
État    : q = (r, θ, r_dot, θ_dot)

Dispositif expérimental :
  - Rayon de la surface  R_surface = 0.40 m  (bord extérieur)
  - Hauteur de courbure  h         = 0.10 m
  - Rayon sphère centrale r_sphere = 0.05 m  → frontière intérieure (collision)
  - Masse sphère centrale M_sphere = 1.3  kg

Conditions d'arrêt (sans modélisation de collision) :
  - r <= r_sphere  → collision avec la sphère centrale → simulation stoppée
  - r >= R_surface → sortie du bord de la surface     → simulation stoppée

Modèles de surface : 'cone', 'laplace'
Schémas            : 'euler_exp', 'euler_semi', 'verlet', 'rk4'
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Callable


# ─────────────────────────────────────────────
#  Géométrie du dispositif
# ─────────────────────────────────────────────


@dataclass
class DeviceGeometry:
    R_surface: float = 0.40  # m  — rayon extérieur de la surface
    h: float = 0.10  # m  — hauteur de courbure
    r_sphere: float = 0.03  # m  — rayon de la sphère centrale
    M_sphere: float = 1.3  # kg — masse de la sphère centrale (pour Laplace)


@dataclass
class PhysicsParams:
    g: float = 9.81
    m: float = 0.030  # kg  — masse de la bille
    M: float = 1.3  # kg  — masse de la sphère centrale (pour Laplace)
    mu: float = 0.004  # coefficient de Coulomb
    alpha: float = 0.0  # rad — pente conique
    K: float = 0.0  # kg·m³/s² — paramètre Laplace
    r_min: float = 0.03  # m — frontière intérieure (sphère)
    r_max: float = 0.40  # m — frontière extérieure (bord)


def compute_params(geom: DeviceGeometry, m_bille: float, mu: float) -> PhysicsParams:
    """
    Dérive les paramètres physiques depuis la géométrie du dispositif.

    Cône   : tan(α) = h / (R_surface - r_sphere)
    Laplace: z(r) = -K/(m·g·r) + C, calé sur z(r_min)=0 et z(r_max)=h
             → K = m·g·h / (1/r_min - 1/r_max)
    """
    g = 9.81
    M = geom.M_sphere
    R = geom.R_surface
    rs = geom.r_sphere
    h = geom.h

    alpha = np.arctan(h / (R - rs))
    K = M * g * h / (1.0 / rs - 1.0 / R)
    return PhysicsParams(g=g, m=m_bille, mu=mu, alpha=alpha, K=K, r_min=rs, r_max=R)


# ─────────────────────────────────────────────
#  Modèles de surface  z(r), z'(r), z''(r)
# ─────────────────────────────────────────────


def cone_surface(r: float, p: PhysicsParams):
    """
    Surface conique — géométrie bol.
    z = 0 en r_min, z = h en r_max.
    z' = tan(α) > 0 (monte vers l'extérieur).
    """
    zp = np.tan(p.alpha)
    zpp = 0.0
    z = zp * (r - p.r_min)
    return z, zp, zpp


def laplace_surface(r: float, p: PhysicsParams):
    """
    Surface de Laplace — géométrie bol.
    z(r) = -K/(m·g·r) + C, calée sur z(r_min)=0 et z(r_max)=h.
    z' = K/(m·g·r²) > 0, z'' = -2K/(m·g·r³) < 0.
    """
    K, m, g = p.K, p.M, p.g
    C = K / (m * g * p.r_min)
    z = -K / (m * g * r) + C
    zp = K / (m * g * r**2)
    zpp = -2 * K / (m * g * r**3)
    return z, zp, zpp


SURFACES: dict[str, Callable] = {
    "cone": cone_surface,
    "laplace": laplace_surface,
}


# ─────────────────────────────────────────────
#  Forces généralisées de frottement (Coulomb)
# ─────────────────────────────────────────────


def friction_forces(r, r_dot, th_dot, zp, zpp, p: PhysicsParams):
    """
    Vitesse sur la surface : v = sqrt(ṙ²(1+z'²) + r²θ̇²)
    Réaction normale       : N = m·sqrt((g·cosα)² + (v²·κ)²)
    Qr  = -μN · ṙ·sqrt(1+z'²) / v
    Qθ  = -μN · r·θ̇ / v
    """
    v2 = r_dot**2 * (1.0 + zp**2) + r**2 * th_dot**2
    v = np.sqrt(max(v2, 1e-12))

    cos_alpha = 1.0 / np.sqrt(1.0 + zp**2)
    kappa = zpp / (1.0 + zp**2) ** 1.5

    N = p.m * np.sqrt((p.g * cos_alpha) ** 2 + (v2 * kappa) ** 2)

    Qr = -p.mu * N * (r_dot * np.sqrt(1.0 + zp**2)) / v
    Qth = -p.mu * N * (r * th_dot) / v
    return Qr, Qth


# ─────────────────────────────────────────────
#  Dynamique : accélérations (r̈, θ̈)
# ─────────────────────────────────────────────


def accelerations(q: np.ndarray, surface_fn: Callable, p: PhysicsParams) -> np.ndarray:
    """
    r̈  = [ r·θ̇² - g·z' - ṙ²·z'·z'' + Qr/m ] / (1 + z'²)
    θ̈  = -2·ṙ·θ̇/r + Qθ/(m·r²)
    """
    r, th, r_dot, th_dot = q
    _, zp, zpp = surface_fn(r, p)
    Qr, Qth = friction_forces(r, r_dot, th_dot, zp, zpp, p)

    denom = 1.0 + zp**2
    r_ddot = (r * th_dot**2 - p.g * zp - r_dot**2 * zp * zpp + Qr / p.m) / denom
    th_ddot = -2.0 * r_dot * th_dot / r + Qth / (p.m * r**2)
    return np.array([r_ddot, th_ddot])


def dqdt(q: np.ndarray, surface_fn: Callable, p: PhysicsParams) -> np.ndarray:
    r, th, r_dot, th_dot = q
    r_ddot, th_ddot = accelerations(q, surface_fn, p)
    return np.array([r_dot, th_dot, r_ddot, th_ddot])


# ─────────────────────────────────────────────
#  Énergie mécanique
# ─────────────────────────────────────────────


def energy(q: np.ndarray, surface_fn: Callable, p: PhysicsParams) -> float:
    """E = ½m[ṙ²(1+z'²) + r²θ̇²] + mgz(r)"""
    r, th, r_dot, th_dot = q
    z, zp, _ = surface_fn(r, p)
    T = 0.5 * p.m * (r_dot**2 * (1.0 + zp**2) + r**2 * th_dot**2)
    V = p.m * p.g * z
    return T + V


# ─────────────────────────────────────────────
#  Schémas d'intégration numérique
# ─────────────────────────────────────────────


def euler_explicit(q, dt, surface_fn, p):
    """Euler explicite — ordre 1, non-simplectique."""
    r_ddot, th_ddot = accelerations(q, surface_fn, p)
    r, th, r_dot, th_dot = q
    return np.array(
        [r + dt * r_dot, th + dt * th_dot, r_dot + dt * r_ddot, th_dot + dt * th_ddot]
    )


def euler_semi_implicit(q, dt, surface_fn, p):
    """Euler semi-implicite — ordre 1, simplectique."""
    r_ddot, th_ddot = accelerations(q, surface_fn, p)
    r, th, r_dot, th_dot = q
    r_dot_new = r_dot + dt * r_ddot
    th_dot_new = th_dot + dt * th_ddot
    return np.array([r + dt * r_dot_new, th + dt * th_dot_new, r_dot_new, th_dot_new])


def velocity_verlet(q, dt, surface_fn, p):
    """Velocity-Verlet — ordre 2, simplectique."""
    r, th, r_dot, th_dot = q
    r_ddot_n, th_ddot_n = accelerations(q, surface_fn, p)

    r_new = r + dt * r_dot + 0.5 * dt**2 * r_ddot_n
    th_new = th + dt * th_dot + 0.5 * dt**2 * th_ddot_n

    q_mid = np.array(
        [r_new, th_new, r_dot + 0.5 * dt * r_ddot_n, th_dot + 0.5 * dt * th_ddot_n]
    )
    r_ddot_np1, th_ddot_np1 = accelerations(q_mid, surface_fn, p)

    return np.array(
        [
            r_new,
            th_new,
            r_dot + 0.5 * dt * (r_ddot_n + r_ddot_np1),
            th_dot + 0.5 * dt * (th_ddot_n + th_ddot_np1),
        ]
    )


def rk4(q, dt, surface_fn, p):
    """RK4 — ordre 4, non-simplectique."""
    k1 = dqdt(q, surface_fn, p)
    k2 = dqdt(q + dt / 2 * k1, surface_fn, p)
    k3 = dqdt(q + dt / 2 * k2, surface_fn, p)
    k4 = dqdt(q + dt * k3, surface_fn, p)
    return q + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


INTEGRATORS = {
    "verlet": velocity_verlet,
    "euler_exp": euler_explicit,
    "euler_semi": euler_semi_implicit,
    "rk4": rk4,
}

# Nombre d'évaluations de f par pas pour chaque schéma
EVALS_PER_STEP = {
    "euler_exp": 1,
    "euler_semi": 1,
    "verlet": 2,
    "rk4": 4,
}


# ─────────────────────────────────────────────
#  Boucle de simulation avec conditions d'arrêt
# ─────────────────────────────────────────────

STOP_SPHERE = "collision_sphere"
STOP_EDGE = "sortie_bord"
STOP_NUMERIC = "divergence_numerique"
STOP_NONE = "simulation_complete"


def simulate(
    q0: np.ndarray,
    T: float,
    dt: float,
    integrator_name: str,
    surface_name: str,
    p: PhysicsParams,
) -> dict:
    """
    Intègre le système sur [0, T].
    Retourne un dict incluant 'stop_reason', 't_stop' et 'cpu_s'.
    """
    surface_fn = SURFACES[surface_name]
    integrator = INTEGRATORS[integrator_name]

    n_steps = int(T / dt)
    t_arr = np.linspace(0, T, n_steps + 1)
    q_arr = np.zeros((n_steps + 1, 4))
    E_arr = np.full(n_steps + 1, np.nan)

    q_arr[0] = q0
    E_arr[0] = energy(q0, surface_fn, p)

    stop_reason = STOP_NONE
    stop_idx = n_steps

    t0 = time.perf_counter()

    for i in range(n_steps):
        q_next = integrator(q_arr[i], dt, surface_fn, p)
        r_next = q_next[0]

        if r_next <= p.r_min:
            stop_reason = STOP_SPHERE
            stop_idx = i
            q_arr[i + 1 :] = q_arr[i]
            break

        if r_next >= p.r_max:
            stop_reason = STOP_EDGE
            stop_idx = i
            q_arr[i + 1 :] = q_arr[i]
            break

        if not np.all(np.isfinite(q_next)):
            stop_reason = STOP_NUMERIC
            stop_idx = i
            q_arr[i + 1 :] = q_arr[i]
            break

        q_arr[i + 1] = q_next
        E_arr[i + 1] = energy(q_next, surface_fn, p)

    cpu_s = time.perf_counter() - t0

    r = q_arr[:, 0]
    th = q_arr[:, 1]

    return {
        "t": t_arr,
        "r": r,
        "theta": th,
        "x": r * np.cos(th),
        "y": r * np.sin(th),
        "E": E_arr,
        "q": q_arr,
        "stop_reason": stop_reason,
        "t_stop": stop_idx * dt,
        "n_steps_run": stop_idx,
        "cpu_s": cpu_s,
    }


# ─────────────────────────────────────────────
#  Métriques d'analyse
# ─────────────────────────────────────────────


def compute_metrics(res: dict, ref: dict | None = None) -> dict:
    """
    Calcule pour une simulation :
      - drift_E_pct  : dérive énergétique finale |ΔE/E₀| (%)
      - max_drift_E  : dérive énergétique max sur toute la trajectoire (%)
      - rmse_r       : RMSE sur r(t) par rapport à ref (si fourni)
      - rmse_xy      : RMSE sur (x,y) par rapport à ref (si fourni)
      - cpu_s        : temps CPU mesuré
      - cpu_per_step : temps CPU par pas de simulation (µs)
    """
    E = res["E"]
    E_valid = E[np.isfinite(E)]
    E0 = E_valid[0]
    dE_rel = np.abs((E_valid - E0) / (np.abs(E0) + 1e-12)) * 100

    metrics = {
        "drift_E_pct": float(dE_rel[-1]),
        "max_drift_E": float(dE_rel.max()),
        "cpu_s": res["cpu_s"],
        "cpu_per_step_us": res["cpu_s"] / max(res["n_steps_run"], 1) * 1e6,
        "rmse_r": None,
        "rmse_xy": None,
    }

    if ref is not None:
        n = min(res["n_steps_run"], ref["n_steps_run"])
        if n > 0:
            r_sim = res["r"][: n + 1]
            r_ref = ref["r"][: n + 1]
            metrics["rmse_r"] = float(np.sqrt(np.mean((r_sim - r_ref) ** 2)))

            x_sim = res["x"][: n + 1]
            y_sim = res["y"][: n + 1]
            x_ref = ref["x"][: n + 1]
            y_ref = ref["y"][: n + 1]
            metrics["rmse_xy"] = float(
                np.sqrt(np.mean((x_sim - x_ref) ** 2 + (y_sim - y_ref) ** 2))
            )

    return metrics


def print_metrics_table(
    all_metrics: dict[str, dict[str, dict]], integrators: list[str], surfaces: list[str]
):
    """
    Affiche un tableau récapitulatif dans le terminal.
    Structure : all_metrics[surface][integrator] = metrics_dict
    """
    col_intg = 16
    col_val = 13

    def hr(char="─"):
        return char * (col_intg + len(surfaces) * col_val * 3 + 10)

    print("\n" + "═" * 80)
    print("  TABLEAU RÉCAPITULATIF DES MÉTRIQUES")
    print("═" * 80)

    # ── Bloc 1 : Dérive énergétique finale ──
    print(f"\n{'Dérive E finale |ΔE/E₀| (%)':}")
    print(f"  {'Schéma':<{col_intg}}", end="")
    for s in surfaces:
        print(f"  {s:^{col_val}}", end="")
    print()
    print("  " + "─" * (col_intg + len(surfaces) * (col_val + 2)))
    for intg in integrators:
        print(f"  {intg:<{col_intg}}", end="")
        for s in surfaces:
            v = all_metrics[s][intg]["drift_E_pct"]
            print(f"  {v:>{col_val}.4f}", end="")
        print()

    # ── Bloc 2 : Dérive max ──
    print(f"\n{'Dérive E max |ΔE/E₀| (%)':}")
    print(f"  {'Schéma':<{col_intg}}", end="")
    for s in surfaces:
        print(f"  {s:^{col_val}}", end="")
    print()
    print("  " + "─" * (col_intg + len(surfaces) * (col_val + 2)))
    for intg in integrators:
        print(f"  {intg:<{col_intg}}", end="")
        for s in surfaces:
            v = all_metrics[s][intg]["max_drift_E"]
            print(f"  {v:>{col_val}.4f}", end="")
        print()

    # ── Bloc 3 : RMSE r vs Verlet ──
    print(f"\n{'RMSE rayon r vs Verlet (mm)':}")
    print(f"  {'Schéma':<{col_intg}}", end="")
    for s in surfaces:
        print(f"  {s:^{col_val}}", end="")
    print()
    print("  " + "─" * (col_intg + len(surfaces) * (col_val + 2)))
    for intg in integrators:
        print(f"  {intg:<{col_intg}}", end="")
        for s in surfaces:
            v = all_metrics[s][intg]["rmse_r"]
            if v is None or intg == "verlet":
                print(f"  {'(ref)':>{col_val}}", end="")
            else:
                print(f"  {v * 1000:>{col_val}.4f}", end="")
        print()

    # ── Bloc 4 : RMSE (x,y) vs Verlet ──
    print(f"\n{'RMSE position (x,y) vs Verlet (mm)':}")
    print(f"  {'Schéma':<{col_intg}}", end="")
    for s in surfaces:
        print(f"  {s:^{col_val}}", end="")
    print()
    print("  " + "─" * (col_intg + len(surfaces) * (col_val + 2)))
    for intg in integrators:
        print(f"  {intg:<{col_intg}}", end="")
        for s in surfaces:
            v = all_metrics[s][intg]["rmse_xy"]
            if v is None or intg == "verlet":
                print(f"  {'(ref)':>{col_val}}", end="")
            else:
                print(f"  {v * 1000:>{col_val}.4f}", end="")
        print()

    # ── Bloc 5 : Temps CPU total ──
    print(f"\n{'Temps CPU total (ms)':}")
    print(f"  {'Schéma':<{col_intg}}", end="")
    for s in surfaces:
        print(f"  {s:^{col_val}}", end="")
    print()
    print("  " + "─" * (col_intg + len(surfaces) * (col_val + 2)))
    for intg in integrators:
        print(f"  {intg:<{col_intg}}", end="")
        for s in surfaces:
            v = all_metrics[s][intg]["cpu_s"] * 1000
            print(f"  {v:>{col_val}.2f}", end="")
        print()

    # ── Bloc 6 : Temps CPU par pas ──
    print(f"\n{'Temps CPU / pas (µs)':}")
    print(f"  {'Schéma':<{col_intg}}", end="")
    for s in surfaces:
        print(f"  {s:^{col_val}}", end="")
    print()
    print("  " + "─" * (col_intg + len(surfaces) * (col_val + 2)))
    for intg in integrators:
        print(f"  {intg:<{col_intg}}", end="")
        for s in surfaces:
            v = all_metrics[s][intg]["cpu_per_step_us"]
            evals = EVALS_PER_STEP[intg]
            print(f"  {v:>{col_val}.3f}", end="")
        print()

    # ── Bloc 7 : Efficacité (RMSE·CPU) ──
    print(f"\n{'Efficacité : RMSE_r (mm) × CPU (ms)   [plus petit = meilleur]':}")
    print(f"  {'Schéma':<{col_intg}}", end="")
    for s in surfaces:
        print(f"  {s:^{col_val}}", end="")
    print()
    print("  " + "─" * (col_intg + len(surfaces) * (col_val + 2)))
    for intg in integrators:
        print(f"  {intg:<{col_intg}}", end="")
        for s in surfaces:
            rmse = all_metrics[s][intg]["rmse_r"]
            cpu = all_metrics[s][intg]["cpu_s"] * 1000
            if rmse is None or intg == "verlet":
                print(f"  {'(ref)':>{col_val}}", end="")
            else:
                print(f"  {rmse * 1000 * cpu:>{col_val}.4f}", end="")
        print()

    print("\n" + "═" * 80 + "\n")


# ─────────────────────────────────────────────
#  Visualisation comparative (2 surfaces)
# ─────────────────────────────────────────────


def plot_comparison(all_results: dict[str, dict[str, dict]], p: PhysicsParams):
    """
    Figure 4×2 :
      Colonne gauche  : surface cône
      Colonne droite  : surface Laplace
      Lignes          : trajectoire plan | r(t) | dérive E | RMSE cumulé vs verlet
    """
    surfaces = list(all_results.keys())
    integrators = list(all_results[surfaces[0]].keys())

    colors = {
        "euler_exp": "#E24B4A",
        "euler_semi": "#EF9F27",
        "verlet": "#1D9E75",
        "rk4": "#378ADD",
    }
    labels = {
        "euler_exp": "Euler explicite",
        "euler_semi": "Euler semi-implicite",
        "verlet": "Velocity-Verlet",
        "rk4": "RK4",
    }
    surf_titles = {"cone": "Cône", "laplace": "Laplace"}

    fig, axes = plt.subplots(4, 2, figsize=(14, 18))
    fig.suptitle("Analyse comparative — cône vs Laplace", fontsize=14, y=0.995)

    theta_plot = np.linspace(0, 2 * np.pi, 300)

    for col, surf in enumerate(surfaces):
        results = all_results[surf]
        ref = results["verlet"]

        ax_xy = axes[0, col]
        ax_r = axes[1, col]
        ax_E = axes[2, col]
        ax_rm = axes[3, col]

        # ── Frontières ──
        ax_xy.plot(
            p.r_min * np.cos(theta_plot),
            p.r_min * np.sin(theta_plot),
            "k--",
            lw=0.7,
            label=f"r_min={p.r_min}m",
        )
        ax_xy.plot(
            p.r_max * np.cos(theta_plot),
            p.r_max * np.sin(theta_plot),
            "k:",
            lw=0.7,
            label=f"r_max={p.r_max}m",
        )

        for intg in integrators:
            res = results[intg]
            c = colors[intg]
            lbl = f"{labels[intg]} [{res['stop_reason']}  t={res['t_stop']:.2f}s]"
            mask = np.isfinite(res["E"])
            n = res["n_steps_run"]

            ax_xy.plot(res["x"][mask], res["y"][mask], color=c, lw=1.0, label=lbl)
            ax_r.plot(
                res["t"][mask], res["r"][mask], color=c, lw=1.0, label=labels[intg]
            )

            E0 = res["E"][0]
            with np.errstate(invalid="ignore"):
                dE = (res["E"] - E0) / (np.abs(E0) + 1e-12) * 100
            ax_E.plot(res["t"][mask], dE[mask], color=c, lw=1.0, label=labels[intg])

            # RMSE cumulé vs verlet
            if intg != "verlet" and n > 0:
                n_c = min(n, ref["n_steps_run"])
                rmse = np.sqrt(
                    np.cumsum((res["r"][: n_c + 1] - ref["r"][: n_c + 1]) ** 2)
                    / (np.arange(n_c + 1) + 1)
                )
                ax_rm.plot(
                    res["t"][: n_c + 1],
                    rmse * 1000,
                    color=c,
                    lw=1.0,
                    label=labels[intg],
                )

        ax_xy.set_title(f"Trajectoire — {surf_titles[surf]}", fontsize=11)
        ax_xy.set_xlabel("x (m)")
        ax_xy.set_ylabel("y (m)")
        ax_xy.set_aspect("equal")
        ax_xy.legend(fontsize=6.5)

        ax_r.axhline(p.r_min, color="k", ls="--", lw=0.6)
        ax_r.axhline(p.r_max, color="k", ls=":", lw=0.6)
        ax_r.set_title(f"Rayon r(t) — {surf_titles[surf]}", fontsize=11)
        ax_r.set_xlabel("t (s)")
        ax_r.set_ylabel("r (m)")
        ax_r.legend(fontsize=7)

        ax_E.axhline(0, color="gray", lw=0.6, ls="--")
        ax_E.set_title(
            f"Dérive énergétique ΔE/E₀ (%) — {surf_titles[surf]}", fontsize=11
        )
        ax_E.set_xlabel("t (s)")
        ax_E.set_ylabel("ΔE/E₀ (%)")
        ax_E.legend(fontsize=7)

        ax_rm.set_title(
            f"RMSE cumulé r vs verlet (mm) — {surf_titles[surf]}", fontsize=11
        )
        ax_rm.set_xlabel("t (s)")
        ax_rm.set_ylabel("RMSE r (mm)")
        ax_rm.legend(fontsize=7)

    plt.tight_layout()
    plt.savefig("comparaison_integrateurs.png", dpi=150, bbox_inches="tight")
    plt.show()


# ─────────────────────────────────────────────
#  Fig. B — Profils de surface z(r), z'(r), z''(r)
# ─────────────────────────────────────────────


def plot_surface_profiles(p: PhysicsParams):
    """
    Trace z(r), z'(r) et z''(r) pour les deux modèles sur [r_min, r_max].
    Justifie visuellement pourquoi κ=0 (cône) vs κ≠0 (Laplace).
    Sauvegarde : surface_profiles.png
    """
    r_arr = np.linspace(p.r_min, p.r_max, 500)

    surf_data = {}
    for name, fn in SURFACES.items():
        z_arr = np.array([fn(r, p)[0] for r in r_arr])
        zp_arr = np.array([fn(r, p)[1] for r in r_arr])
        zpp_arr = np.array([fn(r, p)[2] for r in r_arr])
        kappa = zpp_arr / (1 + zp_arr**2) ** 1.5
        surf_data[name] = (z_arr, zp_arr, zpp_arr, kappa)

    colors_surf = {"cone": "#378ADD", "laplace": "#E24B4A"}
    labels_surf = {"cone": "Cône", "laplace": "Laplace"}

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.suptitle("Profils des surfaces — géométrie bol", fontsize=13)

    titles = [
        "z(r)  [m]",
        "z'(r) = dz/dr",
        "z''(r) = d²z/dr²",
        r"κ(r) = z'' / (1+z'²)^{3/2}  [m⁻¹]",
    ]
    keys = [0, 1, 2, 3]

    for ax, k, title in zip(axes, keys, titles):
        for name in SURFACES:
            ax.plot(
                r_arr * 100,
                surf_data[name][k],
                color=colors_surf[name],
                lw=1.8,
                label=labels_surf[name],
            )
        ax.axhline(0, color="gray", lw=0.6, ls="--")
        ax.axvline(p.r_min * 100, color="k", lw=0.7, ls=":", alpha=0.5)
        ax.axvline(p.r_max * 100, color="k", lw=0.7, ls=":", alpha=0.5)
        ax.set_xlabel("r (cm)")
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)

    plt.tight_layout()
    plt.savefig("surface_profiles.png", dpi=150, bbox_inches="tight")
    plt.show()


# ─────────────────────────────────────────────
#  Fig. C — Espace des phases (r, ṙ)
# ─────────────────────────────────────────────


def plot_phase_space(all_results: dict[str, dict[str, dict]], p: PhysicsParams):
    """
    Trace le portrait de phase (r, ṙ) pour chaque intégrateur et chaque surface.
    Les schémas symplectiques produisent des courbes quasi-fermées ;
    Euler explicite diverge, RK4 converge légèrement.
    Sauvegarde : phase_space.png
    """
    surfaces = list(all_results.keys())
    integrators = list(all_results[surfaces[0]].keys())

    colors = {
        "euler_exp": "#E24B4A",
        "euler_semi": "#EF9F27",
        "verlet": "#1D9E75",
        "rk4": "#378ADD",
    }
    labels = {
        "euler_exp": "Euler explicite",
        "euler_semi": "Euler semi-implicite",
        "verlet": "Velocity-Verlet",
        "rk4": "RK4",
    }
    surf_titles = {"cone": "Cône", "laplace": "Laplace"}

    fig, axes = plt.subplots(1, len(surfaces), figsize=(7 * len(surfaces), 6))
    if len(surfaces) == 1:
        axes = [axes]
    fig.suptitle("Portrait de phase (r, ṙ)", fontsize=13)

    for ax, surf in zip(axes, surfaces):
        for intg in integrators:
            res = all_results[surf][intg]
            mask = np.isfinite(res["E"])
            r_arr = res["q"][:, 0][mask]
            r_dot_arr = res["q"][:, 2][mask]
            ax.plot(
                r_arr * 100,
                r_dot_arr * 100,
                color=colors[intg],
                lw=0.8,
                alpha=0.85,
                label=labels[intg],
            )
            # Point initial
            ax.scatter(
                [r_arr[0] * 100],
                [r_dot_arr[0] * 100],
                color=colors[intg],
                s=30,
                zorder=5,
            )

        ax.set_title(f"Espace des phases — {surf_titles[surf]}", fontsize=11)
        ax.set_xlabel("r (cm)")
        ax.set_ylabel("ṙ (cm/s)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.25)

    plt.tight_layout()
    plt.savefig("phase_space.png", dpi=150, bbox_inches="tight")
    plt.show()


# ─────────────────────────────────────────────
#  Fig. E — θ(t) et moment cinétique L(t)
# ─────────────────────────────────────────────


def plot_angular(all_results: dict[str, dict[str, dict]], p: PhysicsParams):
    """
    Ligne 1 : angle accumulé θ(t) — montre la progression angulaire.
    Ligne 2 : moment cinétique L = m·r²·θ̇ — doit rester quasi-constant
              sans frottement ; sa dérive mesure l'erreur sur la variable angulaire.
    Sauvegarde : angular_momentum.png
    """
    surfaces = list(all_results.keys())
    integrators = list(all_results[surfaces[0]].keys())

    colors = {
        "euler_exp": "#E24B4A",
        "euler_semi": "#EF9F27",
        "verlet": "#1D9E75",
        "rk4": "#378ADD",
    }
    labels = {
        "euler_exp": "Euler explicite",
        "euler_semi": "Euler semi-implicite",
        "verlet": "Velocity-Verlet",
        "rk4": "RK4",
    }
    surf_titles = {"cone": "Cône", "laplace": "Laplace"}

    fig, axes = plt.subplots(2, len(surfaces), figsize=(7 * len(surfaces), 10))
    fig.suptitle("Évolution angulaire et moment cinétique", fontsize=13)

    for col, surf in enumerate(surfaces):
        ax_th = axes[0, col] if len(surfaces) > 1 else axes[0]
        ax_L = axes[1, col] if len(surfaces) > 1 else axes[1]

        for intg in integrators:
            res = all_results[surf][intg]
            mask = np.isfinite(res["E"])
            t_arr = res["t"][mask]
            r_arr = res["q"][:, 0][mask]
            th_arr = res["q"][:, 1][mask]
            th_dot_arr = res["q"][:, 3][mask]

            # Moment cinétique L = m·r²·θ̇
            L = p.m * r_arr**2 * th_dot_arr
            L0 = L[0] if len(L) > 0 else 1.0

            ax_th.plot(
                t_arr,
                np.degrees(th_arr),
                color=colors[intg],
                lw=1.0,
                label=labels[intg],
            )
            ax_L.plot(
                t_arr,
                (L - L0) / (np.abs(L0) + 1e-12) * 100,
                color=colors[intg],
                lw=1.0,
                label=labels[intg],
            )

        ax_th.set_title(f"Angle θ(t) — {surf_titles[surf]}", fontsize=11)
        ax_th.set_xlabel("t (s)")
        ax_th.set_ylabel("θ (degrés)")
        ax_th.legend(fontsize=8)
        ax_th.grid(True, alpha=0.25)

        ax_L.axhline(0, color="gray", lw=0.6, ls="--")
        ax_L.set_title(
            f"Dérive moment cinétique ΔL/L₀ (%) — {surf_titles[surf]}", fontsize=11
        )
        ax_L.set_xlabel("t (s)")
        ax_L.set_ylabel("ΔL/L₀ (%)")
        ax_L.legend(fontsize=8)
        ax_L.grid(True, alpha=0.25)

    plt.tight_layout()
    plt.savefig("angular_momentum.png", dpi=150, bbox_inches="tight")
    plt.show()


# ─────────────────────────────────────────────
#  Fig. D — Sensibilité à Δt (convergence en ordre)
# ─────────────────────────────────────────────


def plot_dt_convergence(
    q0: np.ndarray,
    T_short: float,
    surface_name: str,
    p: PhysicsParams,
    dt_values: list | None = None,
):
    """
    Pour chaque Δt dans dt_values, lance RK4 (référence haute précision à dt_ref)
    et tous les intégrateurs, puis trace RMSE(r) vs Δt en log-log.
    La pente de chaque droite doit correspondre à l'ordre théorique.

    Paramètres
    ----------
    T_short      : durée courte pour que toutes les simulations convergent (ex. 0.5 s)
    dt_values    : liste de pas de temps à tester
    Sauvegarde   : dt_convergence.png
    """
    if dt_values is None:
        dt_values = [5e-3, 2e-3, 1e-3, 5e-4, 2e-4, 1e-4]

    # Référence : RK4 avec le plus petit Δt
    dt_ref = min(dt_values) / 5
    ref = simulate(q0, T_short, dt_ref, "rk4", surface_name, p)

    colors = {
        "euler_exp": "#E24B4A",
        "euler_semi": "#EF9F27",
        "verlet": "#1D9E75",
        "rk4": "#378ADD",
    }
    labels = {
        "euler_exp": "Euler exp. (ordre 1)",
        "euler_semi": "Euler semi-imp. (ordre 1)",
        "verlet": "Velocity-Verlet (ordre 2)",
        "rk4": "RK4 (ordre 4)",
    }
    orders = {"euler_exp": 1, "euler_semi": 1, "verlet": 2, "rk4": 4}

    rmse_data = {intg: [] for intg in INTEGRATORS}

    print(f"\nConvergence en dt -- surface={surface_name}  T={T_short}s")
    for dt in dt_values:
        for intg in INTEGRATORS:
            res = simulate(q0, T_short, dt, intg, surface_name, p)
            n = min(res["n_steps_run"], ref["n_steps_run"])
            # Interpoler la référence sur la grille grossière
            t_coarse = res["t"][: n + 1]
            r_ref_interp = np.interp(t_coarse, ref["t"], ref["r"])
            rmse = float(np.sqrt(np.mean((res["r"][: n + 1] - r_ref_interp) ** 2)))
            rmse_data[intg].append(rmse)
        print(f"  dt={dt:.0e}  OK")

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_title(f"Convergence en Δt — surface : {surface_name}", fontsize=12)

    for intg in INTEGRATORS:
        rmse_arr = np.array(rmse_data[intg])
        valid = rmse_arr > 0
        if valid.sum() < 2:
            continue
        dt_arr = np.array(dt_values)[valid]
        ax.loglog(
            dt_arr,
            rmse_arr[valid],
            "o-",
            color=colors[intg],
            lw=1.4,
            ms=5,
            label=labels[intg],
        )

        # Droite de pente théorique
        p_th = orders[intg]
        x0, y0 = dt_arr[-1], rmse_arr[valid][-1]
        x1 = dt_arr[0]
        ax.loglog(
            [x0, x1],
            [y0, y0 * (x1 / x0) ** p_th],
            "--",
            color=colors[intg],
            lw=0.8,
            alpha=0.5,
        )

    ax.set_xlabel("Δt (s)")
    ax.set_ylabel("RMSE r (m)")
    ax.legend(fontsize=8)
    ax.grid(True, which="both", alpha=0.25)

    plt.tight_layout()
    plt.savefig("dt_convergence.png", dpi=150, bbox_inches="tight")
    plt.show()


# ─────────────────────────────────────────────
#  Export LaTeX des tableaux
# ─────────────────────────────────────────────


def export_latex_tables(
    all_metrics: dict[str, dict[str, dict]],
    p: PhysicsParams,
    surfaces: list[str],
    integrators: list[str],
    filename: str = "tables_annexe.tex",
):
    """
    Genere un fichier .tex contenant :
      - Tab. B : parametres du modele derives du dispositif
      - Tab. D : performances numeriques completes (drift E, RMSE, CPU)
    Pret a \\input{} dans le rapport.
    """
    intg_labels = {
        "euler_exp": "Euler exp.",
        "euler_semi": "Euler semi-imp.",
        "verlet": "Velocity-Verlet",
        "rk4": "RK4",
    }

    L = []
    L.append("% Tableaux generes automatiquement par integration_lagrangienne.py")
    L.append("")

    # Tab. B : Parametres du modele
    L.append(r"\begin{table}[h]")
    L.append(r"  \centering")
    L.append(r"  \small")
    L.append(
        r"  \caption{Param\`etres physiques d\'eriv\'es de la g\'eom\'etrie du dispositif.}"
    )
    L.append(r"  \label{tab:params_modele}")
    L.append(r"  \begin{tabular}{llll}")
    L.append(r"    \toprule")
    L.append(r"    Param\`etre & Symbole & Valeur & Unit\'e \\")
    L.append(r"    \midrule")
    L.append(r"    Rayon de la surface & $R$ & $0.40$ & m \\")
    L.append(r"    Hauteur de courbure & $h$ & $0.10$ & m \\")
    L.append(r"    Rayon sph\`ere centrale & $r_{\text{sph}}$ & $0.05$ & m \\")
    L.append(r"    Masse sph\`ere centrale & $M$ & $1.30$ & kg \\")
    L.append(
        f"    Pente conique & $\\\\alpha$ & ${np.degrees(p.alpha):.2f}$ & \\\\textdegree \\\\"
    )
    L.append(f"    Param\\`etre Laplace & $K$ & ${p.K:.5f}$ & kg\\,m$^3$/s$^2$ \\\\")
    L.append(
        f"    Fronti\\`ere int\\u00e9rieure & $r_{{\\\\min}}$ & ${p.r_min:.3f}$ & m \\\\"
    )
    L.append(
        f"    Fronti\\`ere ext\\u00e9rieure & $r_{{\\\\max}}$ & ${p.r_max:.3f}$ & m \\\\"
    )
    L.append(r"    \bottomrule")
    L.append(r"  \end{tabular}")
    L.append(r"\end{table}")
    L.append("")

    # Tab. D : Performances numeriques
    for surf in surfaces:
        surf_label = "C\\^one" if surf == "cone" else "Laplace"
        L.append(r"\begin{table}[h]")
        L.append(r"  \centering")
        L.append(r"  \small")
        L.append(
            f"  \\\\caption{{Performances num\\u00e9riques des int\\u00e9grateurs --- surface {surf_label}.}}"
        )
        L.append(f"  \\\\label{{tab:perf_{surf}}}")
        L.append(r"  \begin{tabular}{lccccc}")
        L.append(r"    \toprule")
        L.append(
            r"    M\'ethode & Drift $|\Delta E/E_0|$ (\%) & Max drift (\%) & RMSE $r$ (mm) & RMSE $(x,y)$ (mm) & CPU (ms) \\"
        )
        L.append(r"    \midrule")

        for intg in integrators:
            m = all_metrics[surf][intg]
            drift = f"{m['drift_E_pct']:.4f}"
            mdrift = f"{m['max_drift_E']:.4f}"
            rmse_r = f"{m['rmse_r'] * 1000:.4f}" if m["rmse_r"] is not None else "---"
            rmse_xy = (
                f"{m['rmse_xy'] * 1000:.4f}" if m["rmse_xy"] is not None else "---"
            )
            cpu = f"{m['cpu_s'] * 1000:.1f}"
            lbl = intg_labels.get(intg, intg)
            L.append(
                f"    {lbl} & ${drift}$ & ${mdrift}$ & ${rmse_r}$ & ${rmse_xy}$ & ${cpu}$ \\\\"
            )

        L.append(r"    \bottomrule")
        L.append(r"  \end{tabular}")
        L.append(r"\end{table}")
        L.append("")

    with open(filename, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    print(f"\n OK Tableaux LaTeX exportes -> {filename}")
    print(f"   Utiliser \\input{{{filename}}} dans le rapport.")


# ─────────────────────────────────────────────
#  Point d'entrée
# ─────────────────────────────────────────────

if __name__ == "__main__":
    geom = DeviceGeometry(R_surface=0.40, h=0.10, r_sphere=0.03, M_sphere=1.3)
    p = compute_params(geom, m_bille=0.030, mu=0.004)

    print("Paramètres calculés depuis la géométrie :")
    print(f"  alpha  = {np.degrees(p.alpha):.2f}°  (tan α = {np.tan(p.alpha):.4f})")
    print(f"  K      = {p.K:.5f} kg·m³/s²")
    print(f"  r_min  = {p.r_min} m  (sphère — collision)")
    print(f"  r_max  = {p.r_max} m  (bord   — sortie)")

    # ── Conditions initiales ──────────────────────────────────────
    r0 = 0.38
    r_dot0 = -0.1

    th_dot_orb = np.sqrt(p.g * np.tan(p.alpha) / r0)

    facteur = 0.7  # 1.0 = orbite stable, >1 spirale ext., <1 spirale int.
    th_dot0 = th_dot_orb * facteur
    # th_dot0 = 2.5        # ← valeur directe en rad/s (décommenter si besoin)

    q0 = np.array([r0, 0.0, r_dot0, th_dot0])

    print(f"\nConditions initiales :")
    print(f"  r0        = {r0} m")
    print(f"  r_dot0    = {r_dot0} m/s")
    print(f"  θ̇_orbital = {th_dot_orb:.3f} rad/s")
    print(f"  θ̇_0       = {th_dot0:.3f} rad/s  (facteur={facteur:.2f})")
    regime = (
        "sous-orbital → spirale intérieure"
        if facteur < 1
        else "sur-orbital → spirale extérieure"
        if facteur > 1
        else "orbital stable"
    )
    print(f"  régime    : {regime}")

    T = 25.0
    dt = 5e-5
    surfaces_to_run = ["cone", "laplace"]

    print(f"\nSimulation — surfaces={surfaces_to_run}  T={T}s  dt={dt}s\n")

    # ── Lancement ────────────────────────────────────────────────
    all_results = {}
    all_metrics = {}

    for surf in surfaces_to_run:
        all_results[surf] = {}
        all_metrics[surf] = {}
        print(f"  Surface : {surf}")

        for intg in INTEGRATORS:
            res = simulate(q0, T, dt, intg, surf, p)
            all_results[surf][intg] = res

            ref = all_results[surf].get("verlet")  # None si verlet pas encore tourné
            m = compute_metrics(res, ref)
            all_metrics[surf][intg] = m

            print(
                f"    {intg:15s} | {res['stop_reason']:25s} "
                f"| t_stop={res['t_stop']:.3f}s "
                f"| drift={m['drift_E_pct']:.4f}% "
                f"| CPU={m['cpu_s'] * 1000:.1f}ms"
            )
        print()

    # ── Tableau récapitulatif terminal ───────────────────────────
    print_metrics_table(all_metrics, list(INTEGRATORS.keys()), surfaces_to_run)

    # ── Fig. A : comparaison 4×2 (déjà dans le script) ───────────
    plot_comparison(all_results, p)

    # ── Fig. B : profils de surface z(r), z'(r), z''(r), κ(r) ────
    plot_surface_profiles(p)

    # ── Fig. C : portrait de phase (r, ṙ) ────────────────────────
    plot_phase_space(all_results, p)

    # ── Fig. E : θ(t) et moment cinétique L(t) ───────────────────
    plot_angular(all_results, p)

    # ── Fig. D : convergence en Δt (optionnel, coûteux en CPU) ───
    # Décommenter pour vérifier empiriquement les ordres de convergence.
    # Utilise une courte durée T_short pour rester rapide.
    #
    # plot_dt_convergence(q0, T_short=0.5, surface_name="cone", p=p)

    # ── Export tableaux LaTeX ─────────────────────────────────────
    # Génère tables_annexe.tex contenant Tab. B (paramètres) et
    # Tab. D (performances) prêts à \input{} dans le rapport.
    export_latex_tables(
        all_metrics,
        p,
        surfaces=surfaces_to_run,
        integrators=list(INTEGRATORS.keys()),
        filename="tables_annexe.tex",
    )
