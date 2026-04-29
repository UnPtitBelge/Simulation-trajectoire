"""Lance les simulations et génère les graphes."""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from functools import partial
from pathlib import Path

from surfaces import cone_slope, laplace_slope, laplace_regularized_slope
from physics import (
    centripetal_acceleration,
    laplace_mechanical_energy,
    laplace_regularized_mechanical_energy,
    cone_mechanical_energy,
)
from integrators import (
    explicit_euler,
    semi_implicit_euler,
    velocity_verlet,
    rk4,
)
from simulations import simulate, simulate_adaptive, stop_at_radius

# ─────────────────────────────────────────────────────────────────────────────
# Paramètres expérimentaux
# ─────────────────────────────────────────────────────────────────────────────

M = 1.00  # masse bille (kg)
G = 9.81  # pesanteur (m/s²)
R_MIN = 0.03  # rayon bille centrale (m) — condition d'arrêt (collision)
R_MAX = 0.80  # rayon membrane (m)
MU = 0.01  # coefficient de résistance au roulement (adimensionnel)
DT = 1e-3  # pas de temps (s)
MAX_STEPS = 1_000_000  # garde-fou (orbite sans frottement n'atteint jamais r_min/r_max)

# Rayon de régularisation du modèle Laplace (m), utilisé uniquement par
# le modèle « Laplace R_C ». Pour r < R_C, la surface est un cône tangent
# à la courbe Laplace en r = R_C (raccord C¹). Motivation : la pente
# Laplace dz/dr = K/(m g r²) diverge en 1/r² au voisinage du centre,
# ce qui crée une stiffness numérique énorme au périgée.
# Choix de R_C : 0.10 m ≈ 3.3 × R_MIN — borne a_c(R_C) à un facteur ~11
# de plus que a_c(R_MIN) (relation quadratique), sans défigurer la
# surface au-delà. Interprétation physique : la bille centrale de rayon
# R_MIN aplatit la membrane sous elle sur un disque de rayon ≈ R_C.
R_C = 0.10

# Bornes du pas adaptatif pour le modèle Laplace pur. L'adaptatif suit
# la loi de Kepler dt(r) = DT × (r / R_REF)^(3/2) : nombre de pas par
# orbite constant, quelle que soit la distance au centre. Plafonné pour
# éviter un dt excessif à grand r, et borné par le bas pour garder un
# minimum de précision même au périgée.
DT_ADAPT_MAX = 5e-3
DT_ADAPT_MIN = 1e-6

# Dossier de destination des graphes
FIGURES_DIR = Path("figures/physic_models")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Conditions initiales via arguments CLI (défauts : orbite quasi-circulaire)
_parser = argparse.ArgumentParser(description="Simulations trajectoire physique")
_parser.add_argument("--x", type=float, default=0.75, help="position initiale x (m)")
_parser.add_argument("--y", type=float, default=0.0, help="position initiale y (m)")
_parser.add_argument("--vx", type=float, default=0.0, help="vitesse initiale vx (m/s)")
_parser.add_argument("--vy", type=float, default=0.7, help="vitesse initiale vy (m/s)")
_args = _parser.parse_args()

R0 = np.array([_args.x, _args.y])
V0 = np.array([_args.vx, _args.vy])

# Référence du potentiel : Ep = 0 à r = |R0|.
R_REF = float(np.linalg.norm(R0))

# Constante K ajustée à l'orbite initiale (Laplace)
K = M * np.linalg.norm(R0) * np.linalg.norm(V0) ** 2

# Paramètre surface conique : angle tel que v0 est l'orbite circulaire à r0
ALPHA = np.arctan(np.linalg.norm(V0) ** 2 / (G * np.linalg.norm(R0)))

# ─────────────────────────────────────────────────────────────────────────────
# Définition des modèles et intégrateurs
# ─────────────────────────────────────────────────────────────────────────────


# Pas adaptatif pour le modèle Laplace pur : dt ∝ r^(3/2) (loi de Kepler)
# calibré pour que dt(R_REF) = DT. Concrètement : à l'apogée le pas est
# ~DT, au périgée il est beaucoup plus petit → la stiffness numérique
# est compensée sans surcoût global (moins de pas dans la branche stable
# de l'orbite, plus dans la branche rapide).
def dt_kepler_adaptive(r_vec, _v_vec):
    rn = float(np.linalg.norm(r_vec))
    dt = DT * (rn / R_REF) ** 1.5
    return float(np.clip(dt, DT_ADAPT_MIN, DT_ADAPT_MAX))


MODELS = {
    "Conique": partial(cone_slope, alpha_const=ALPHA),
    "Laplace": partial(laplace_slope, K=K, m=M, g=G),
    "Laplace R_C": partial(laplace_regularized_slope, K=K, m=M, r_c=R_C, g=G),
}

ENERGY_FUNCS = {
    "Conique": lambda r, v: cone_mechanical_energy(
        M, np.linalg.norm(v), np.linalg.norm(r), ALPHA, G, R_REF
    ),
    "Laplace": lambda r, v: laplace_mechanical_energy(
        M, np.linalg.norm(v), np.linalg.norm(r), K, G, R_REF
    ),
    "Laplace R_C": lambda r, v: laplace_regularized_mechanical_energy(
        M, np.linalg.norm(v), np.linalg.norm(r), K, R_C, G, R_REF
    ),
}

# Stratégie d'intégration par modèle :
#   - float  → simulate() avec dt fixe
#   - Callable → simulate_adaptive() avec dt_func(r, v)
# Seul Laplace pur (singulier en 1/r²) justifie le coût d'un pas adaptatif ;
# Conique et Laplace R_C ont une accélération bornée, un dt fixe suffit.
DT_SPEC = {
    "Conique": DT,
    "Laplace": dt_kepler_adaptive,
    "Laplace R_C": DT,
}

INTEGRATORS = {
    "Euler": explicit_euler,
    "Euler semi-implicite": semi_implicit_euler,
    "Verlet": velocity_verlet,
    "RK4": rk4,
}

COLORS_MODEL = {
    "Conique": "#e07b54",
    "Laplace": "#5b8dd9",
    "Laplace R_C": "#b07bd9",
}

COLORS_INTEG = {
    "Euler": "#e05c5c",
    "Euler semi-implicite": "#e0b84a",
    "Verlet": "#5b8dd9",
    "RK4": "#6abf8a",
}


def make_acc(slope_func):
    def acc(r_vec, v_vec):
        rn = np.linalg.norm(r_vec)
        vn = np.linalg.norm(v_vec)
        if rn <= 0:
            return np.zeros(2)
        a_c = centripetal_acceleration(rn, slope_func, G)
        a_centripete = -a_c * r_vec / rn
        a_frottement = -MU * G * (v_vec / vn) if vn > 0 else np.zeros(2)
        return a_centripete + a_frottement

    return acc


def run(slope_func, integrator, dt_spec):
    acc = make_acc(slope_func)
    stop = stop_at_radius(R_MIN, R_MAX)
    if callable(dt_spec):
        return simulate_adaptive(
            R0,
            V0,
            acc,
            integrator,
            dt_spec,
            stop_condition=stop,
            max_steps=MAX_STEPS,
        )
    return simulate(
        R0,
        V0,
        acc,
        integrator,
        dt_spec,
        stop_condition=stop,
        max_steps=MAX_STEPS,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Collecte des données
# ─────────────────────────────────────────────────────────────────────────────

results = {}
for model_name, slope_func in MODELS.items():
    results[model_name] = {}
    for integ_name, integrator in INTEGRATORS.items():
        t, r, v, a = run(slope_func, integrator, DT_SPEC[model_name])
        Em = np.array([ENERGY_FUNCS[model_name](r[i], v[i]) for i in range(len(t))])
        results[model_name][integ_name] = {"t": t, "r": r, "v": v, "Em": Em}

# ─────────────────────────────────────────────────────────────────────────────
# Style global
# ─────────────────────────────────────────────────────────────────────────────

plt.rcParams.update(
    {
        "figure.facecolor": "#0f0f13",
        "axes.facecolor": "#16161d",
        "axes.edgecolor": "#333344",
        "axes.labelcolor": "#c8c8d8",
        "axes.titlecolor": "#e8e8f0",
        "axes.grid": True,
        "grid.color": "#252535",
        "grid.linewidth": 0.6,
        "xtick.color": "#888899",
        "ytick.color": "#888899",
        "text.color": "#c8c8d8",
        "legend.facecolor": "#1c1c28",
        "legend.edgecolor": "#333344",
        "legend.fontsize": 8,
        "lines.linewidth": 1.4,
        "font.family": "monospace",
    }
)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 : Comparaison des modèles (Verlet) — trajectoire + Em + |r|
# ─────────────────────────────────────────────────────────────────────────────

fig1, axes1 = plt.subplots(1, 3, figsize=(15, 5))
fig1.patch.set_facecolor("#0f0f13")
fig1.suptitle("Comparaison des modèles — Verlet", color="#e8e8f0", fontsize=13, y=1.01)

# Trajectoires
ax = axes1[0]
ax.set_title("Trajectoire (x, y)", fontsize=10)
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(
    R_MIN * np.cos(theta),
    R_MIN * np.sin(theta),
    "--",
    color="#555566",
    lw=0.8,
    label="r_min",
)
ax.plot(
    R_MAX * np.cos(theta),
    R_MAX * np.sin(theta),
    "--",
    color="#333344",
    lw=0.8,
    label="r_max",
)
for model_name, color in COLORS_MODEL.items():
    r = results[model_name]["Verlet"]["r"]
    ax.plot(r[:, 0], r[:, 1], color=color, label=model_name, alpha=0.9)
ax.set_aspect("equal")
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")
ax.legend()

# Énergie mécanique
ax = axes1[1]
ax.set_title("Énergie mécanique Em(t)", fontsize=10)
for model_name, color in COLORS_MODEL.items():
    t = results[model_name]["Verlet"]["t"]
    Em = results[model_name]["Verlet"]["Em"]
    ax.plot(t, Em * 1000, color=color, label=model_name, alpha=0.9)
ax.set_xlabel("t (s)")
ax.set_ylabel("Em (mJ)")
ax.legend()

# Rayon
ax = axes1[2]
ax.set_title("|r|(t)", fontsize=10)
for model_name, color in COLORS_MODEL.items():
    t = results[model_name]["Verlet"]["t"]
    r = results[model_name]["Verlet"]["r"]
    ax.plot(t, np.linalg.norm(r, axis=1), color=color, label=model_name, alpha=0.9)
ax.axhline(R_MIN, color="#555566", lw=0.8, ls="--", label="r_min")
ax.axhline(R_MAX, color="#333344", lw=0.8, ls="--", label="r_max")
ax.set_xlabel("t (s)")
ax.set_ylabel("|r| (m)")
ax.legend()

fig1.tight_layout()
fig1.savefig(
    FIGURES_DIR / "fig1_modeles.png",
    dpi=150,
    bbox_inches="tight",
    facecolor=fig1.get_facecolor(),
)
print(FIGURES_DIR / "fig1_modeles.png")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 : Comparaison des intégrateurs sur chaque modèle — trajectoires
# ─────────────────────────────────────────────────────────────────────────────

fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
fig2.patch.set_facecolor("#0f0f13")
fig2.suptitle(
    "Comparaison des intégrateurs — trajectoires", color="#e8e8f0", fontsize=13, y=1.01
)

for ax, model_name in zip(axes2, MODELS):
    ax.set_title(model_name, fontsize=10)
    theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(R_MIN * np.cos(theta), R_MIN * np.sin(theta), "--", color="#555566", lw=0.8)
    ax.plot(R_MAX * np.cos(theta), R_MAX * np.sin(theta), "--", color="#333344", lw=0.8)
    for integ_name, color in COLORS_INTEG.items():
        r = results[model_name][integ_name]["r"]
        ax.plot(r[:, 0], r[:, 1], color=color, label=integ_name, alpha=0.85)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend()

fig2.tight_layout()
fig2.savefig(
    FIGURES_DIR / "fig2_integrateurs_trajectoires.png",
    dpi=150,
    bbox_inches="tight",
    facecolor=fig2.get_facecolor(),
)
print(FIGURES_DIR / "fig2_integrateurs_trajectoires.png")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 : Comparaison des intégrateurs — Em(t) par modèle
# ─────────────────────────────────────────────────────────────────────────────

fig3, axes3 = plt.subplots(1, 3, figsize=(15, 5))
fig3.patch.set_facecolor("#0f0f13")
fig3.suptitle(
    "Comparaison des intégrateurs — énergie mécanique",
    color="#e8e8f0",
    fontsize=13,
    y=1.01,
)

for ax, model_name in zip(axes3, MODELS):
    ax.set_title(model_name, fontsize=10)
    for integ_name, color in COLORS_INTEG.items():
        t = results[model_name][integ_name]["t"]
        Em = results[model_name][integ_name]["Em"]
        ax.plot(t, Em * 1000, color=color, label=integ_name, alpha=0.85)
    ax.set_xlabel("t (s)")
    ax.set_ylabel("Em (mJ)")
    ax.legend()

fig3.tight_layout()
fig3.savefig(
    FIGURES_DIR / "fig3_integrateurs_energie.png",
    dpi=150,
    bbox_inches="tight",
    facecolor=fig3.get_facecolor(),
)
print(FIGURES_DIR / "fig3_integrateurs_energie.png")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4 : Comparaison des intégrateurs — |r|(t) par modèle
# ─────────────────────────────────────────────────────────────────────────────

fig4, axes4 = plt.subplots(1, 3, figsize=(15, 5))
fig4.patch.set_facecolor("#0f0f13")
fig4.suptitle(
    "Comparaison des intégrateurs — rayon", color="#e8e8f0", fontsize=13, y=1.01
)

for ax, model_name in zip(axes4, MODELS):
    ax.set_title(model_name, fontsize=10)
    for integ_name, color in COLORS_INTEG.items():
        t = results[model_name][integ_name]["t"]
        r = results[model_name][integ_name]["r"]
        ax.plot(t, np.linalg.norm(r, axis=1), color=color, label=integ_name, alpha=0.85)
    ax.axhline(R_MIN, color="#555566", lw=0.8, ls="--")
    ax.axhline(R_MAX, color="#333344", lw=0.8, ls="--")
    ax.set_xlabel("t (s)")
    ax.set_ylabel("|r| (m)")
    ax.legend()

fig4.tight_layout()
fig4.savefig(
    FIGURES_DIR / "fig4_integrateurs_rayon.png",
    dpi=150,
    bbox_inches="tight",
    facecolor=fig4.get_facecolor(),
)
print(FIGURES_DIR / "fig4_integrateurs_rayon.png")
