#!/usr/bin/env python3
"""Affiche visuellement quelques trajectoires du dataset pour vérification."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠ Matplotlib non disponible, installation requise:")
    print("  pip install matplotlib")
    sys.exit(1)

from src.model.ml.sim_to_real.data_utils import load_pool, _SYNTHETIC_NPZ


def plot_sample_trajectories(n_samples: int = 9):
    """Affiche un échantillon de trajectoires."""
    print(f"Chargement du dataset: {_SYNTHETIC_NPZ}")
    pool_data = load_pool(_SYNTHETIC_NPZ)
    if pool_data is None:
        print("✗ Échec du chargement")
        return

    trajs = pool_data["trajectories"]
    print(f"✓ {len(trajs):,} trajectoires chargées")

    # Sélectionner des trajectoires de différentes longueurs
    lengths = np.array([len(t) for t in trajs])
    percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    selected_indices = []

    for p in percentiles:
        target_len = np.percentile(lengths, p)
        idx = np.argmin(np.abs(lengths - target_len))
        selected_indices.append(idx)

    # Créer la grille de plots
    fig, axes = plt.subplots(3, 3, figsize=(15, 15))
    fig.suptitle(
        "Échantillon de trajectoires (dataset synthétique)", fontsize=16, y=0.995
    )

    for idx, (traj_idx, percentile) in enumerate(
        zip(selected_indices, percentiles)
    ):
        ax = axes[idx // 3, idx % 3]

        traj = trajs[traj_idx]
        positions = np.asarray(traj, dtype=np.float32)

        # Tracer la trajectoire
        ax.plot(positions[:, 0], positions[:, 1], "b-", linewidth=1, alpha=0.7)
        ax.plot(positions[0, 0], positions[0, 1], "go", markersize=8, label="Début")
        ax.plot(positions[-1, 0], positions[-1, 1], "ro", markersize=8, label="Fin")

        # Conditions initiales
        dt = 0.01
        x0, y0 = positions[0]
        r0 = np.sqrt(x0**2 + y0**2)

        if len(positions) > 1:
            x1, y1 = positions[1]
            vx = (x1 - x0) / dt
            vy = (y1 - y0) / dt
            v0 = np.sqrt(vx**2 + vy**2)
            phi0 = np.degrees(np.arctan2(vy, vx)) % 360

            ax.set_title(
                f"P{percentile} | L={len(traj)} frames\n"
                f"r₀={r0:.3f}m, v₀={v0:.2f}m/s, φ₀={phi0:.0f}°",
                fontsize=10,
            )
        else:
            ax.set_title(f"P{percentile} | L={len(traj)} frames", fontsize=10)

        # Cercle du cône
        circle = plt.Circle((0, 0), 0.5, fill=False, edgecolor="gray", linestyle="--")
        ax.add_patch(circle)

        ax.set_xlim(-0.6, 0.6)
        ax.set_ylim(-0.6, 0.6)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="upper right")

    plt.tight_layout()

    output_path = os.path.join(os.path.dirname(_SYNTHETIC_NPZ), "sample_trajectories.png")
    plt.savefig(output_path, dpi=150)
    print(f"\n✓ Visualisation sauvegardée: {output_path}")
    plt.show()


if __name__ == "__main__":
    if not HAS_MATPLOTLIB:
        sys.exit(1)
    plot_sample_trajectories()
