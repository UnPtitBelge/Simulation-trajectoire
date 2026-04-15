"""Export consolidé des métriques ML — tous modèles, tous contextes.

Charge les 8 modèles pré-entraînés (data/models/), évalue chacun sur un jeu
de test indépendant (trajectoires synthétiques générées à la volée), et produit
un tableau CSV + résumé console.

Métriques par (algo, contexte) :
  mae_r          — erreur absolue moyenne sur r (m) — métrique principale
  rmse_r         — RMSE sur r (m)
  mae_total      — MAE sur les 4 composantes (r, θ, vr, vθ)
  stability_pct  — % de trajectoires qui survivent > min_steps pas sans NaN
  mean_length    — longueur moyenne des trajectoires prédites (pas)
  ref_length     — longueur moyenne des trajectoires de référence (pas)

Usage :
    python src/scripts/collect_metrics.py
    python src/scripts/collect_metrics.py --n-test 100 --output results/metrics.csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import LinearStepModel, MLPStepModel, StepModelBase
from ml.predict import predict_trajectory
from physics.cone import compute_cone
from utils.angle import v0_dir_to_vr_vtheta


# ── Génération du jeu de test ─────────────────────────────────────────────────

def _generate_test_ics(n: int, phys: dict, rng: np.random.Generator) -> list[np.ndarray]:
    """Tire n conditions initiales uniformes sur le cône."""
    R = phys["R"]
    center_r = phys.get("center_radius", 0.03)
    v_min, v_max = 0.3, 2.0
    r_frac = (center_r / R) ** 2
    r0 = R * np.sqrt(rng.uniform(r_frac, 1.0, n))
    th0 = rng.uniform(0.0, 2 * np.pi, n)
    v0 = rng.uniform(v_min, v_max, n)
    direction = rng.uniform(-np.pi, np.pi, n)
    vr0 = v0 * np.sin(direction)
    vth0 = v0 * np.cos(direction)
    return [np.array([r0[i], th0[i], vr0[i], vth0[i]]) for i in range(n)]


def _reference_trajectory(ic: np.ndarray, phys: dict) -> np.ndarray:
    """Trajectoire physique de référence depuis une CI."""
    return compute_cone(
        r0=float(ic[0]), theta0=float(ic[1]),
        vr0=float(ic[2]), vtheta0=float(ic[3]),
        R=phys["R"], depth=phys["depth"],
        friction=phys["friction"], g=phys["g"],
        dt=phys["dt"], n_steps=phys["n_steps"],
    )


# ── Évaluation d'un modèle ────────────────────────────────────────────────────

def evaluate_model(
    model: StepModelBase,
    ics: list[np.ndarray],
    phys: dict,
    n_steps_pred: int,
    min_steps: int = 20,
) -> dict:
    """Évalue un modèle sur les ICs, retourne un dict de métriques."""
    R = phys["R"]
    center_r = phys.get("center_radius", 0.03)
    v_stop = phys.get("v_stop", 2e-3)
    dt = phys["dt"]

    mae_r_list, rmse_r_list, mae_total_list = [], [], []
    pred_lengths, ref_lengths = [], []
    n_stable = 0

    for ic in ics:
        ref = _reference_trajectory(ic, phys)
        if len(ref) < 2:
            continue

        try:
            pred = predict_trajectory(
                model, ic, n_steps_pred,
                r_max=R, r_min=center_r, v_stop=v_stop,
            )
        except RuntimeError:
            # NaN/Inf : trajectoire instable
            pred_lengths.append(0)
            ref_lengths.append(len(ref))
            continue

        n = min(len(pred), len(ref))
        if n < 2:
            pred_lengths.append(len(pred))
            ref_lengths.append(len(ref))
            continue

        errors = np.abs(pred[:n] - ref[:n])
        mae_r_list.append(float(np.mean(errors[:, 0])))
        rmse_r_list.append(float(np.sqrt(np.mean(errors[:, 0] ** 2))))
        mae_total_list.append(float(np.mean(errors)))
        pred_lengths.append(len(pred))
        ref_lengths.append(len(ref))
        if len(pred) >= min_steps:
            n_stable += 1

    n_valid = len(mae_r_list)
    n_total = len(ics)
    return {
        "n_test":        n_total,
        "n_valid":        n_valid,
        "mae_r":          float(np.mean(mae_r_list))    if mae_r_list    else float("nan"),
        "rmse_r":         float(np.mean(rmse_r_list))   if rmse_r_list   else float("nan"),
        "mae_total":      float(np.mean(mae_total_list)) if mae_total_list else float("nan"),
        "stability_pct":  100.0 * n_stable / n_total    if n_total > 0   else 0.0,
        "mean_length":    float(np.mean(pred_lengths))  if pred_lengths  else 0.0,
        "ref_length":     float(np.mean(ref_lengths))   if ref_lengths   else 0.0,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collecte les métriques de tous les modèles ML pré-entraînés."
    )
    parser.add_argument("--n-test", type=int, default=50,
                        help="Trajectoires de test par modèle (défaut : 50)")
    parser.add_argument("--n-steps-pred", type=int, default=500,
                        help="Horizon de prédiction max en pas (défaut : 500)")
    parser.add_argument("--min-steps", type=int, default=20,
                        help="Longueur min pour compter comme 'stable' (défaut : 20)")
    parser.add_argument("--seed", type=int, default=999,
                        help="Graine aléatoire (défaut : 999 — indépendante du train)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Chemin du CSV de sortie")
    args = parser.parse_args()

    cfg  = load_config("ml")
    phys = {**cfg["physics"], **cfg["synth"]["physics"]}
    models_dir = ROOT / cfg["paths"]["models_dir"]
    contexts   = cfg["synth"]["contexts"]["names"]

    rng = np.random.default_rng(args.seed)
    ics = _generate_test_ics(args.n_test, phys, rng)
    print(f"Jeu de test : {len(ics)} ICs (seed={args.seed})")

    rows = []
    algos = [("linear", LinearStepModel), ("mlp", MLPStepModel)]

    for algo_name, _ in algos:
        for ctx in contexts:
            pkl_path = models_dir / f"synth_{algo_name}_{ctx}.pkl"
            if not pkl_path.exists():
                print(f"  [SKIP] {pkl_path.name} — fichier absent")
                continue

            print(f"  Évaluation {algo_name:>6} / {ctx:>6} ...", end=" ", flush=True)
            model = StepModelBase.load(pkl_path)
            m = evaluate_model(model, ics, phys, args.n_steps_pred, args.min_steps)
            m.update({"algo": algo_name, "context": ctx})
            rows.append(m)
            print(
                f"MAE(r)={m['mae_r']:.5f}  RMSE(r)={m['rmse_r']:.5f}"
                f"  stab={m['stability_pct']:.1f}%  len={m['mean_length']:.0f}"
            )

    if not rows:
        print("Aucun modèle trouvé. Lancer train_models.py d'abord.")
        return

    # ── Tableau console ────────────────────────────────────────────────────────
    print(f"\n{'═' * 80}")
    print(f"  {'Algo':<8} {'Ctx':<8} {'MAE(r)':>9} {'RMSE(r)':>9} "
          f"{'MAE_tot':>9} {'Stable%':>8} {'Len pred':>9} {'Len ref':>9}")
    print(f"{'─' * 80}")
    for r in rows:
        print(
            f"  {r['algo']:<8} {r['context']:<8}"
            f"  {r['mae_r']:>8.5f}  {r['rmse_r']:>8.5f}"
            f"  {r['mae_total']:>8.5f}  {r['stability_pct']:>7.1f}%"
            f"  {r['mean_length']:>8.0f}  {r['ref_length']:>8.0f}"
        )
    print(f"{'═' * 80}")

    if args.output:
        import csv
        fieldnames = ["algo", "context", "n_test", "n_valid",
                      "mae_r", "rmse_r", "mae_total",
                      "stability_pct", "mean_length", "ref_length"]
        with open(args.output, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"\nCSV sauvegardé : {args.output}")


if __name__ == "__main__":
    main()
