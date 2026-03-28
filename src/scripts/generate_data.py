"""Génération de données synthétiques pour l'entraînement ML.

Génère 1 million de trajectoires sur la surface du cône avec des CI
tirées uniformément (r0 ~ sqrt(U) pour densité uniforme en surface).
Écriture progressive par chunks de N trajectoires pour éviter la saturation RAM.

Usage :
    python scripts/generate_data.py [--config path/to/ml.toml]
"""

import argparse
import gc
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import tomllib

# Résolution du chemin relatif au script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from physics.cone import compute_cone


def _sample_initial_conditions(n: int, cfg: dict, rng: np.random.Generator):
    """Tire n CI plausibles uniformément sur la surface du cône.

    Vitesse : anneau uniforme (v0 ∈ [v_min, v_max], direction ∈ [-π, π]).
    Cela évite le biais des diagonales du carré (vr, vtheta) ∈ [-v_max, v_max]²
    et garantit que toutes les directions sont équiprobables.
    """
    R             = cfg["R"]
    center_radius = cfg.get("center_radius", 0.03)
    v_min         = cfg.get("v_min", 0.3)
    v_max         = cfg.get("v_max", 2.0)

    # densité uniforme sur surface ; clippé à [center_radius, R) pour éviter r0=0
    r_frac = (center_radius / R) ** 2
    r0     = R * np.sqrt(rng.uniform(r_frac, 1.0, n))
    theta0 = rng.uniform(0.0, 2 * np.pi, n)

    # Vitesse : norme uniforme sur [v_min, v_max], direction uniforme sur [-π, π]
    v0        = rng.uniform(v_min, v_max, n)
    direction = rng.uniform(-np.pi, np.pi, n)
    vr0     = v0 * np.sin(direction)   # même convention que v0_dir_to_vr_vtheta
    vtheta0 = v0 * np.cos(direction)
    return r0, theta0, vr0, vtheta0


def _sample_initial_conditions_grid(cfg: dict):
    """Produit cartésien (r0, θ0, v0, direction) pour une couverture systématique.

    Garantit qu'au moins une trajectoire est lancée depuis chaque position de la
    surface, dans chaque direction et avec chaque vitesse de la grille.

    r0 : linspace en r² → densité uniforme en surface (même principe que le mode random).
    θ0 : équiréparti sur [0, 2π[.
    v0 : linspace sur [v_min, v_max].
    direction : équiréparti sur [-π, π[ → même convention que v0_dir_to_vr_vtheta.

    Total = n_r × n_theta × n_v × n_dir trajectoires.
    """
    R             = cfg["R"]
    center_radius = cfg.get("center_radius", 0.03)
    v_min         = cfg.get("v_min", 0.3)
    v_max         = cfg.get("v_max", 2.0)
    n_r           = int(cfg.get("n_r",     30))
    n_theta       = int(cfg.get("n_theta", 36))
    n_v           = int(cfg.get("n_v",      5))
    n_dir         = int(cfg.get("n_dir",   12))

    r_frac = (center_radius / R) ** 2
    r0_1d  = R * np.sqrt(np.linspace(r_frac, 1.0, n_r, endpoint=False))
    th_1d  = np.linspace(0.0,      2 * np.pi, n_theta, endpoint=False)
    v_1d   = np.linspace(v_min,    v_max,     n_v)
    dir_1d = np.linspace(-np.pi,   np.pi,     n_dir,   endpoint=False)

    g_r, g_th, g_v, g_dir = np.meshgrid(r0_1d, th_1d, v_1d, dir_1d, indexing="ij")
    r0_flat  = g_r.ravel()
    th0_flat = g_th.ravel()
    v0_flat  = g_v.ravel()
    dir_flat = g_dir.ravel()

    vr0     = v0_flat * np.sin(dir_flat)
    vtheta0 = v0_flat * np.cos(dir_flat)
    return r0_flat, th0_flat, vr0, vtheta0


def _simulate_chunk(r0, theta0, vr0, vtheta0, phys_cfg: dict, gen_cfg: dict):
    """Simule un batch de trajectoires, retourne les paires (état_t, état_{t+1}).

    Les trajectoires peuvent être plus courtes que n_steps si la bille sort du
    cône (early exit dans compute_cone). Les listes absorbent cette variabilité.
    """
    n_steps  = phys_cfg["n_steps"]
    R        = phys_cfg["R"]
    depth    = phys_cfg["depth"]
    friction = phys_cfg["friction"]
    g        = phys_cfg["g"]
    dt       = phys_cfg["dt"]

    min_steps = gen_cfg.get("min_steps", 50)

    X_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []

    for i in range(len(r0)):
        traj = compute_cone(
            r0=float(r0[i]),
            theta0=float(theta0[i]),
            vr0=float(vr0[i]),
            vtheta0=float(vtheta0[i]),
            R=R,
            depth=depth,
            friction=friction,
            g=g,
            dt=dt,
            n_steps=n_steps,
        )
        if len(traj) >= max(2, min_steps):
            X_parts.append(traj[:-1].astype(np.float32))
            y_parts.append(traj[1:].astype(np.float32))

    if not X_parts:
        return np.empty((0, 4), np.float32), np.empty((0, 4), np.float32)
    return np.vstack(X_parts), np.vstack(y_parts)


def _generate_one_chunk(
    chunk_idx: int,
    n_this: int,
    phys_cfg: dict,
    gen_cfg: dict,
    seed: np.random.SeedSequence,
    out_dir: str,
) -> tuple[int, int]:
    """Worker random : génère et sauvegarde un chunk. Retourne (chunk_idx, n_pairs).

    Doit être défini au niveau module pour être picklable par multiprocessing.
    """
    rng = np.random.default_rng(seed)
    overlap = set(gen_cfg) & set(phys_cfg)
    assert not overlap, f"Clés communes entre gen_cfg et phys_cfg : {overlap!r}"
    r0, theta0, vr0, vtheta0 = _sample_initial_conditions(n_this, {**gen_cfg, **phys_cfg}, rng)
    X, y = _simulate_chunk(r0, theta0, vr0, vtheta0, phys_cfg, gen_cfg)
    out_path = Path(out_dir) / f"chunk_{chunk_idx:05d}.npz"
    np.savez_compressed(out_path, X=X, y=y)
    del r0, theta0, vr0, vtheta0
    gc.collect()
    return chunk_idx, len(X)


def _generate_grid_chunk(
    chunk_idx: int,
    r0: np.ndarray,
    theta0: np.ndarray,
    vr0: np.ndarray,
    vtheta0: np.ndarray,
    phys_cfg: dict,
    gen_cfg: dict,
    out_dir: str,
) -> tuple[int, int]:
    """Worker grille : simule une tranche de CI déterministes et sauvegarde le chunk.

    Doit être défini au niveau module pour être picklable par multiprocessing.
    Les CI sont précalculées dans le processus principal et passées directement —
    pas de seed, le résultat est entièrement déterministe.
    """
    X, y = _simulate_chunk(r0, theta0, vr0, vtheta0, phys_cfg, gen_cfg)
    out_path = Path(out_dir) / f"chunk_{chunk_idx:05d}.npz"
    np.savez_compressed(out_path, X=X, y=y)
    del r0, theta0, vr0, vtheta0
    gc.collect()
    return chunk_idx, len(X)


def _run_chunks(chunks_args, workers: int, n_chunks: int) -> None:
    """Exécute les workers (random ou grille) séquentiellement ou en parallèle."""
    if workers == 1:
        for fn, args in chunks_args:
            idx, n_pairs = fn(*args)
            if (idx + 1) % 10 == 0 or idx == n_chunks - 1:
                print(f"  [{idx + 1:>4}/{n_chunks}] chunk_{idx:05d}.npz  ({n_pairs:,} paires)")
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(fn, *args): None for fn, args in chunks_args}
            completed = 0
            for future in as_completed(futures):
                chunk_idx, n_pairs = future.result()
                completed += 1
                if completed % 10 == 0 or completed == n_chunks:
                    print(
                        f"  [{completed:>4}/{n_chunks}] chunk_{chunk_idx:05d}.npz"
                        f"  ({n_pairs:,} paires)"
                    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config" / "ml.toml"))
    parser.add_argument(
        "--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1),
        help="Nombre de processus parallèles (défaut : nb_CPU - 1)",
    )
    parser.add_argument(
        "--mode", choices=["random", "grid"], default="random",
        help=(
            "random (défaut) : CI aléatoires, n_trajectories total. "
            "grid : produit cartésien (r0, θ0, v0, direction) depuis [synth.grid]."
        ),
    )
    args = parser.parse_args()

    with open(args.config, "rb") as f:
        cfg = tomllib.load(f)

    phys_cfg   = cfg["synth"]["physics"]
    gen_cfg    = cfg["synth"]["generation"]
    chunk_size = int(gen_cfg["chunk_size"])
    out_dir    = ROOT / cfg["paths"]["synth_data_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "grid":
        grid_cfg = cfg["synth"]["grid"]
        # Fusionne les clés nécessaires pour _sample_initial_conditions_grid
        merged = {**phys_cfg, **gen_cfg, **grid_cfg}
        r0_all, th0_all, vr0_all, vth0_all = _sample_initial_conditions_grid(merged)
        n_total  = len(r0_all)
        n_chunks = (n_total + chunk_size - 1) // chunk_size
        print(
            f"Mode grille — {n_total:,} trajectoires ({grid_cfg['n_r']} r × "
            f"{grid_cfg['n_theta']} θ × {grid_cfg['n_v']} v × {grid_cfg['n_dir']} dir)"
            f" en {n_chunks} chunks — {args.workers} worker(s)..."
        )
        chunks_args = []
        for i in range(n_chunks):
            start = i * chunk_size
            end   = min(start + chunk_size, n_total)
            chunks_args.append((
                _generate_grid_chunk,
                (i,
                 r0_all[start:end], th0_all[start:end],
                 vr0_all[start:end], vth0_all[start:end],
                 phys_cfg, gen_cfg, str(out_dir)),
            ))
    else:
        n_total  = int(gen_cfg["n_trajectories"])
        n_chunks = (n_total + chunk_size - 1) // chunk_size
        child_seeds = np.random.SeedSequence(42).spawn(n_chunks)
        n_this_list = [min(chunk_size, n_total - i * chunk_size) for i in range(n_chunks)]
        print(
            f"Mode random — {n_total:,} trajectoires en {n_chunks} chunks "
            f"de {chunk_size:,} — {args.workers} worker(s)..."
        )
        chunks_args = [
            (_generate_one_chunk,
             (i, n_this_list[i], phys_cfg, gen_cfg, child_seeds[i], str(out_dir)))
            for i in range(n_chunks)
        ]

    _run_chunks(chunks_args, args.workers, n_chunks)
    print(f"\nTerminé. Données écrites dans : {out_dir}")


if __name__ == "__main__":
    main()
