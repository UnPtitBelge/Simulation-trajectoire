"""Export consolidé des métriques ML — tous modèles, tous contextes.

Charge les 16 modèles pré-entraînés (data/models/), évalue chacun sur un jeu
de test indépendant (trajectoires synthétiques générées à la volée), et produit
un tableau CSV + résumé console.

Modèles évalués :
  - Step-by-step (8)  : synth_{linear,mlp}_{1pct,10pct,50pct,100pct}.pkl
  - Direct CI→traj (8): direct_{linear,mlp}_{1pct,10pct,50pct,100pct}.pkl

Métriques par (paradigme, algo, contexte) :
  mae_r          — erreur absolue moyenne sur r (m) — métrique principale
  rmse_r         — RMSE sur r (m)
  mae_total      — MAE sur les 4 composantes (r, θ, vr, vθ)
  stability_pct  — % de trajectoires sans NaN ni divergence (r < 2R)
  mean_length    — longueur moyenne des trajectoires prédites (pas)
  ref_length     — longueur moyenne des trajectoires de référence (pas)

Usage :
    python src/scripts/collect_metrics.py
    python src/scripts/collect_metrics.py --n-test 100 --output results/metrics.csv
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.direct_models import DirectModelBase
from ml.models import LinearStepModel, MLPStepModel, StepModelBase
from ml.predict import predict_trajectory
from physics.cone import compute_cone


# ── Génération du jeu de test ──────────────────────────────────────────────────


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


# ── Évaluation modèle step-by-step ────────────────────────────────────────────


def evaluate_step_model(
    model: StepModelBase,
    ics: list[np.ndarray],
    refs: list[np.ndarray],
    phys: dict,
    n_steps_pred: int,
    min_steps: int = 20,
) -> dict:
    """Évalue un modèle step-by-step sur les ICs, retourne un dict de métriques."""
    R = phys["R"]
    center_r = phys.get("center_radius", 0.03)
    v_stop = phys.get("v_stop", 2e-3)

    mae_r_list, rmse_r_list, mae_total_list = [], [], []
    pred_lengths, ref_lengths = [], []
    n_stable = 0

    for ic, ref in zip(ics, refs):
        ref_lengths.append(len(ref))
        if len(ref) < 2:
            pred_lengths.append(0)
            continue

        try:
            pred = predict_trajectory(
                model, ic, n_steps_pred,
                r_max=R, r_min=center_r, v_stop=v_stop,
            )
        except RuntimeError:
            pred_lengths.append(0)
            continue

        n = min(len(pred), len(ref))
        if n < 2:
            pred_lengths.append(len(pred))
            continue

        errors = np.abs(pred[:n] - ref[:n])
        mae_r_list.append(float(np.mean(errors[:, 0])))
        rmse_r_list.append(float(np.sqrt(np.mean(errors[:, 0] ** 2))))
        mae_total_list.append(float(np.mean(errors)))
        pred_lengths.append(len(pred))
        if len(pred) >= min_steps:
            n_stable += 1

    n_total = len(ics)
    n_valid = len(mae_r_list)
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


# ── Évaluation modèle direct ───────────────────────────────────────────────────


def evaluate_direct_model(
    model: DirectModelBase,
    ics: list[np.ndarray],
    refs: list[np.ndarray],
    r_max: float,
    min_steps: int = 20,
) -> dict:
    """Évalue un modèle direct (DirectModelBase) sur les ICs, retourne un dict de métriques.

    Le modèle prédit la trajectoire entière en une seule inférence via model.predict(ic).
    La longueur prédite est toujours target_len (fixe).
    """
    target_len = model.target_len

    mae_r_list, rmse_r_list, mae_total_list = [], [], []
    pred_lengths, ref_lengths = [], []
    n_stable = 0

    for ic, ref in zip(ics, refs):
        ref_lengths.append(len(ref))

        # Prédiction via l'API unifiée
        pred = model.predict(ic).astype(np.float64)      # (target_len, 4)

        # Stabilité : pas de NaN/Inf et r < 2R
        r_pred = pred[:, 0]
        is_stable = (
            not np.any(np.isnan(pred))
            and not np.any(np.isinf(pred))
            and float(np.max(np.abs(r_pred))) < 2.0 * r_max
        )
        pred_lengths.append(target_len)
        if is_stable and target_len >= min_steps:
            n_stable += 1

        if not is_stable:
            continue

        # Métriques : sur min(target_len, len(ref)) pas communs
        n = min(target_len, len(ref))
        if n < 2:
            continue

        errors = np.abs(pred[:n] - ref[:n])
        mae_r_list.append(float(np.mean(errors[:, 0])))
        rmse_r_list.append(float(np.sqrt(np.mean(errors[:, 0] ** 2))))
        mae_total_list.append(float(np.mean(errors)))

    n_total = len(ics)
    n_valid = len(mae_r_list)
    return {
        "n_test":        n_total,
        "n_valid":        n_valid,
        "mae_r":          float(np.mean(mae_r_list))    if mae_r_list    else float("nan"),
        "rmse_r":         float(np.mean(rmse_r_list))   if rmse_r_list   else float("nan"),
        "mae_total":      float(np.mean(mae_total_list)) if mae_total_list else float("nan"),
        "stability_pct":  100.0 * n_stable / n_total    if n_total > 0   else 0.0,
        "mean_length":    float(target_len),
        "ref_length":     float(np.mean(ref_lengths))   if ref_lengths   else 0.0,
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collecte les métriques de tous les modèles ML pré-entraînés."
    )
    parser.add_argument("--n-test", type=int, default=200,
                        help="Trajectoires de test par modèle (défaut : 200)")
    parser.add_argument("--n-steps-pred", type=int, default=10000,
                        help="Horizon de prédiction max pour les modèles step (défaut : 10000)")
    parser.add_argument("--min-steps", type=int, default=20,
                        help="Longueur min pour compter comme 'stable' (défaut : 20)")
    parser.add_argument("--seed", type=int, default=999,
                        help="Graine aléatoire (défaut : 999 — indépendante du train)")
    parser.add_argument("--output", type=Path, default=ROOT.parent / "results" / "metrics.csv",
                        help="Chemin du CSV de sortie (défaut : <projet>/results/metrics.csv)")
    args = parser.parse_args()

    cfg  = load_config("ml")
    phys = {**cfg["physics"], **cfg["synth"]["physics"]}
    R    = float(phys["R"])
    models_dir = ROOT / cfg["paths"]["models_dir"]
    contexts   = cfg["synth"]["contexts"]["names"]

    # ── Jeu de test et trajectoires de référence (générés une seule fois) ─────
    rng  = np.random.default_rng(args.seed)
    ics  = _generate_test_ics(args.n_test, phys, rng)
    print(f"Jeu de test : {len(ics)} ICs (seed={args.seed})")
    print("Calcul des trajectoires de référence...")
    refs = [_reference_trajectory(ic, phys) for ic in ics]
    print(f"  {len(refs)} trajectoires physiques calculées\n")

    rows: list[dict] = []

    # ── 1. Modèles step-by-step ───────────────────────────────────────────────
    print("── Modèles step-by-step ──────────────────────────────────")
    algos_step = [("linear", LinearStepModel), ("mlp", MLPStepModel)]

    for algo_name, _ in algos_step:
        for ctx in contexts:
            pkl_path = models_dir / f"synth_{algo_name}_{ctx}.pkl"
            if not pkl_path.exists():
                print(f"  [SKIP] {pkl_path.name} — fichier absent")
                continue

            print(f"  {algo_name:>6} / {ctx:>6} ...", end=" ", flush=True)
            model = StepModelBase.load(pkl_path)
            m = evaluate_step_model(model, ics, refs, phys, args.n_steps_pred, args.min_steps)
            m.update({"paradigm": "step", "algo": algo_name, "context": ctx})
            rows.append(m)
            print(
                f"MAE(r)={m['mae_r']:.5f}  RMSE(r)={m['rmse_r']:.5f}"
                f"  stab={m['stability_pct']:.1f}%  len={m['mean_length']:.0f}"
            )

    # ── 2. Modèles directs ────────────────────────────────────────────────────
    print("\n── Modèles directs CI→trajectoire ───────────────────────")
    algos_direct = ["linear", "mlp"]

    for algo_name in algos_direct:
        for ctx in contexts:
            pkl_path = models_dir / f"direct_{algo_name}_{ctx}.pkl"
            if not pkl_path.exists():
                print(f"  [SKIP] {pkl_path.name} — fichier absent")
                continue

            print(f"  {algo_name:>6} / {ctx:>6} ...", end=" ", flush=True)
            model = DirectModelBase.load(pkl_path)
            m = evaluate_direct_model(model, ics, refs, R, args.min_steps)
            m.update({"paradigm": "direct", "algo": algo_name, "context": ctx})
            rows.append(m)
            print(
                f"MAE(r)={m['mae_r']:.5f}  RMSE(r)={m['rmse_r']:.5f}"
                f"  stab={m['stability_pct']:.1f}%  len={m['mean_length']:.0f}"
                f"  (target={model.target_len} pas)"
            )

    if not rows:
        print("\nAucun modèle trouvé. Lancer train_models.py et train_direct_models.py d'abord.")
        return

    # ── Tableau console ────────────────────────────────────────────────────────
    print(f"\n{'═' * 92}")
    print(f"  {'Paradigme':<10} {'Algo':<8} {'Ctx':<8} {'MAE(r)':>9} {'RMSE(r)':>9} "
          f"{'MAE_tot':>9} {'Stable%':>8} {'Len pred':>9} {'Len ref':>9}")
    print(f"{'─' * 92}")
    last_paradigm = None
    for r in rows:
        if r["paradigm"] != last_paradigm:
            if last_paradigm is not None:
                print(f"{'─' * 92}")
            last_paradigm = r["paradigm"]
        print(
            f"  {r['paradigm']:<10} {r['algo']:<8} {r['context']:<8}"
            f"  {r['mae_r']:>8.5f}  {r['rmse_r']:>8.5f}"
            f"  {r['mae_total']:>8.5f}  {r['stability_pct']:>7.1f}%"
            f"  {r['mean_length']:>8.0f}  {r['ref_length']:>8.0f}"
        )
    print(f"{'═' * 92}")

    if args.output is not None:
        fieldnames = ["paradigm", "algo", "context", "n_test", "n_valid",
                      "mae_r", "rmse_r", "mae_total",
                      "stability_pct", "mean_length", "ref_length"]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"\nCSV sauvegardé : {args.output}")


if __name__ == "__main__":
    main()
