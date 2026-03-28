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

# Tester les modèles ML pré-entraînés (nécessite les .pkl dans data/models/)
python src/scripts/test_ml_models.py

# Tester l'entraînement + prédiction sur données synthétiques
python src/scripts/test_synth_training.py [--chunks N]

# Tester l'entraînement + prédiction sur données de tracking réelles
python src/scripts/test_real_training.py [--test-id N] [--passes N]

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

#### Apprentissage résiduel (résidus)

Les deux modèles (`LinearStepModel`, `MLPStepModel`) apprennent **les résidus** `Δ = feat(s_{t+1}) - feat(s_t)` plutôt que l'état absolu `s_{t+1}`. `predict_step` ajoute le delta prédit aux features courantes puis reconvertit en état polaire.

#### Données réelles — unités pixels

Le pipeline réel (`train_real`, `MLWidget._compute_real`, `test_real_training.py`) travaille **entièrement en pixels/unité-temps** centrés sur le centre du cône (`tracking.center_x/y`). Pas de conversion px→m : toutes les expériences étant enregistrées de la même façon, l'espace pixel est cohérent. `predict_trajectory` est appelé avec `r_max=None` (les données peuvent dépasser R à cause d'une calibration approchée).

#### Nombre de pas — deux paramètres distincts

- `synth.physics.n_steps = 100 000` : génération des chunks synthétiques
- `display.n_steps_pred = 10 000` : borne de prédiction/affichage dans l'UI et les scripts de test

### Pattern BaseSimWidget (toutes les simulations)

Tous les widgets de simulation héritent de `ui/base_sim_widget.py`. Le cycle de vie est :

1. `setup(params)` — lance `_compute()` dans un `QThread` (jamais de Qt dans `_compute`)
2. Signal `compute_done` → `_draw_initial()` dans le thread principal (frame 0)
3. Timer périodique → `_draw(frame)` pour chaque frame suivante

Les sous-classes implémentent : `_compute()`, `_draw_initial()`, `_draw(frame)`, `_add_marker(r, theta)`.

#### Sécurité thread (BaseSimWidget)

- `_Worker.finished = Signal(int)` et `failed = Signal(int, str)` portent le numéro de génération (`gen`).
- Connexion directe aux méthodes `self._on_done` / `self._on_failed` (méthodes d'un `QWidget` dans le thread principal) → Qt choisit automatiquement une **Queued Connection** → callbacks exécutés dans le thread Qt, jamais dans le thread worker.
- Ne pas utiliser de lambdas pour ces connexions : une lambda n'est pas un `QObject`, Qt ne peut pas déterminer son thread et utilise Direct Connection → `_timer.start()` depuis le mauvais thread.
- `_stop()` protège `isRunning()` par `try/except RuntimeError` : `thread.deleteLater` peut supprimer l'objet C++ avant que Python n'ait nettoyé la référence `self._thread`.

### Config → UI (pipeline contrôles)

`ControlsPanel` (`ui/controls.py`) est **entièrement généré depuis le TOML** :
- `cfg["preset"]` → QComboBox avec les noms des presets
- `cfg["ranges"]` → QDoubleSpinBox (min/max) pour chaque paramètre

Signal `params_changed(dict)` → `sim_widget.setup(params)`. Toute modification de paramètre relance la simulation.

### Système de coordonnées

État interne **uniforme** pour cône et membrane : `(r, θ, vr, vθ)` en polaire où `vθ = r·dθ/dt`.

Les modèles ML encodent `θ` comme `(cos θ, sin θ)` pour éviter les discontinuités à ±π (`ml/models.py::state_to_features`).

Convention `v0_dir_to_vr_vtheta` : 0° = tangentiel CCW, 90° = radial sortant.

Les contrôles UI et les presets utilisent `v0` (norme, m/s) + `direction_deg` (angle). La conversion vers `(vr, vθ)` se fait à l'entrée de chaque `_compute()`.

### 3D vs 2D

- **MCU / ML** : `pyqtgraph.PlotWidget` (2D)
- **Cône / Membrane** : `pyqtgraph.opengl.GLViewWidget` (3D) — mesh généré par `_cone_surface_mesh()` / `_membrane_surface_mesh()` à l'init

### Distribution des conditions initiales synthétiques

`generate_data.py::_sample_initial_conditions` échantillonne :
- `r0` : `R * sqrt(U[r_frac², 1])` → densité uniforme en surface (aire ∝ r²)
- `theta0` : `U[0, 2π]`
- Vitesse : **anneau uniforme** — `v0 ~ U(v_min, v_max)`, `direction ~ U(-π, π)` → `vr = v0·sin(dir)`, `vtheta = v0·cos(dir)`. Évite le biais des diagonales du carré `(vr, vtheta) ∈ [-v_max, v_max]²`.
- Trajectoires de moins de `min_steps` pas filtrées (bille sortant immédiatement — peu informatives).

Paramètres dans `[synth.generation]` de `ml.toml` : `v_min`, `v_max`, `min_steps`.

### Entraînement parallèle

`train_synth(n_workers=N)` et `generate_data.py --workers N` utilisent `ProcessPoolExecutor`. Les fonctions workers (`_train_lr_context`, `_train_mlp_context`, `_generate_one_chunk`) sont définies au niveau module (requis pour pickling multiprocessing). Seeds reproductibles via `np.random.SeedSequence`.

## Commits

Après chaque modification (fichier ou ensemble de fichiers liés), créer un commit décrivant précisément ce qui a changé et pourquoi. Un commit par tâche logique — ne pas regrouper des changements sans rapport. Message en français, style impératif court (ex. "Ajoute common.toml pour centraliser la config partagée").

## Maintenance des README

Après toute modification d'un fichier, vérifier si un `README.md` existe dans le même répertoire. Si c'est le cas, lire ce README et déterminer si la modification apportée nécessite une mise à jour de sa documentation (nouvelle fonctionnalité, changement d'interface, modification des paramètres, changement de comportement). Mettre à jour le README si nécessaire.

## Fichiers clés à lire en priorité

| Objectif | Fichier |
|---|---|
| Comprendre le démarrage | `src/app.py` |
| Ajouter une simulation | `src/ui/base_sim_widget.py` |
| Modifier les paramètres UI | `src/config/*.toml` |
| Modifier la physique | `src/physics/cone.py` ou `membrane.py` |
| Modifier le ML | `src/ml/models.py` + `train.py` + `predict.py` |
| Thème / couleurs | `src/config/theme.py` |
