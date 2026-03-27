# Simulation Trajectoire

Projet universitaire ULB Ba3 — simulation de trajectoires sur surfaces physiques avec module sim-to-real par apprentissage automatique.

## Prérequis

Avant le premier lancement, générer les données synthétiques et entraîner les modèles :

```bash
python refactor/scripts/generate_data.py
python refactor/scripts/train_models.py
```

Les modèles entraînés sur données réelles (tracking CSV) sont produits automatiquement au lancement de l'app.

## Installation

```bash
pip install -e .          # runtime
pip install -e ".[dev]"   # + outils de dev
```

## Lancement

```bash
python refactor/app.py
```

## Simulations

| Onglet | Physique | Rendu |
|--------|----------|-------|
| MCU | Mouvement circulaire uniforme (analytique) | 2D pyqtgraph |
| Cône | Euler semi-implicite sur surface conique | 3D OpenGL |
| Membrane | Verlet sur surface de Laplace | 3D OpenGL |
| ML — Réel | Régression linéaire + MLP entraînés sur CSV de tracking | 2D pyqtgraph |
| ML — Synthétique | Mêmes modèles, 3 contextes (10 % / 50 % / 100 % des données) | 2D pyqtgraph |

Appuyer sur **P** dans n'importe quelle vue pour poser un marqueur de référence (r, θ).

## Structure

```
refactor/
├── app.py                  # Point d'entrée
├── config/                 # Fichiers TOML (mcu, cone, membrane, ml) + thème
├── physics/                # Intégrateurs physiques (cone, membrane, mcu)
├── ml/                     # Modèles ML, prédiction, entraînement
├── ui/                     # Widgets Qt (un fichier par vue)
├── scripts/                # generate_data.py, train_models.py
└── data/                   # Généré : synthetic/, models/, tracking_data.csv
```

## Qualité du code

```bash
black refactor/
flake8 refactor/
pyright refactor/
pytest
```
