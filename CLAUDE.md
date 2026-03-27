# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

Always respond in **French**. Code identifiers and technical terms stay in their original form.

## Commands

```bash
# Lancer l'application
python src/app.py

# Générer les données synthétiques (prérequis au lancement)
python src/scripts/generate_data.py [--workers N]

# Entraîner les 6 modèles synthétiques (prérequis au lancement)
python src/scripts/train_models.py [--workers N]   # max utile : --workers 6

# Tester les simulations physiques
python src/scripts/test_simulations.py

# Tester les modèles ML (nécessite les .pkl dans data/models/)
python src/scripts/test_ml_models.py [--preset default|1|2]

# Qualité du code
black src/
flake8 src/
pyright
```

Le répertoire de travail Python est `src/` — tous les imports internes sont relatifs à `src/`.

## Prérequis au lancement

`app.py` vérifie au démarrage la présence de :
- `src/data/tracking_data.csv` (données caméra réelles)
- `src/data/models/synth_{linear,mlp}_{10pct,50pct,100pct}.pkl` (6 modèles)

Sans ces fichiers, une `QMessageBox` bloque le démarrage.

## Architecture

### Flux de données ML (de bout en bout)

```
generate_data.py
  → physics/cone.py (simulateur Euler semi-implicite)
  → data/synthetic/chunk_NNNNN.npz  (X: état_t, y: état_{t+1})

train_models.py
  → ml/train.py::train_synth()  (6 modèles × 3 contextes × 2 algos)
  → data/models/synth_{algo}_{context}.pkl

app.py (au démarrage)
  → ml/train.py::train_real()   (modèles réels, en mémoire seulement)

MLWidget._compute()
  → ml/predict.py::predict_trajectory()  (itère model.predict_step())
  → affichage 2D pyqtgraph
```

### Pattern BaseSimWidget (toutes les simulations)

Tous les widgets de simulation héritent de `ui/base_sim_widget.py`. Le cycle de vie est :

1. `setup(params)` — lance `_compute()` dans un `QThread` (jamais de Qt dans `_compute`)
2. Signal `compute_done` → `_draw_initial()` dans le thread principal (frame 0)
3. Timer périodique → `_draw(frame)` pour chaque frame suivante

Les sous-classes implémentent : `_compute()`, `_draw_initial()`, `_draw(frame)`, `_add_marker(r, theta)`.

### Config → UI (pipeline contrôles)

`ControlsPanel` (`ui/controls.py`) est **entièrement généré depuis le TOML** :
- `cfg["preset"]` → QComboBox avec les noms des presets
- `cfg["ranges"]` → QDoubleSpinBox (min/max) pour chaque paramètre

Signal `params_changed(dict)` → `sim_widget.setup(params)`. Toute modification de paramètre relance la simulation.

### Système de coordonnées

État interne **uniforme** pour cône et membrane : `(r, θ, vr, vθ)` en polaire où `vθ = r·dθ/dt`.

Les modèles ML encodent `θ` comme `(cos θ, sin θ)` pour éviter les discontinuités à ±π (`ml/models.py::state_to_features`).

Convention `v0_dir_to_vr_vtheta` : 0° = tangentiel CCW, 90° = radial sortant.

### 3D vs 2D

- **MCU / ML** : `pyqtgraph.PlotWidget` (2D)
- **Cône / Membrane** : `pyqtgraph.opengl.GLViewWidget` (3D) — mesh généré par `_cone_surface_mesh()` / `_membrane_surface_mesh()` à l'init

### Entraînement parallèle

`train_synth(n_workers=N)` et `generate_data.py --workers N` utilisent `ProcessPoolExecutor`. Les fonctions workers (`_train_lr_context`, `_train_mlp_context`, `_generate_one_chunk`) sont définies au niveau module (requis pour pickling multiprocessing). Seeds reproductibles via `np.random.SeedSequence`.

## Fichiers clés à lire en priorité

| Objectif | Fichier |
|---|---|
| Comprendre le démarrage | `src/app.py` |
| Ajouter une simulation | `src/ui/base_sim_widget.py` |
| Modifier les paramètres UI | `src/config/*.toml` |
| Modifier la physique | `src/physics/cone.py` ou `membrane.py` |
| Modifier le ML | `src/ml/models.py` + `train.py` |
| Thème / couleurs | `src/config/theme.py` |
