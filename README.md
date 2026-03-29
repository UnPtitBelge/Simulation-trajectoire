# Simulation Trajectoire

Projet universitaire ULB Ba3 — simulation de trajectoires sur surfaces physiques avec module sim-to-real par apprentissage automatique.

## Prérequis au premier lancement

Générer les données synthétiques puis entraîner les 8 modèles :

```bash
python src/scripts/generate_data.py [--workers N]
python src/scripts/train_models.py  [--workers 8]
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

## Simulations

| Onglet | Physique | Rendu |
|--------|----------|-------|
| MCU | Mouvement circulaire uniforme (analytique) | 2D pyqtgraph |
| Cône | Euler semi-implicite sur surface conique | 3D OpenGL |
| Membrane | Euler semi-implicite sur surface logarithmique | 3D OpenGL |
| ML — Réel | Ridge + MLP entraînés sur CSV de tracking réel | 2D pyqtgraph |
| ML — Synthétique | Mêmes modèles, 4 contextes (1 % / 10 % / 50 % / 100 %) | 2D pyqtgraph |

## Modèles ML

Deux algorithmes entraînés chacun sur quatre contextes (quantités de données) :

| Contexte | Fraction des chunks | Fichiers produits |
|----------|--------------------|--------------------|
| `1pct`   | 1 %  | `synth_linear_1pct.pkl`, `synth_mlp_1pct.pkl` |
| `10pct`  | 10 % | `synth_linear_10pct.pkl`, `synth_mlp_10pct.pkl` |
| `50pct`  | 50 % | `synth_linear_50pct.pkl`, `synth_mlp_50pct.pkl` |
| `100pct` | 100 %| `synth_linear_100pct.pkl`, `synth_mlp_100pct.pkl` |

Les deux algorithmes apprennent les **résidus** `Δ = feat(s_{t+1}) − feat(s_t)` à partir de 9 features physiques `(r, cos θ, sin θ, vr, vθ, vθ²/r, vr·vθ/r, …)`.

## Raccourcis clavier

| Touche | Action | Portée |
|--------|--------|--------|
| `Espace` | Pause / reprendre l'animation | Tous les onglets |
| `R` | Remettre à zéro | Tous les onglets |
| `[` / `]` | Preset précédent / suivant | Tous les onglets |
| `P` | Poser un marqueur (r, θ) | Tous les onglets |
| `L` | Sélectionner le modèle Linéaire | ML uniquement |
| `M` | Sélectionner le modèle MLP | ML uniquement |
| `Ctrl+1/2/3/4` | Contexte 1 % / 10 % / 50 % / 100 % | ML — Synthétique uniquement |

## Scripts

| Script | Rôle |
|--------|------|
| `generate_data.py` | Génère les chunks synthétiques (`data/synthetic/`) |
| `train_models.py` | Entraîne les 8 modèles et les sauvegarde dans `data/models/` |
| `benchmark_linear.py` | Convergence de `LinearStepModel` vs nombre de trajectoires |
| `benchmark_mlp.py` | Convergence de `MLPStepModel` vs nombre de chunks |
| `test_simulations.py` | Valide les simulateurs physiques |
| `test_ml_models.py` | Teste les modèles pré-entraînés (`.pkl`) |
| `test_synth_training.py` | Cycle complet entraînement → prédiction sur données synthétiques |
| `test_real_training.py` | Cycle complet entraînement → prédiction sur données réelles |
| `test_data_distribution.py` | Compare distributions des CI (mode aléatoire vs grille) |

Tous s'exécutent depuis la racine du projet : `python src/scripts/<nom>.py [--help]`.

## Structure

```
src/
├── app.py              # Point d'entrée
├── config/             # TOML (common, cone, membrane, mcu, ml) + thème
├── physics/            # Intégrateurs physiques (cone, membrane, mcu)
├── ml/                 # Modèles, entraînement, prédiction
├── ui/                 # Widgets Qt (un fichier par vue)
├── scripts/            # Génération, entraînement, benchmarks, tests
├── tracking/           # Module de tracking vidéo (indépendant)
└── data/               # Généré : synthetic/, models/, tracking_data.csv
```

## Qualité du code

```bash
black src/
flake8 src/
pyright
```
