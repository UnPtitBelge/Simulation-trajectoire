# Simulation Trajectoire

Projet universitaire ULB Ba3 — simulation de trajectoires sur surfaces physiques avec module sim-to-real par apprentissage automatique.

**Question de recherche :** *Comment simuler la réalité avec un ordinateur ?*

Trois approches comparées : simulation physique déterministe, prédiction ML sur données synthétiques, prédiction ML sur données réelles (tracking vidéo).

---

## Prérequis au premier lancement

Générer les données synthétiques, entraîner les modèles step-by-step puis les modèles directs :

```bash
python src/scripts/generate_data.py [--workers N]
python src/scripts/train_models.py  [--workers 8]
python src/scripts/train_direct_models.py
```

Les modèles entraînés sur données réelles (tracking CSV) sont produits automatiquement au lancement de l'app.

## Installation

```bash
pip install -e .          # runtime
pip install -e ".[dev]"   # + outils de dev (pyright, black, flake8, pytest)
```

## Lancement

```bash
python src/app.py
```

Au démarrage, l'app vérifie la présence de `data/tracking_data.csv` et des 8 modèles synthétiques. Un message d'erreur indique les commandes manquantes si les fichiers sont absents.

---

## Simulations

| Onglet | Physique | Rendu |
| --- | --- | --- |
| MCU (analytique) | Solution exacte, orbite circulaire uniforme | 2D pyqtgraph |
| Cône | 3 intégrateurs : Euler, Euler-Cromer (défaut), RK4 | 3D OpenGL |
| Membrane | Euler-Cromer, surface logarithmique (pente variable) | 3D OpenGL |
| ML — Réel | Ridge + MLP entraînés sur CSV de tracking réel | 2D pyqtgraph |
| ML — Synthétique | Ridge + MLP step-by-step, 4 contextes (1 % / 10 % / 50 % / 100 %) | 2D pyqtgraph |
| ML — Direct | Ridge + MLP direct CI→trajectoire, 4 contextes | 2D pyqtgraph |

### Niveaux de précision physique

Le cône et la membrane acceptent trois niveaux cumulatifs, configurables dans `src/config/common.toml` :

| Niveau | Paramètre | Valeur typique | Effet |
| --- | --- | --- | --- |
| 0 (défaut) | — | `rolling = false` | Glissement Coulomb cinétique μ |
| 1 | `rolling = true` | — | Roulement pur, facteur f = 5/7 (sphère pleine) |
| 2 | `rolling_resistance` | 0.001–0.005 | + Résistance au roulement μ_r |
| 3 | `drag_coeff` | 0.01–0.1 m⁻¹ | + Traînée aérodynamique k·\|v\|·v |

---

## Modèles ML

Deux algorithmes entraînés chacun sur quatre contextes (quantités de données) :

| Contexte | Fraction des chunks | Fichiers produits |
| --- | --- | --- |
| `1pct` | 1 % | `synth_linear_1pct.pkl`, `synth_mlp_1pct.pkl` |
| `10pct` | 10 % | `synth_linear_10pct.pkl`, `synth_mlp_10pct.pkl` |
| `50pct` | 50 % | `synth_linear_50pct.pkl`, `synth_mlp_50pct.pkl` |
| `100pct` | 100 % | `synth_linear_100pct.pkl`, `synth_mlp_100pct.pkl` |

Les deux algorithmes apprennent les **résidus** `Δ = feat(s_{t+1}) − feat(s_t)` à partir de 9 features physiques `(r, cos θ, sin θ, vr, vθ, vθ²/r, vr·vθ/r, …)`.

---

## Raccourcis clavier

| Touche | Action | Portée |
| --- | --- | --- |
| `Espace` | Pause / reprendre l'animation | Tous les onglets |
| `R` | Remettre à zéro | Tous les onglets |
| `[` / `]` | Preset précédent / suivant | Tous les onglets |
| `P` | Poser un marqueur (r, θ) | Tous les onglets |
| `L` | Sélectionner le modèle Linéaire | ML uniquement |
| `M` | Sélectionner le modèle MLP | ML uniquement |
| `Ctrl+1/2/3/4` | Contexte 1 % / 10 % / 50 % / 100 % | ML — Synthétique et ML — Direct |

---

## Scripts

### Prérequis et pipeline

```text
generate_data.py  →  train_models.py  →  app.py
```

Les scripts d'analyse scientifique peuvent être lancés indépendamment une fois les prérequis présents.

### Scripts de préparation

| Script | Prérequis | Description |
| --- | --- | --- |
| `generate_data.py` | — | Génère les chunks synthétiques (`data/synthetic/`) |
| `train_models.py` | chunks | Entraîne les 8 modèles → `data/models/` |

```bash
python src/scripts/generate_data.py --workers 4 --mode random
python src/scripts/train_models.py --workers 8
```

### Scripts d'analyse scientifique

| Script | Prérequis | Ce que ça mesure |
| --- | --- | --- |
| `benchmark_integrators.py` | — | Ordre de convergence Euler vs Euler-Cromer vs RK4 en fonction de dt |
| `benchmark_physics_levels.py` | — | Comparaison des 4 niveaux physiques L0–L3 (r(t), énergie, XY) |
| `benchmark_linear.py` | — | Convergence de LinearStepModel vs nombre de trajectoires d'entraînement |
| `benchmark_mlp.py` | chunks | Convergence de MLPStepModel vs nombre de chunks |
| `collect_metrics.py` | modèles `.pkl` | Métriques consolidées (MAE, stabilité, longueur) pour les 8 modèles |
| `analyze_ml_error.py` | modèles `.pkl` | Accumulation d'erreur ML vs horizon de prédiction |
| `ablation_features.py` | chunks | Justification empirique des 9 features (sous-ensembles A→D) |
| `compare_approaches.py` | CSV + modèles | Comparaison physique / ML / réel sur les mêmes CI |

```bash
# Benchmark des intégrateurs numériques (aucun prérequis)
python src/scripts/benchmark_integrators.py
python src/scripts/benchmark_integrators.py --output figures/integrators.png

# Comparaison des 4 niveaux physiques (aucun prérequis)
python src/scripts/benchmark_physics_levels.py
python src/scripts/benchmark_physics_levels.py --output figures/physics_levels.png

# Convergence linéaire (génère ses propres trajectoires à la volée)
python src/scripts/benchmark_linear.py --n-trajectories 5000 --n-test 50
python src/scripts/benchmark_linear.py --no-plot --output results/linear.csv

# Métriques consolidées des 8 modèles (nécessite les .pkl)
python src/scripts/collect_metrics.py --n-test 200 --output results/metrics.csv

# Accumulation d'erreur ML (nécessite les .pkl)
python src/scripts/analyze_ml_error.py --n-ic 500 --horizon 500

# Ablation des features (nécessite les chunks)
python src/scripts/ablation_features.py --n-chunks 20

# Comparaison des 4 approches (nécessite tracking_data.csv + .pkl)
python src/scripts/compare_approaches.py --test-id 5 --output figures/compare.png
```

### Scripts de validation

| Script | Prérequis | Description |
| --- | --- | --- |
| `test_simulations.py` | — | Valide les 4 niveaux physiques et les 3 intégrateurs (cône + membrane) |
| `test_ml_models.py` | modèles `.pkl` | Teste les modèles pré-entraînés sur le preset par défaut |
| `test_synth_training.py` | chunks | Cycle complet entraînement → prédiction sur données synthétiques |
| `test_real_training.py` | CSV | Cycle complet entraînement → prédiction sur données réelles |
| `test_data_distribution.py` | — | Compare distributions CI (mode aléatoire vs grille) |

```bash
python src/scripts/test_simulations.py
python src/scripts/test_synth_training.py --chunks 5
python src/scripts/test_real_training.py --test-id 9
```

### Tests unitaires pytest

```bash
pytest                           # 107 tests (physique, ML, config, prédiction)
pytest src/tests/test_physics.py # uniquement les tests physiques
pytest -k "test_cone"            # filtrer par nom
```

Tous s'exécutent depuis la racine du projet. Chaque script accepte `--help` pour la liste complète des arguments.

---

## Structure

```text
src/
├── app.py              # Point d'entrée
├── config/             # TOML (common, cone, membrane, mcu, ml) + thème
├── physics/            # Intégrateurs physiques (cone.py, membrane.py, mcu.py)
├── ml/                 # Modèles, entraînement, prédiction
├── ui/                 # Widgets Qt (un fichier par vue)
├── scripts/            # Génération, entraînement, benchmarks, tests
├── tracking/           # Module de tracking vidéo (indépendant)
└── data/               # Généré : synthetic/, models/, tracking_data.csv
```

Documentation détaillée par module : [`src/physics/README.md`](src/physics/README.md), [`src/ml/README.md`](src/ml/README.md), [`src/scripts/README.md`](src/scripts/README.md).

---

## Qualité du code

```bash
black src/
flake8 src/
pyright
```
