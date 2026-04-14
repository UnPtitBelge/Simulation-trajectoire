"""Benchmark MLPStepModel — précision vs quantité de données d'entraînement.

Entraîne le modèle depuis zéro sur n chunks (progression géométrique :
1, 2, 4, 8, …, N_total) avec n_epochs passes par contexte, mesure l'erreur
sur un jeu de test **indépendant des chunks d'entraînement** (trajectoires
fraîches générées avec seed=999), et trace une trajectoire de référence
(preset par défaut) pour la visualisation.

Note : chaque contexte réentraîne le MLP de zéro. Le temps de calcul
croît avec le nombre de chunks × epochs — réduire --n-contexts ou
--epochs si le benchmark est trop lent.

Usage :
    python src/scripts/benchmark_mlp.py
    python src/scripts/benchmark_mlp.py --max-chunks 50 --epochs 2
    python src/scripts/benchmark_mlp.py --n-contexts 10 --n-test 30
    python src/scripts/benchmark_mlp.py --n-highlight 4 --workers 4
    python src/scripts/benchmark_mlp.py --output figures/mlp.png
    python src/scripts/benchmark_mlp.py --no-plot --output results/mlp.csv
"""

import argparse
import concurrent.futures as cf
import sys
import time
import warnings
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from sklearn.exceptions import ConvergenceWarning

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.loader import load_config
from ml.models import MLPStepModel, state_to_features
from ml.predict import predict_trajectory
from ml.train import fit_shared_scalers
from physics.cone import compute_cone
from scripts.generate_data import _sample_initial_conditions
from utils.angle import v0_dir_to_vr_vtheta

warnings.filterwarnings("ignore", category=ConvergenceWarning)


# ── Entraînement ───────────────────────────────────────────────────────────────


def _load_chunk(path: Path):
    data = np.load(path)
    return (
        state_to_features(data["X"].astype(np.float32)),
        state_to_features(data["y"].astype(np.float32)),
    )


def _train(chunk_paths: list[Path], scaler_X, scaler_y, n_epochs: int) -> MLPStepModel:
    """Entraîne MLPStepModel depuis zéro sur les chunks donnés.

    n_epochs passes avec shuffle des chunks à chaque epoch.
    """
    model = MLPStepModel()
    model.inject_scalers(scaler_X, scaler_y)
    rng = np.random.default_rng(0)
    for _ in range(n_epochs):
        for idx in rng.permutation(len(chunk_paths)):
            X, y = _load_chunk(chunk_paths[int(idx)])
            model.partial_fit(X, y)
    return model


# ── Jeu de test indépendant ────────────────────────────────────────────────────


def _generate_test_cases(
    n: int, phys: dict, gen_cfg: dict, rng: np.random.Generator, n_steps: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Génère n trajectoires de test **jamais vues** par les modèles.

    Les trajectoires sont simulées à la volée (pas depuis les chunks pré-calculés)
    avec le générateur rng fourni (seed=999, distinct du seed d'entraînement).

    Retourne [(init_state, true_traj), …].
    """
    min_steps = gen_cfg.get("min_steps", 50)
    merged    = {**phys, **gen_cfg}
    cases: list[tuple[np.ndarray, np.ndarray]] = []
    batch = max(n, 64)
    while len(cases) < n:
        r0, th0, vr0, vth0 = _sample_initial_conditions(batch, merged, rng)
        for i in range(batch):
            if len(cases) >= n:
                break
            traj = compute_cone(
                r0=float(r0[i]), theta0=float(th0[i]),
                vr0=float(vr0[i]), vtheta0=float(vth0[i]),
                R=phys["R"], depth=phys["depth"],
                friction=phys["friction"], g=phys["g"],
                dt=phys["dt"], n_steps=n_steps,
            )
            if len(traj) >= min_steps:
                cases.append((traj[0].astype(float), traj))
    return cases


# ── Métriques ──────────────────────────────────────────────────────────────────


def _errors(pred: np.ndarray, true: np.ndarray) -> dict:
    n = min(len(pred), len(true))
    d = np.abs(pred[:n] - true[:n])
    return {
        "n_pred":     len(pred),
        "n_true":     len(true),
        "mae_r":      float(d[:, 0].mean()),
        "mae_theta":  float(d[:, 1].mean()),
        "mae_vr":     float(d[:, 2].mean()),
        "mae_vtheta": float(d[:, 3].mean()),
        "mae_total":  float(d.mean()),
    }


def _mean_errors(
    model: MLPStepModel,
    test_cases: list[tuple[np.ndarray, np.ndarray]],
    n_steps: int,
    r_max: float,
    r_min: float,
    v_stop: float,
) -> dict:
    """Moyenne des métriques sur tous les cas de test."""
    all_errs = [
        _errors(
            predict_trajectory(model, init, n_steps, r_max=r_max, r_min=r_min, v_stop=v_stop),
            true_traj,
        )
        for init, true_traj in test_cases
    ]
    return {
        "n_pred":     float(np.mean([e["n_pred"]     for e in all_errs])),
        "n_true":     float(np.mean([e["n_true"]     for e in all_errs])),
        "mae_r":      float(np.mean([e["mae_r"]      for e in all_errs])),
        "mae_theta":  float(np.mean([e["mae_theta"]  for e in all_errs])),
        "mae_vr":     float(np.mean([e["mae_vr"]     for e in all_errs])),
        "mae_vtheta": float(np.mean([e["mae_vtheta"] for e in all_errs])),
        "mae_total":  float(np.mean([e["mae_total"]  for e in all_errs])),
    }


# ── Progression géométrique ────────────────────────────────────────────────────


def _geom_steps(n_total: int, n_steps: int) -> list[int]:
    """Entiers uniques de 1 à n_total en progression géométrique."""
    raw = np.geomspace(1, n_total, n_steps)
    return sorted(set(max(1, int(round(v))) for v in raw))


# ── Workers parallèles ─────────────────────────────────────────────────────────

_shared: dict = {}


def _init_worker(
    all_chunks: list,
    scaler_X,
    scaler_y,
    n_epochs: int,
    test_cases: list,
    ref_init: np.ndarray,
    n_steps_pred: int,
    r_max: float,
    r_min: float,
    v_stop: float,
) -> None:
    """Copie les données partagées dans chaque processus worker (une seule fois)."""
    _shared["all_chunks"]  = all_chunks
    _shared["scaler_X"]    = scaler_X
    _shared["scaler_y"]    = scaler_y
    _shared["n_epochs"]    = n_epochs
    _shared["test_cases"]  = test_cases
    _shared["ref_init"]    = ref_init
    _shared["n_steps"]     = n_steps_pred
    _shared["r_max"]       = r_max
    _shared["r_min"]       = r_min
    _shared["v_stop"]      = v_stop


def _run_step(n: int) -> tuple[int, dict, np.ndarray, float]:
    """Entraîne et évalue le MLP sur les n premiers chunks."""
    t0    = time.perf_counter()
    model = _train(
        _shared["all_chunks"][:n],
        _shared["scaler_X"],
        _shared["scaler_y"],
        _shared["n_epochs"],
    )
    # Métriques moyennées sur le jeu de test indépendant
    errs = _mean_errors(
        model, _shared["test_cases"],
        _shared["n_steps"], _shared["r_max"], _shared["r_min"], _shared["v_stop"],
    )
    # Prédiction sur le preset uniquement pour la visualisation XY / r(t)
    ref_traj = predict_trajectory(
        model, _shared["ref_init"], _shared["n_steps"],
        r_max=_shared["r_max"], r_min=_shared["r_min"], v_stop=_shared["v_stop"],
    )
    return n, errs, ref_traj, time.perf_counter() - t0


# ── Visualisation ──────────────────────────────────────────────────────────────


def _save_csv(steps: list[int], errors: list[dict], csv_path: Path) -> None:
    """Exporte les métriques du benchmark en CSV pour les tableaux du rapport."""
    import csv
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["n_chunks", "mae_r", "mae_total", "n_pred", "n_true"])
        w.writeheader()
        for n, e in zip(steps, errors):
            w.writerow({"n_chunks": n, **{k: e[k] for k in ("mae_r", "mae_total", "n_pred", "n_true")}})
    print(f"CSV sauvegardé : {csv_path}")


def _plot(
    steps: list[int],
    errors: list[dict],
    trajs: dict[int, np.ndarray],
    ref_true: np.ndarray,
    highlight: list[int],
    R: float,
    dt: float,
    n_epochs: int,
    n_test: int,
    output: Path | None = None,
) -> None:
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"Benchmark MLPStepModel ({n_epochs} epoch(s)) — précision vs quantité de données\n"
        f"(métriques moyennées sur {n_test} trajectoires de test indépendantes — "
        "progression géométrique du nombre de chunks d'entraînement)",
        fontsize=12,
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32)

    n_arr   = np.array(steps)
    mae_r   = np.array([e["mae_r"]    for e in errors])
    mae_tot = np.array([e["mae_total"] for e in errors])
    n_pred  = np.array([e["n_pred"]   for e in errors])
    n_true  = errors[0]["n_true"]

    palette = plt.cm.plasma(np.linspace(0.1, 0.9, len(highlight)))  # type: ignore

    # ── MAE vs chunks ─────────────────────────────────────────────────────
    ax_mae = fig.add_subplot(gs[0, 0])
    ax_mae.plot(n_arr, mae_r,   color="steelblue",  linewidth=2,   label="MAE r (m)")
    ax_mae.plot(n_arr, mae_tot, color="darkorange",  linewidth=1.5, linestyle="--",
                label="MAE total")
    for i, n in enumerate(highlight):
        ax_mae.axvline(n, color=palette[i], linestyle=":", linewidth=1, alpha=0.6)
    ax_mae.set_xscale("log")
    ax_mae.set_title("Erreur MAE vs chunks d'entraînement")
    ax_mae.set_xlabel("Chunks (échelle log)")
    ax_mae.set_ylabel("MAE (m)")
    ax_mae.legend(fontsize=9)
    ax_mae.grid(True, alpha=0.3, which="both")

    # ── Longueur prédite ──────────────────────────────────────────────────
    ax_len = fig.add_subplot(gs[0, 1])
    ax_len.axhline(n_true, color="green", linestyle="--", linewidth=1.5,
                   label=f"Vrai (moy. {n_true:.0f} pas)")
    ax_len.plot(n_arr, n_pred, color="steelblue", linewidth=2, label="Prédit (moy.)")
    for i, n in enumerate(highlight):
        ax_len.axvline(n, color=palette[i], linestyle=":", linewidth=1, alpha=0.6)
    ax_len.set_xscale("log")
    ax_len.set_title("Longueur de trajectoire prédite")
    ax_len.set_xlabel("Chunks (échelle log)")
    ax_len.set_ylabel("Nombre de pas")
    ax_len.legend(fontsize=9)
    ax_len.grid(True, alpha=0.3, which="both")

    # ── Trajectoires XY (preset de référence) ────────────────────────────
    ax_xy = fig.add_subplot(gs[1, 0])
    ang = np.linspace(0, 2 * np.pi, 200)
    ax_xy.plot(R * np.cos(ang), R * np.sin(ang),
               color="gray", linestyle="--", linewidth=1)
    ax_xy.plot(
        ref_true[:, 0] * np.cos(ref_true[:, 1]),
        ref_true[:, 0] * np.sin(ref_true[:, 1]),
        color="green", linewidth=2, label="Vérité terrain (preset)", zorder=5,
    )
    for i, n in enumerate(highlight):
        traj = trajs.get(n)
        if traj is None:
            continue
        ax_xy.plot(
            traj[:, 0] * np.cos(traj[:, 1]),
            traj[:, 0] * np.sin(traj[:, 1]),
            color=palette[i], linewidth=1.2, alpha=0.85, label=f"{n} chunk(s)",
        )
    ax_xy.set_aspect("equal")
    ax_xy.set_title("Trajectoire — vue de dessus (preset)")
    ax_xy.set_xlabel("x (m)")
    ax_xy.set_ylabel("y (m)")
    ax_xy.legend(fontsize=8)
    ax_xy.grid(True, alpha=0.25)

    # ── r(t) ─────────────────────────────────────────────────────────────
    ax_r = fig.add_subplot(gs[1, 1])
    ax_r.plot(np.arange(len(ref_true)) * dt, ref_true[:, 0],
              color="green", linewidth=2, label="Vrai (preset)", zorder=5)
    for i, n in enumerate(highlight):
        traj = trajs.get(n)
        if traj is None:
            continue
        ax_r.plot(np.arange(len(traj)) * dt, traj[:, 0],
                  color=palette[i], linewidth=1.2, alpha=0.85, label=f"{n} chunk(s)")
    ax_r.set_title("r(t) — preset")
    ax_r.set_xlabel("t (s)")
    ax_r.set_ylabel("r (m)")
    ax_r.legend(fontsize=8)
    ax_r.grid(True, alpha=0.25)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=150, bbox_inches="tight")
        print(f"Figure sauvegardée : {output}")

    plt.show()


# ── Main ───────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-chunks", type=int, default=None,
        help="Nombre max de chunks à utiliser (défaut : tous)",
    )
    parser.add_argument(
        "--n-contexts", type=int, default=12,
        help="Nombre de points sur la progression géométrique (défaut : 12)",
    )
    parser.add_argument(
        "--epochs", type=int, default=3,
        help="Passes d'entraînement par contexte (défaut : 3)",
    )
    parser.add_argument(
        "--n-test", type=int, default=20,
        help="Trajectoires de test indépendantes pour moyenner les métriques (défaut : 20)",
    )
    parser.add_argument(
        "--n-highlight", type=int, default=5,
        help="Trajectoires affichées sur les graphes XY/r(t) (défaut : 5)",
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Processus parallèles pour les étapes du benchmark (défaut : 1)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Sauvegarde la figure (.png/.pdf) ou les données (.csv)",
    )
    parser.add_argument(
        "--no-plot", action="store_true",
        help="Ne pas afficher la fenêtre graphique (mode batch)",
    )
    args = parser.parse_args()

    cfg      = load_config("ml")
    phys     = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg  = cfg["synth"]["generation"]
    data_dir = ROOT / cfg["paths"]["synth_data_dir"]
    preset   = cfg["preset"]["default"]

    all_chunks = sorted(data_dir.glob("chunk_*.npz"))
    if not all_chunks:
        print(f"⚠  Aucun chunk dans {data_dir} — lancez generate_data.py d'abord")
        sys.exit(1)

    n_total    = min(args.max_chunks, len(all_chunks)) if args.max_chunks else len(all_chunks)
    all_chunks = all_chunks[:n_total]
    print(f"{n_total} chunks disponibles — {args.epochs} epoch(s) par contexte")

    print("Calibration des scalers…")
    scaler_X, scaler_y = fit_shared_scalers(all_chunks, n_sample=min(20, n_total))

    n_steps_pred = cfg["display"]["n_steps_pred"]
    r_max  = phys["R"]
    r_min  = phys["center_radius"]
    v_stop = phys["v_stop"]

    # ── Jeu de test indépendant (seed distinct des chunks) ────────────────
    print(f"Génération de {args.n_test} trajectoires de test (seed=999, indépendant des chunks)…")
    rng_test   = np.random.default_rng(999)
    test_cases = _generate_test_cases(args.n_test, phys, gen_cfg, rng_test, n_steps_pred)
    print(f"  {len(test_cases)} cas de test prêts\n")

    # ── Trajectoire de référence (preset) pour les plots XY / r(t) ───────
    vr0, vth0 = v0_dir_to_vr_vtheta(preset["v0"], preset["direction_deg"])
    ref_init  = np.array([preset["r0"], preset["theta0"], vr0, vth0])
    ref_true  = compute_cone(
        r0=float(ref_init[0]), theta0=float(ref_init[1]),
        vr0=float(ref_init[2]), vtheta0=float(ref_init[3]),
        R=phys["R"], depth=phys["depth"], friction=phys["friction"],
        g=phys["g"], dt=phys["dt"], n_steps=n_steps_pred,
    )
    print(f"Référence (preset) : {len(ref_true)} pas\n")

    steps = _geom_steps(n_total, args.n_contexts)
    print(f"Étapes ({len(steps)}) : {steps}\n")

    errors: list[dict]            = []
    trajs:  dict[int, np.ndarray] = {}

    n_workers = min(args.workers, len(steps))
    initargs  = (
        all_chunks, scaler_X, scaler_y, args.epochs,
        test_cases, ref_init, n_steps_pred, r_max, r_min, v_stop,
    )
    print(f"{'Chunks':>8}  {'MAE r':>10}  {'MAE total':>10}  {'n_pred moy':>12}  {'n_true moy':>12}  {'temps':>7}")
    print("─" * 70)
    with cf.ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_init_worker,
        initargs=initargs,
    ) as pool:
        for n, errs, traj, elapsed in pool.map(_run_step, steps):
            errors.append(errs)
            trajs[n] = traj
            print(
                f"{n:>8}  {errs['mae_r']:>10.5f}  {errs['mae_total']:>10.5f}"
                f"  {errs['n_pred']:>12.1f}  {errs['n_true']:>12.1f}  {elapsed:>6.2f}s"
            )

    hi_idx    = np.unique(np.round(np.linspace(0, len(steps) - 1, args.n_highlight)).astype(int))
    highlight = [steps[int(i)] for i in hi_idx]

    output_path = Path(args.output) if args.output else None

    if output_path is not None and output_path.suffix == ".csv":
        _save_csv(steps, errors, output_path)
    else:
        fig_path = output_path if output_path else None
        _plot(steps, errors, trajs, ref_true, highlight, r_max, phys["dt"], args.epochs, args.n_test, fig_path)
        if args.no_plot:
            plt.close("all")
