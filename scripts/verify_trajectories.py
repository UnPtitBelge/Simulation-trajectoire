#!/usr/bin/env python3
"""Script de vérification du dataset synthétique.

Vérifie que :
1. Les trajectoires sont de vraies simulations complètes (début à fin)
2. La distribution des paramètres initiaux (r0, v0, phi0) est uniforme
3. Les trajectoires sont physiquement cohérentes
"""

import logging
import os
import sys
from datetime import datetime

import numpy as np

# Matplotlib optionnel pour les graphiques
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.model.ml.sim_to_real.data_utils import (
        _SYNTHETIC_NPZ,
        _MIN_TRAJ_LEN,
        load_pool,
        _run_cone,
    )

    log.info("✓ Imports successful")
except ImportError as e:
    log.error(f"✗ Import failed: {e}")
    sys.exit(1)


def verify_trajectory_integrity(trajs: np.ndarray, n_samples: int = 100) -> None:
    """Vérifie que les trajectoires sont de vraies simulations physiques."""
    log.info("\n" + "=" * 70)
    log.info("VÉRIFICATION 1: Intégrité des trajectoires")
    log.info("=" * 70)

    # Vérifier que ce sont des simulations complètes
    issues = []
    total_checked = min(n_samples, len(trajs))

    for i in np.random.choice(len(trajs), total_checked, replace=False):
        traj = trajs[i]
        if len(traj) < 2:
            issues.append(f"Trajectoire {i}: trop courte ({len(traj)} points)")
            continue

        # Vérifier la continuité (pas de sauts brusques)
        positions = np.asarray(traj, dtype=np.float32)
        diffs = np.diff(positions, axis=0)
        distances = np.linalg.norm(diffs, axis=1)

        # Un saut > 1 mètre entre deux frames est suspect (dt=0.01s)
        max_dist = np.max(distances)
        if max_dist > 1.0:
            issues.append(
                f"Trajectoire {i}: saut suspect de {max_dist:.3f}m entre frames"
            )

        # Vérifier que la trajectoire commence près de l'origine
        start_pos = positions[0]
        start_dist = np.linalg.norm(start_pos)
        if start_dist > 1.0:  # La bille commence sur le bord du cône (r < 0.5m)
            issues.append(
                f"Trajectoire {i}: position initiale suspecte à {start_dist:.3f}m"
            )

    if issues:
        log.warning(f"⚠ {len(issues)} problèmes détectés:")
        for issue in issues[:10]:  # Afficher max 10
            log.warning(f"  - {issue}")
        if len(issues) > 10:
            log.warning(f"  ... et {len(issues) - 10} autres")
    else:
        log.info(f"✓ {total_checked} trajectoires vérifiées: toutes valides")

    # Statistiques sur les longueurs
    lengths = [len(t) for t in trajs]
    n_usable = sum(1 for l in lengths if l >= _MIN_TRAJ_LEN)
    log.info(f"\nStatistiques des longueurs:")
    log.info(f"  Total:      {len(trajs):>10,}")
    log.info(f"  Utilisables: {n_usable:>10,} (≥ {_MIN_TRAJ_LEN} frames)")
    log.info(f"  Min:        {min(lengths):>10} frames")
    log.info(f"  Moyenne:    {np.mean(lengths):>10.1f} frames")
    log.info(f"  Médiane:    {np.median(lengths):>10.0f} frames")
    log.info(f"  Max:        {max(lengths):>10} frames")


def extract_initial_conditions(trajs: np.ndarray, n_samples: int = 10000) -> dict:
    """Extrait les conditions initiales approximatives des trajectoires."""
    log.info("\n" + "=" * 70)
    log.info("VÉRIFICATION 2: Distribution des conditions initiales")
    log.info("=" * 70)

    dt = 0.01  # ConeParams.dt par défaut
    total_samples = min(n_samples, len(trajs))

    r0_vals = []
    v0_vals = []
    phi0_vals = []

    log.info(f"Extraction des CI sur {total_samples} échantillons...")
    indices = np.random.choice(len(trajs), total_samples, replace=False)

    for i in indices:
        traj = trajs[i]
        if len(traj) < 2:
            continue

        positions = np.asarray(traj[:2], dtype=np.float32)

        # Position initiale → r0
        x0, y0 = positions[0]
        r0 = np.sqrt(x0**2 + y0**2)

        # Vitesse initiale → v0, phi0
        x1, y1 = positions[1]
        vx = (x1 - x0) / dt
        vy = (y1 - y0) / dt
        v0 = np.sqrt(vx**2 + vy**2)
        phi0 = np.degrees(np.arctan2(vy, vx)) % 360

        r0_vals.append(r0)
        v0_vals.append(v0)
        phi0_vals.append(phi0)

    log.info(f"✓ {len(r0_vals)} CI extraites\n")

    return {
        "r0": np.array(r0_vals),
        "v0": np.array(v0_vals),
        "phi0": np.array(phi0_vals),
    }


def verify_uniform_distribution(ci_data: dict) -> None:
    """Vérifie l'uniformité de la distribution via tests statistiques."""
    log.info("Analyse de l'uniformité:")

    for param, values in ci_data.items():
        log.info(f"\n  {param.upper()}:")
        log.info(f"    Min:     {np.min(values):>8.3f}")
        log.info(f"    Max:     {np.max(values):>8.3f}")
        log.info(f"    Moyenne: {np.mean(values):>8.3f}")
        log.info(f"    Médiane: {np.median(values):>8.3f}")
        log.info(f"    Écart-t: {np.std(values):>8.3f}")

        # Test de Kolmogorov-Smirnov pour uniformité
        from scipy.stats import kstest

        # Normaliser les valeurs dans [0, 1]
        vmin, vmax = np.min(values), np.max(values)
        normalized = (values - vmin) / (vmax - vmin)

        ks_stat, p_value = kstest(normalized, "uniform")
        log.info(f"    KS test: stat={ks_stat:.4f}, p={p_value:.4f}")

        if p_value < 0.05:
            log.warning(f"    ⚠ Distribution non uniforme (p={p_value:.4f})")
        else:
            log.info(f"    ✓ Distribution uniforme (p={p_value:.4f})")


def plot_distributions(ci_data: dict, output_path: str) -> None:
    """Génère des histogrammes de distribution."""
    if not HAS_MATPLOTLIB:
        log.warning("⚠ Matplotlib non disponible, génération de graphiques ignorée")
        return

    log.info("\n" + "=" * 70)
    log.info("Génération des graphiques de distribution...")
    log.info("=" * 70)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(
        "Distribution des conditions initiales (1M trajectoires)", fontsize=14
    )

    params = [
        ("r0", "Position radiale r₀ (m)", (0.08, 0.35)),
        ("v0", "Vitesse initiale v₀ (m/s)", (0.10, 2.50)),
        ("phi0", "Angle initial φ₀ (°)", (0, 360)),
    ]

    for idx, (param, label, expected_range) in enumerate(params):
        values = ci_data[param]

        # Histogramme
        ax_hist = axes[0, idx]
        n, bins, patches = ax_hist.hist(values, bins=50, alpha=0.7, edgecolor="black")
        ax_hist.set_xlabel(label)
        ax_hist.set_ylabel("Fréquence")
        ax_hist.set_title(f"Distribution de {param}")
        ax_hist.axvline(
            np.mean(values), color="red", linestyle="--", label="Moyenne"
        )
        ax_hist.legend()

        # Q-Q plot pour uniformité
        ax_qq = axes[1, idx]
        vmin, vmax = expected_range
        expected_uniform = np.random.uniform(vmin, vmax, len(values))

        sorted_values = np.sort(values)
        sorted_expected = np.sort(expected_uniform)

        ax_qq.scatter(sorted_expected, sorted_values, alpha=0.3, s=1)
        ax_qq.plot(
            [vmin, vmax], [vmin, vmax], "r--", label="Uniforme parfaite"
        )
        ax_qq.set_xlabel(f"{param} attendu (uniforme)")
        ax_qq.set_ylabel(f"{param} observé")
        ax_qq.set_title(f"Q-Q Plot: {param}")
        ax_qq.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    log.info(f"✓ Graphiques sauvegardés: {output_path}")


def compare_with_ground_truth(trajs: np.ndarray, n_samples: int = 10) -> None:
    """Compare quelques trajectoires avec des simulations de référence."""
    log.info("\n" + "=" * 70)
    log.info("VÉRIFICATION 3: Comparaison avec simulation de référence")
    log.info("=" * 70)

    dt = 0.01
    max_error_threshold = 0.010  # 10mm de tolérance (accumulation d'erreurs d'arrondi)

    errors = []
    for i in np.random.choice(len(trajs), n_samples, replace=False):
        traj = trajs[i]
        if len(traj) < 2:
            continue

        positions = np.asarray(traj, dtype=np.float32)

        # Extraire CI
        x0, y0 = positions[0]
        r0 = np.sqrt(x0**2 + y0**2)
        x1, y1 = positions[1]
        vx = (x1 - x0) / dt
        vy = (y1 - y0) / dt
        v0 = np.sqrt(vx**2 + vy**2)
        phi0 = np.degrees(np.arctan2(vy, vx)) % 360

        # Re-simuler avec les mêmes CI
        ref_traj = _run_cone(r0, v0, phi0, n_frames=len(traj))
        ref_positions = np.array(ref_traj, dtype=np.float32)

        # Comparer
        n_compare = min(len(positions), len(ref_positions))
        if n_compare < 2:
            continue

        diff = positions[:n_compare] - ref_positions[:n_compare]
        max_error = np.max(np.linalg.norm(diff, axis=1))
        errors.append(max_error)

    if errors:
        log.info(f"Comparaison sur {len(errors)} trajectoires:")
        log.info(f"  Erreur max moyenne: {np.mean(errors):.6f} m")
        log.info(f"  Erreur max médiane: {np.median(errors):.6f} m")
        log.info(f"  Erreur max maximum: {np.max(errors):.6f} m")

        n_valid = sum(1 for e in errors if e < max_error_threshold)
        log.info(
            f"  {n_valid}/{len(errors)} trajectoires valides "
            f"(erreur < {max_error_threshold*1000}mm)"
        )

        if n_valid == len(errors):
            log.info("  ✓ Toutes les trajectoires sont conformes!")
        else:
            log.warning(
                f"  ⚠ {len(errors) - n_valid} trajectoires avec erreur > seuil"
            )
    else:
        log.warning("  ⚠ Aucune trajectoire vérifiable")


def main() -> int:
    log.info("=" * 70)
    log.info("VÉRIFICATION DU DATASET SYNTHÉTIQUE")
    log.info("=" * 70)
    log.info(f"Source: {_SYNTHETIC_NPZ}\n")

    if not os.path.exists(_SYNTHETIC_NPZ):
        log.error(f"✗ Dataset introuvable: {_SYNTHETIC_NPZ}")
        log.error("Générer d'abord avec: python scripts/generate_synthetic_data.py")
        return 1

    start_time = datetime.now()

    # Charger le dataset
    log.info("Chargement du dataset...")
    pool_data = load_pool(_SYNTHETIC_NPZ)
    if pool_data is None:
        log.error("✗ Échec du chargement")
        return 1

    trajs = pool_data["trajectories"]
    log.info(f"✓ {len(trajs):,} trajectoires chargées\n")

    # 1. Vérifier l'intégrité des trajectoires
    verify_trajectory_integrity(trajs, n_samples=1000)

    # 2. Extraire et analyser la distribution des CI
    ci_data = extract_initial_conditions(trajs, n_samples=10000)
    verify_uniform_distribution(ci_data)

    # 3. Générer les graphiques
    output_path = os.path.join(
        os.path.dirname(_SYNTHETIC_NPZ), "distribution_analysis.png"
    )
    plot_distributions(ci_data, output_path)

    # 4. Comparer avec simulation de référence
    compare_with_ground_truth(trajs, n_samples=50)

    duration = datetime.now() - start_time
    log.info("\n" + "=" * 70)
    log.info(f"✓ Vérification terminée en {duration}")
    log.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
