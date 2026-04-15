"""Benchmark direct vs step-by-step sur données synthétiques.

Compare les 4 paradigmes × 4 contextes sur un jeu de test commun de
trajectoires synthétiques générées indépendamment :

  - direct-Ridge   (direct_linear_{ctx}.pkl)
  - direct-MLP     (direct_mlp_{ctx}.pkl)
  - step-Ridge     (synth_linear_{ctx}.pkl)
  - step-MLP       (synth_mlp_{ctx}.pkl)

Métriques :
  mae_r           — erreur absolue moyenne sur r (m) — métrique principale
  stability_pct   — % de trajectoires sans NaN ni divergence (r > 2×R)

Sorties :
  figures/benchmark_direct.png
  results/benchmark_direct.csv

Interprétation attendue :
  - Le paradigme step-by-step bénéficie de chaque pas supplémentaire
    comme exemple d'entraînement → meilleure généralisation à faible contexte.
  - Le paradigme direct est limité par la taille de sortie fixe et l'absence
    de physique non-linéaire dans les features d'entrée.

Usage :
    python src/scripts/benchmark_direct.py
    python src/scripts/benchmark_direct.py --n-test 500
    python src/scripts/benchmark_direct.py --no-plot
"""

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.direct_models import DirectModelBase
from ml.models import LinearStepModel, MLPStepModel
from ml.predict import predict_trajectory
from ml.train_direct import generate_trajectories
from scripts.generate_data import _sample_initial_conditions
from physics.cone import compute_cone


# ── Génération du jeu de test ──────────────────────────────────────────────────


def generate_test_set(
    n: int,
    phys_cfg: dict,
    gen_cfg: dict,
    seed: int = 999,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Génère n paires (CI, trajectoire_physique) indépendantes du train.

    Seed 999 : jamais utilisée pour l'entraînement (train utilise seed 0).
    Retourne [(ic, traj), …] où ic = (r, θ, vr, vθ) et traj de forme (T, 4).
    """
    trajs = generate_trajectories(n, phys_cfg, gen_cfg, np.random.default_rng(seed))
    # Ajoute la CI séparément (traj[0]) pour garder l'interface (ic, traj)
    return [(traj[0].copy(), traj) for traj in trajs]


# ── Évaluation modèle direct ───────────────────────────────────────────────────


def eval_direct(
    model: DirectModelBase,
    test_pairs: list[tuple[np.ndarray, np.ndarray]],
    r_max: float,
) -> tuple[float, float]:
    """Évalue un modèle direct sur le jeu de test. Retourne (mae_r, stability_pct).

    Pour chaque trajectoire de test :
    - Prédit via model.predict(ic) → (target_len, 4)
    - Compare r prédit vs r réel sur min(target_len, len(traj_vraie)) pas
    - Stabilité : pas de NaN et r < 2×R
    """
    mae_r_list: list[float] = []
    stable:     list[bool]  = []

    for ic, ref_traj in test_pairs:
        pred = model.predict(ic)          # (target_len, 4)
        n    = min(model.target_len, len(ref_traj))
        r_pred = pred[:n, 0]
        r_ref  = ref_traj[:n, 0]

        is_stable = (
            not np.any(np.isnan(r_pred))
            and not np.any(np.isinf(r_pred))
            and float(np.max(np.abs(r_pred))) < 2.0 * r_max
        )
        stable.append(is_stable)
        if is_stable:
            mae_r_list.append(float(np.mean(np.abs(r_pred - r_ref))))

    mae_r         = float(np.mean(mae_r_list)) if mae_r_list else float("nan")
    stability_pct = 100.0 * sum(stable) / len(stable) if stable else 0.0
    return mae_r, stability_pct


# ── Évaluation modèle step-by-step ────────────────────────────────────────────


def eval_step(
    model: "LinearStepModel | MLPStepModel",
    test_pairs: list[tuple[np.ndarray, np.ndarray]],
    phys_cfg: dict,
) -> tuple[float, float]:
    """Évalue un modèle step-by-step sur le jeu de test. Retourne (mae_r, stability_pct)."""
    r_max   = float(phys_cfg["R"])
    r_min   = float(phys_cfg.get("center_radius", 0.03))
    v_stop  = float(phys_cfg.get("v_stop", 2e-3))
    n_steps = int(phys_cfg.get("n_steps", 100_000))

    mae_r_list: list[float] = []
    stable:     list[bool]  = []

    for ic, ref_traj in test_pairs:
        traj_pred = predict_trajectory(
            model, ic, n_steps=n_steps, r_max=r_max, r_min=r_min, v_stop=v_stop,
        )
        n = min(len(traj_pred), len(ref_traj))
        if n < 2:
            stable.append(False)
            continue

        r_pred = traj_pred[:n, 0]
        r_ref  = ref_traj[:n, 0]
        is_stable = (
            not np.any(np.isnan(r_pred))
            and not np.any(np.isinf(r_pred))
            and float(np.max(np.abs(r_pred))) < 2.0 * r_max
        )
        stable.append(is_stable)
        if is_stable:
            mae_r_list.append(float(np.mean(np.abs(r_pred - r_ref))))

    mae_r         = float(np.mean(mae_r_list)) if mae_r_list else float("nan")
    stability_pct = 100.0 * sum(stable) / len(stable) if stable else 0.0
    return mae_r, stability_pct


# ── Chargement des modèles ─────────────────────────────────────────────────────


def load_direct(models_dir: Path, ctx: str, algo: str) -> DirectModelBase | None:
    """Charge un modèle direct. Retourne None si absent."""
    path = models_dir / f"direct_{algo}_{ctx}.pkl"
    if not path.exists():
        return None
    return DirectModelBase.load(path)


def load_step(models_dir: Path, ctx: str, algo: str) -> "LinearStepModel | MLPStepModel | None":
    """Charge un modèle step-by-step. Retourne None si absent."""
    path = models_dir / f"synth_{algo}_{ctx}.pkl"
    if not path.exists():
        return None
    cls = LinearStepModel if algo == "linear" else MLPStepModel
    return cls.load(path)


# ── Visualisation ──────────────────────────────────────────────────────────────


def plot_benchmark(
    records: list[dict],
    contexts: list[str],
    output: Path | None,
) -> None:
    """2 panels : MAE r (log) et stabilité vs contexte pour les 4 paradigmes."""
    paradigms = [
        ("direct-Ridge", "o", "steelblue",       "--"),
        ("direct-MLP",   "s", "cornflowerblue",  "--"),
        ("step-Ridge",   "o", "crimson",          "-"),
        ("step-MLP",     "s", "tomato",           "-"),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    fig.suptitle(
        "Direct CI→trajectoire  vs  Step-by-step (résidus)\n"
        "sur données synthétiques — 4 contextes d'entraînement",
        fontsize=11, fontweight="bold",
    )
    x = np.arange(len(contexts))

    def _get(label, metric):
        return [
            next((r[metric] for r in records
                  if r["label"] == label and r["context"] == ctx), np.nan)
            for ctx in contexts
        ]

    for label, marker, color, ls in paradigms:
        mae_vals  = _get(label, "mae_r")
        stab_vals = _get(label, "stability_pct")
        ax1.plot(x, mae_vals,  marker=marker, linestyle=ls, color=color,
                 linewidth=2, markersize=7, label=label)
        ax2.plot(x, stab_vals, marker=marker, linestyle=ls, color=color,
                 linewidth=2, markersize=7, label=label)

    ax1.set_title("MAE r (m) — erreur sur le rayon")
    ax1.set_xticks(x); ax1.set_xticklabels(contexts)
    ax1.set_xlabel("Contexte d'entraînement"); ax1.set_ylabel("MAE r (m)")
    ax1.legend(fontsize=9); ax1.grid(True, alpha=0.3); ax1.set_yscale("log")

    ax2.set_title("Stabilité (% trajectoires sans divergence)")
    ax2.set_xticks(x); ax2.set_xticklabels(contexts)
    ax2.set_xlabel("Contexte d'entraînement"); ax2.set_ylabel("Trajectoires stables (%)")
    ax2.set_ylim(0, 105); ax2.legend(fontsize=9); ax2.grid(True, alpha=0.3)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Figure sauvegardée : {output}")

    plt.show()


# ── Sauvegarde CSV ─────────────────────────────────────────────────────────────


def save_csv(records: list[dict], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return
    fields = list(records[0].keys())
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"CSV sauvegardé : {csv_path}")


# ── Main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark direct vs step-by-step sur données synthétiques."
    )
    parser.add_argument("--n-test", type=int, default=500,
                        help="Trajectoires de test (défaut : 500).")
    parser.add_argument("--output", type=Path,
                        default=ROOT.parent / "figures" / "benchmark_direct.png",
                        help="Chemin de la figure.")
    parser.add_argument("--csv", type=Path,
                        default=ROOT.parent / "results" / "benchmark_direct.csv",
                        help="Chemin du CSV.")
    parser.add_argument("--no-plot", action="store_true",
                        help="Mode batch sans fenêtre graphique.")
    args = parser.parse_args()

    cfg        = load_config("ml")
    phys_cfg   = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg    = cfg["synth"]["generation"]
    ctx_names  = cfg["synth"]["contexts"]["names"]
    models_dir = ROOT / cfg["paths"]["models_dir"]
    r_max      = float(phys_cfg["R"])

    # ── Jeu de test commun ────────────────────────────────────────────────────
    print(f"\nGénération de {args.n_test} trajectoires de test (seed=999)...")
    test_pairs = generate_test_set(args.n_test, phys_cfg, gen_cfg, seed=999)
    print(f"  {len(test_pairs)} trajectoires générées\n")

    if not test_pairs:
        print("⚠  Aucune trajectoire de test générée.")
        return

    # ── Évaluation ────────────────────────────────────────────────────────────
    records: list[dict] = []

    for ctx in ctx_names:
        print(f"[{ctx}]")

        for algo, label in [("linear", "direct-Ridge"), ("mlp", "direct-MLP")]:
            model = load_direct(models_dir, ctx, algo)
            if model is not None:
                mae_r, stab = eval_direct(model, test_pairs, r_max)
                print(f"  {label:<14} : MAE r={mae_r:.5f} m  stab={stab:.1f}%")
                records.append({
                    "label": label, "paradigm": "direct", "algo": algo, "context": ctx,
                    "n_train": model.n_train, "target_len": model.target_len,
                    "mae_r": round(mae_r, 6), "stability_pct": round(stab, 1),
                })
            else:
                print(f"  {label:<14} : modèle absent — skipped")

        for algo, label in [("linear", "step-Ridge"), ("mlp", "step-MLP")]:
            model = load_step(models_dir, ctx, algo)
            if model is not None:
                mae_r, stab = eval_step(model, test_pairs, phys_cfg)
                print(f"  {label:<14} : MAE r={mae_r:.5f} m  stab={stab:.1f}%")
                records.append({
                    "label": label, "paradigm": "step", "algo": algo, "context": ctx,
                    "n_train": None, "target_len": None,
                    "mae_r": round(mae_r, 6), "stability_pct": round(stab, 1),
                })
            else:
                print(f"  {label:<14} : modèle absent — skipped")

        print()

    save_csv(records, args.csv)

    if not args.no_plot:
        plot_benchmark(records, ctx_names, args.output)
    else:
        if records:
            plot_benchmark(records, ctx_names, args.output)
        plt.close("all")

    # ── Résumé console ────────────────────────────────────────────────────────
    print(f"\n{'═' * 64}")
    print(f"  {'Paradigme':<14} {'Contexte':<10} {'MAE r (m)':<14} {'Stabilité':<10}")
    print(f"  {'-' * 54}")
    for r in records:
        print(f"  {r['label']:<14} {r['context']:<10} {r['mae_r']:<14.6f} {r['stability_pct']:.1f}%")
    print(f"{'═' * 64}\n")


if __name__ == "__main__":
    main()
