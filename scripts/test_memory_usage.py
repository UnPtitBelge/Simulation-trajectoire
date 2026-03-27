#!/usr/bin/env python3
"""Test pour mesurer la consommation mémoire pendant l'entraînement."""

import os
import sys
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model.ml.sim_to_real.model_utils import train_and_evaluate


def test_memory(n_trajs: int, chunk_size: int = 50000):
    """Test la consommation mémoire avec n_trajs trajectoires."""
    print(f"\n{'='*70}")
    print(f"Test avec {n_trajs:,} trajectoires (chunk_size={chunk_size:,})")
    print(f"{'='*70}\n")

    # Générer des données de test
    print("Génération des données de test...")
    trajs = np.random.randn(n_trajs, 605, 2).astype(np.float32) * 0.1
    pool_data = {"trajectories": trajs}
    
    data_size_mb = trajs.nbytes / (1024 * 1024)
    print(f"  Taille du dataset: {data_size_mb:.1f} MB\n")

    # Démarrer le suivi mémoire
    tracemalloc.start()
    initial_mem = tracemalloc.get_traced_memory()[0] / (1024 * 1024)

    # Entraîner
    print("Entraînement...")
    result = train_and_evaluate(pool_data, chunk_size=chunk_size)

    # Mesurer la mémoire maximale
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    current_mb = current_mem / (1024 * 1024)
    peak_mb = peak_mem / (1024 * 1024)
    tracemalloc.stop()

    print(f"\n{'='*70}")
    print("📊 RÉSULTATS MÉMOIRE")
    print(f"{'='*70}")
    print(f"  Dataset:           {data_size_mb:>8.1f} MB")
    print(f"  Mémoire initiale:  {initial_mem:>8.1f} MB")
    print(f"  Mémoire actuelle:  {current_mb:>8.1f} MB")
    print(f"  Pic mémoire:       {peak_mb:>8.1f} MB")
    print(f"  Overhead:          {peak_mb - data_size_mb:>8.1f} MB")
    print(f"{'='*70}")
    
    print(f"\n✓ LR  R²=({result['metrics_lr']['r2_x']:.3f}, "
          f"{result['metrics_lr']['r2_y']:.3f})")
    print(f"✓ MLP R²=({result['metrics_mlp']['r2_x']:.3f}, "
          f"{result['metrics_mlp']['r2_y']:.3f})")


if __name__ == "__main__":
    # Test avec différentes tailles
    test_memory(10_000, chunk_size=5_000)
    test_memory(50_000, chunk_size=25_000)
    test_memory(100_000, chunk_size=50_000)
