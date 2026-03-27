"""Génération de données synthétiques pour l'entraînement ML.

Génère 1 million de trajectoires sur la surface du cône avec des CI
tirées uniformément (r0 ~ sqrt(U) pour densité uniforme en surface).
Écriture progressive par chunks de N trajectoires pour éviter la saturation RAM.

Usage :
    python scripts/generate_data.py [--config path/to/ml.toml]
"""

import argparse
import gc
import sys
from pathlib import Path

import numpy as np
import tomllib

# Résolution du chemin relatif au script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from physics.cone import compute_cone


def _sample_initial_conditions(n: int, cfg: dict, rng: np.random.Generator):
    """Tire n CI plausibles uniformément sur la surface du cône."""
    R = cfg["R"]
    v_max = cfg.get("v_max", 3.0)

    r0 = R * np.sqrt(rng.uniform(0.0, 1.0, n))  # densité uniforme sur surface
    theta0 = rng.uniform(0.0, 2 * np.pi, n)
    vr0 = rng.uniform(-v_max, v_max, n)
    vtheta0 = rng.uniform(-v_max, v_max, n)
    return r0, theta0, vr0, vtheta0


def _simulate_chunk(r0, theta0, vr0, vtheta0, phys_cfg: dict):
    """Simule un batch de trajectoires, retourne les paires (état_t, état_{t+1})."""
    n = len(r0)
    n_steps = phys_cfg["n_steps"]
    n_pairs = n_steps - 1
    R = phys_cfg["R"]
    depth = phys_cfg["depth"]
    friction = phys_cfg["friction"]
    g = phys_cfg["g"]
    dt = phys_cfg["dt"]

    X_buf = np.empty((n * n_pairs, 4), dtype=np.float32)
    y_buf = np.empty((n * n_pairs, 4), dtype=np.float32)

    for i in range(n):
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
        start = i * n_pairs
        end = start + n_pairs
        X_buf[start:end] = traj[:-1].astype(np.float32)
        y_buf[start:end] = traj[1:].astype(np.float32)

    return X_buf, y_buf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config" / "ml.toml"))
    args = parser.parse_args()

    with open(args.config, "rb") as f:
        cfg = tomllib.load(f)

    phys_cfg = cfg["synth"]["physics"]
    gen_cfg = cfg["synth"]["generation"]
    out_dir = ROOT / cfg["paths"]["synth_data_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    n_total = int(gen_cfg["n_trajectories"])
    chunk_size = int(gen_cfg["chunk_size"])
    n_chunks = (n_total + chunk_size - 1) // chunk_size

    rng = np.random.default_rng(seed=42)
    print(
        f"Génération de {n_total:,} trajectoires en {n_chunks} chunks de {chunk_size:,}..."
    )

    for chunk_idx in range(n_chunks):
        n_this = min(chunk_size, n_total - chunk_idx * chunk_size)
        r0, theta0, vr0, vtheta0 = _sample_initial_conditions(
            n_this, gen_cfg | phys_cfg, rng
        )

        X, y = _simulate_chunk(r0, theta0, vr0, vtheta0, phys_cfg)

        out_path = out_dir / f"chunk_{chunk_idx:05d}.npz"
        np.savez_compressed(out_path, X=X, y=y)

        # Libération explicite de la RAM
        del X, y, r0, theta0, vr0, vtheta0
        gc.collect()

        if (chunk_idx + 1) % 10 == 0 or chunk_idx == n_chunks - 1:
            done = (chunk_idx + 1) * chunk_size
            print(
                f"  [{chunk_idx + 1:>4}/{n_chunks}] {min(done, n_total):>10,} trajectoires — {out_path.name}"
            )

    print(f"\nTerminé. Données écrites dans : {out_dir}")


if __name__ == "__main__":
    main()
