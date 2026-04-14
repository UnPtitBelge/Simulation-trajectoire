"""Analyse de l'accumulation d'erreur des modèles ML en prédiction récursive.

Ce script quantifie comment l'erreur d'un modèle ML croît avec l'horizon
de prédiction — problème fondamental de toute prédiction récursive step-by-step.

Protocole :
  1. Générer N_IC conditions initiales aléatoires couvrant l'espace des états
  2. Pour chaque CI :
       a. Simuler la trajectoire de référence (physique, Euler-Cromer)
       b. Prédire récursivement avec LinearStepModel et MLPStepModel (100pct)
       c. Calculer l'erreur à chaque pas : |r_pred(t) − r_ref(t)|
  3. Calculer et tracer :
       - Erreur médiane sur r en fonction du pas de prédiction
       - Bande [25e-75e percentile] pour quantifier la variance
       - Erreur relative r/R (sans dimension)

Résultat attendu : l'erreur croît de façon super-linéaire — les erreurs
s'accumulent parce que l'état mal prédit au pas t devient l'entrée du pas t+1.

Prérequis :
  - Modèles synthétiques entraînés : data/models/synth_{linear,mlp}_100pct.pkl

Usage :
    python src/scripts/analyze_ml_error.py
    python src/scripts/analyze_ml_error.py --n-ic 100 --horizon 500
    python src/scripts/analyze_ml_error.py --context 50pct --output figures/ml_error.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, MLPStepModel
from ml.predict import predict_with_errors
from physics.cone import compute_cone


# ── Génération des conditions initiales ─────────────────────────────────────────


def sample_initial_conditions(
    cfg: dict, n: int, rng: np.random.Generator,
) -> list[dict]:
    """Tire n conditions initiales dans l'espace valide (r, θ, v, direction).

    Distribution identique à generate_data.py : densité uniforme en surface (√U),
    vitesse et direction uniformes dans l'anneau.
    """
    phys  = cfg["physics"]
    synth = cfg["synth"]
    gen   = synth["generation"]
    R     = phys["R"]
    r_min = phys["center_radius"]
    r_frac = r_min / R

    # Densité uniforme en surface (aire ∝ r²) → r = R * sqrt(U[r_frac², 1])
    u = rng.uniform(r_frac ** 2, 1.0, n)
    r0s = R * np.sqrt(u)
    th0s = rng.uniform(0, 2 * np.pi, n)

    v0s = rng.uniform(gen["v_min"], gen["v_max"], n)
    dirs = rng.uniform(-np.pi, np.pi, n)
    vr0s     = v0s * np.sin(dirs)
    vtheta0s = v0s * np.cos(dirs)

    return [
        {"r0": float(r0s[i]), "theta0": float(th0s[i]),
         "vr0": float(vr0s[i]), "vtheta0": float(vtheta0s[i])}
        for i in range(n)
    ]


# ── Calcul des erreurs ───────────────────────────────────────────────────────────


def compute_error_curves(
    ics: list[dict],
    lr_model: LinearStepModel,
    mlp_model: MLPStepModel,
    cfg: dict,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Pour chaque CI, calcule |r_pred(t) - r_ref(t)| / R pour les deux modèles.

    Retourne (errors_lr, errors_mlp, ref_r_norms, n_valid) où :
      errors_lr / errors_mlp : (n_valid, horizon) — erreurs normalisées par R
      ref_r_norms            : (n_valid, horizon) — r_ref/R (pour contexte)
      n_valid                : nombre de CI dont la référence dure au moins `horizon` pas
    """
    phys  = cfg["physics"]
    synth = cfg["synth"]["physics"]
    R     = phys["R"]

    errors_lr:  list[np.ndarray] = []
    errors_mlp: list[np.ndarray] = []
    ref_norms:  list[np.ndarray] = []

    for ic in ics:
        ref = compute_cone(
            **ic,
            R=R, depth=synth["depth"],
            friction=phys["friction"], g=phys["g"],
            dt=phys["dt"], n_steps=horizon,
            center_radius=phys["center_radius"],
            method="euler_cromer",
        )
        if len(ref) < horizon:
            continue  # Trajectoire trop courte (bille sortie avant horizon)

        init = np.array([ic["r0"], ic["theta0"], ic["vr0"], ic["vtheta0"]])
        _, err_lr  = predict_with_errors(
            lr_model, init, ref,
            r_max=R, r_min=phys["center_radius"], v_stop=phys["v_stop"],
        )
        _, err_mlp = predict_with_errors(
            mlp_model, init, ref,
            r_max=R, r_min=phys["center_radius"], v_stop=phys["v_stop"],
        )

        # Tronque ou padde à `horizon` pas (pad avec NaN si prédiction plus courte)
        def pad(arr: np.ndarray) -> np.ndarray:
            n = len(arr)
            if n >= horizon:
                return arr[:horizon, 0] / R
            padded = np.full(horizon, np.nan)
            padded[:n] = arr[:n, 0] / R
            return padded

        errors_lr.append(pad(err_lr))
        errors_mlp.append(pad(err_mlp))
        ref_norms.append(ref[:horizon, 0] / R)

    if not errors_lr:
        raise RuntimeError("Aucune trajectoire valide de longueur >= horizon. "
                           "Réduire --horizon ou --n-ic.")

    return (
        np.array(errors_lr),
        np.array(errors_mlp),
        np.array(ref_norms),
        len(errors_lr),
    )


# ── Visualisation ────────────────────────────────────────────────────────────────


def plot_error_accumulation(
    errors_lr:  np.ndarray,
    errors_mlp: np.ndarray,
    dt:         float,
    horizon:    int,
    context:    str,
    n_valid:    int,
    output:     Path | None,
) -> None:
    """Graphe d'accumulation d'erreur : médiane + bande inter-quartile."""
    steps = np.arange(horizon)
    t_s   = steps * dt

    def percentiles(arr):
        return (
            np.nanmedian(arr, axis=0),
            np.nanpercentile(arr, 25, axis=0),
            np.nanpercentile(arr, 75, axis=0),
        )

    med_lr,  q25_lr,  q75_lr  = percentiles(errors_lr)
    med_mlp, q25_mlp, q75_mlp = percentiles(errors_mlp)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(
        f"Accumulation d'erreur ML en prédiction récursive — contexte {context}\n"
        f"{n_valid} trajectoires valides  |  dt = {dt} s  |  horizon = {horizon} pas ({horizon*dt:.1f} s)",
        fontsize=11,
    )

    for ax, use_log in zip(axes, [False, True]):
        ax.plot(t_s, med_lr,  color="steelblue",  label="Linéaire (médiane)",  linewidth=2)
        ax.fill_between(t_s, q25_lr,  q75_lr,  alpha=0.2, color="steelblue",  label="Linéaire [Q25-Q75]")
        ax.plot(t_s, med_mlp, color="crimson",    label="MLP (médiane)",       linewidth=2)
        ax.fill_between(t_s, q25_mlp, q75_mlp, alpha=0.2, color="crimson",    label="MLP [Q25-Q75]")

        ax.set_xlabel("Horizon de prédiction (s)")
        ax.set_ylabel("|r_prédit − r_réel| / R")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        if use_log:
            ax.set_yscale("log")
            ax.set_title("Échelle log")
        else:
            ax.set_title("Échelle linéaire")

    plt.tight_layout()

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"\nFigure sauvegardée : {output}")

    plt.show()


def print_error_table(errors_lr: np.ndarray, errors_mlp: np.ndarray, dt: float) -> None:
    """Affiche les médianes d'erreur à quelques horizons clés."""
    horizons = [1, 10, 50, 100, 200, 500]
    print(f"\n{'═' * 52}")
    print(f"  {'Horizon':>8}  {'t (s)':>7}  {'Linéaire':>12}  {'MLP':>12}")
    print(f"  {'(pas)':>8}  {'':>7}  {'méd |Δr|/R':>12}  {'méd |Δr|/R':>12}")
    print(f"{'─' * 52}")
    for h in horizons:
        if h > errors_lr.shape[1]:
            break
        med_lr  = float(np.nanmedian(errors_lr[:, h - 1]))
        med_mlp = float(np.nanmedian(errors_mlp[:, h - 1]))
        print(f"  {h:>8}  {h * dt:>7.2f}  {med_lr:>12.4f}  {med_mlp:>12.4f}")
    print(f"{'═' * 52}\n")


# ── Main ─────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyse de l'accumulation d'erreur ML sur l'horizon de prédiction."
    )
    parser.add_argument("--n-ic",     type=int, default=200,
                        help="Nombre de conditions initiales (défaut : 200)")
    parser.add_argument("--horizon",  type=int, default=300,
                        help="Horizon max en pas (défaut : 300 = 3 s à dt=0.01)")
    parser.add_argument("--context",  type=str, default="100pct",
                        choices=["1pct", "10pct", "50pct", "100pct"],
                        help="Contexte des modèles synthétiques (défaut : 100pct)")
    parser.add_argument("--seed",     type=int, default=42,
                        help="Graine aléatoire (défaut : 42)")
    parser.add_argument("--output",   type=str, default=None,
                        help="Chemin de sauvegarde de la figure")
    args = parser.parse_args()

    cfg      = load_config("ml")
    phys     = cfg["physics"]
    models_dir = ROOT / cfg["paths"]["models_dir"]

    # ── Chargement des modèles synthétiques ──────────────────────────────────
    lr_path  = models_dir / f"synth_linear_{args.context}.pkl"
    mlp_path = models_dir / f"synth_mlp_{args.context}.pkl"

    for p in (lr_path, mlp_path):
        if not p.exists():
            print(f"⚠  Modèle manquant : {p}")
            print("   Lancer : python src/scripts/train_models.py")
            sys.exit(1)

    print(f"\nChargement des modèles (contexte {args.context})...")
    lr_model  = LinearStepModel.load(lr_path)
    mlp_model = MLPStepModel.load(mlp_path)

    # ── Génération des CI ────────────────────────────────────────────────────
    rng = np.random.default_rng(args.seed)
    print(f"Génération de {args.n_ic} conditions initiales (seed={args.seed})...")
    ics = sample_initial_conditions(cfg, args.n_ic, rng)

    # ── Calcul des erreurs ───────────────────────────────────────────────────
    print(f"Calcul des erreurs sur {args.n_ic} trajectoires × horizon {args.horizon} pas...")
    errors_lr, errors_mlp, _, n_valid = compute_error_curves(
        ics, lr_model, mlp_model, cfg, args.horizon,
    )
    print(f"  → {n_valid} trajectoires valides (durée ≥ {args.horizon} pas)")

    print_error_table(errors_lr, errors_mlp, phys["dt"])

    plot_error_accumulation(
        errors_lr, errors_mlp,
        dt=phys["dt"], horizon=args.horizon,
        context=args.context, n_valid=n_valid,
        output=Path(args.output) if args.output else None,
    )
