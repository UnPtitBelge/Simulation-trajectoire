# scripts/

Scripts autonomes pour générer les données, entraîner les modèles, tester les composants
et mesurer les performances. Tous s'exécutent depuis la racine du projet avec
`python src/scripts/<nom>.py`.

---

## Ordre d'exécution recommandé

```
generate_data.py   →   train_models.py   →   app.py
```

Les scripts de test et de benchmark peuvent être lancés à n'importe quel moment
une fois les prérequis présents (voir chaque section).

---

## generate_data.py

**Rôle** : génère les données d'entraînement synthétiques pour le pipeline ML.

Simule des milliers de trajectoires sur la surface du cône (intégrateur Euler
semi-implicite de `physics/cone.py`) et écrit les paires d'états successifs
`(état_t, état_{t+1})` dans des fichiers `chunk_NNNNN.npz` dans `data/synthetic/`.

### Modes de génération

| Mode | Description | Paramètres |
|------|-------------|------------|
| `random` (défaut) | CI tirées aléatoirement — densité uniforme en surface | `[synth.generation]` de `ml.toml` |
| `grid` | Produit cartésien `(r₀, θ₀, v₀, direction)` — couverture systématique | `[synth.grid]` de `ml.toml` |

**Mode random** — distribution des CI :
- `r₀` : `R × √U[r_frac², 1]` → densité uniforme en surface (aire ∝ r²)
- `θ₀` : `U[0, 2π]`
- Vitesse : anneau uniforme `v₀ ∈ [v_min, v_max]`, `direction ∈ [-π, π]` — évite
  le biais des diagonales du carré `(vr, vθ) ∈ [-v_max, v_max]²`

**Filtrage** : les trajectoires de moins de `min_steps` pas sont ignorées
(bille qui sort immédiatement — peu informatives).

**Parallélisme** : `ProcessPoolExecutor` avec `--workers N` processus.
Seeds reproductibles via `np.random.SeedSequence(42)`.

**Niveau physique** : le simulateur utilise les paramètres de `src/config/common.toml [physics]`.
Les clés `rolling`, `rolling_resistance`, `drag_coeff` contrôlent le niveau de précision
(Level 0 glissement par défaut). **Tout changement nécessite de régénérer les chunks et
de réentraîner les modèles** — les chunks existants restent cohérents avec la physique
qui les a produits.

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--workers N` | nb_CPU − 1 | Processus parallèles |
| `--mode {random,grid}` | `random` | Mode de génération des CI |
| `--n-trajectories N` | config | Nombre de trajectoires (mode random uniquement) |
| `--plot` | off | Affiche histogramme et CDF des longueurs après génération |

### Sorties

- `data/synthetic/chunk_NNNNN.npz` — chaque fichier contient deux arrays :
  - `X` : états `(r, θ, vr, vθ)` au pas `t`, shape `(N_paires, 4)`
  - `y` : états au pas `t+1`, même shape

---

## train_models.py

**Rôle** : entraîne les 8 modèles ML synthétiques (2 algorithmes × 4 contextes)
et les sauvegarde dans `data/models/`.

**Prérequis** : chunks dans `data/synthetic/` (lancer `generate_data.py` d'abord).

### Algorithmes et contextes

| Contexte | Fraction des chunks | Modèles produits |
|----------|--------------------|--------------------|
| `1pct`   | 1 %  | `synth_linear_1pct.pkl`, `synth_mlp_1pct.pkl` |
| `10pct`  | 10 % | `synth_linear_10pct.pkl`, `synth_mlp_10pct.pkl` |
| `50pct`  | 50 % | `synth_linear_50pct.pkl`, `synth_mlp_50pct.pkl` |
| `100pct` | 100 %| `synth_linear_100pct.pkl`, `synth_mlp_100pct.pkl` |

Les contextes sont lus depuis `[synth.contexts]` de `ml.toml` — ajouter une entrée
suffit à créer un nouveau modèle sans modifier le code.

### Apprentissage

- **LinearStepModel** (Ridge) : 1 seule passe — les équations normales sont exactes,
  répéter biaise la régularisation.
- **MLPStepModel** : `mlp_n_epochs` passes avec shuffle des chunks + early stopping
  sur `val_fraction` des chunks (patience = `mlp_patience`).
- Scalers `StandardScaler` calibrés une fois sur `n_scaler_chunks` chunks tirés
  uniformément, injectés dans chaque modèle via `inject_scalers()`.

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--workers N` | 1 | Processus parallèles (max utile : 8) |
| `--plot` | off | Affiche les courbes de convergence val MSE MLP |

---

## test_simulations.py

**Rôle** : vérifie les simulateurs physiques (cône et membrane) avec le preset par défaut.

Affiche les statistiques de la trajectoire (durée, r min/max, |v| final, énergie
cinétique) et trace une figure 2×2 : trajectoire XY (colorée par temps) et r(t)/|v|(t)
pour chaque simulateur.

**Prérequis** : aucun (pas de données générées nécessaires).

```bash
python src/scripts/test_simulations.py
```

---

## test_ml_models.py

**Rôle** : charge et teste les modèles pré-entraînés (`.pkl`) sur le preset par défaut.

Charge tous les contextes disponibles pour `linear` et `mlp`, prédit une trajectoire
depuis le preset par défaut, imprime les statistiques (longueur, r, |v|, énergie),
puis trace une figure 2×2 superposant les 4 contextes pour chaque algorithme.

**Prérequis** : fichiers `.pkl` dans `data/models/` (lancer `train_models.py` d'abord).

Les modèles manquants sont signalés sans bloquer l'affichage des modèles présents.

```bash
python src/scripts/test_ml_models.py
```

---

## test_synth_training.py

**Rôle** : teste le cycle complet entraînement → prédiction sur données synthétiques.

Entraîne `LinearStepModel` et `MLPStepModel` depuis zéro sur un sous-ensemble de chunks,
compare les trajectoires prédites à la vérité terrain du simulateur physique, et trace
une figure 2×2 : XY, r(t), |v|(t), erreur |Δr|(t).

**Prérequis** : chunks dans `data/synthetic/`.

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--chunks N` | 10 | Nombre de chunks à utiliser pour l'entraînement |
| `--epochs N` | 3 | Epochs MLP |

### Ce qui est mesuré

- **MAE r, MAE θ, MAE vr, MAE vθ, MAE global** — erreur absolue moyenne sur les pas communs
- Longueur prédite vs vérité terrain (condition d'arrêt physique)

```bash
python src/scripts/test_synth_training.py --chunks 5
```

---

## test_real_training.py

**Rôle** : teste le cycle complet entraînement → prédiction sur données de tracking réel.

Protocole **leave-one-out** : une expérience = jeu de test, les autres = entraînement.
Toutes les unités restent en **pixels/unité-temps** (pas de conversion px→m).

Le centre du cône est estimé par expérience via `compute_exp_centers` (correction
d'offset caméra — la bille finit toujours au même endroit physique).

Trace une figure 2×2 : XY (pixels centrés), r(t) en pixels, |v|(t), erreur |Δr|(t).

**Prérequis** : `data/tracking_data.csv`.

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--test-id N` | dernier expID | ID de l'expérience à utiliser comme test |
| `--passes N` | 3 | Passes d'entraînement MLP |

```bash
python src/scripts/test_real_training.py --test-id 9
```

---

## test_data_distribution.py

**Rôle** : compare les distributions des états d'entraînement entre mode aléatoire et
mode grille, pour valider la couverture de l'espace des phases.

Génère un petit jeu de CI dans chaque mode, simule les trajectoires, et trace :
- Distributions marginales de r (avec la densité uniforme théorique `2r/R²`) et |v|
- Heatmaps 2D de couverture dans l'espace `(r, |v|)`
- Heatmaps 2D de couverture dans l'espace `(vr, vθ)`
- Histogramme des longueurs de trajectoire

**Prérequis** : aucun.

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--n-random N` | 8640 | Trajectoires en mode aléatoire |
| `--n-r N` | 15 | Grille : nombre de rayons |
| `--n-theta N` | 18 | Grille : nombre d'angles |
| `--n-v N` | 4 | Grille : nombre de vitesses |
| `--n-dir N` | 8 | Grille : nombre de directions |

```bash
python src/scripts/test_data_distribution.py --n-random 3000 --n-r 20
```

---

## benchmark_linear.py

**Rôle** : mesure la convergence de `LinearStepModel` en fonction du nombre de
trajectoires d'entraînement, de 1 trajectoire jusqu'à `--n-trajectories`.

### Mécanisme

Les trajectoires sont **générées à la volée** (sans passer par les chunks pré-calculés)
car un chunk (~10 000 paires) suffit déjà à approcher la convergence de Ridge — ce script
descend à l'échelle de la trajectoire individuelle (~100–500 paires).

À chaque étape `n` de la progression géométrique :
1. Un modèle vierge est créé (XᵀX / Xᵀy remis à zéro).
2. `partial_fit` accumule les équations normales sur les `n` premières trajectoires.
3. La solution Ridge `W = (XᵀX + αI)⁻¹ Xᵀy` est calculée sur l'ensemble.

Les scalers sont calibrés **une seule fois** sur la totalité du jeu d'entraînement.

### Évaluation

Les métriques (MAE r, MAE total, longueur prédite) sont **moyennées sur `--n-test`
trajectoires de test** tirées avec `seed=999` (indépendant du train `seed=42`).

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--n-trajectories N` | 2000 | Taille maximale du jeu d'entraînement |
| `--n-contexts N` | 20 | Points sur la progression géométrique |
| `--n-test N` | 20 | Trajectoires de test pour moyenner les métriques |
| `--n-highlight N` | 5 | Trajectoires affichées sur les plots XY / r(t) |
| `--workers N` | 1 | Processus parallèles (max utile : `--n-contexts`) |
| `--output PATH` | — | Sauvegarde la figure (.png/.pdf) ou les données (.csv) |
| `--no-plot` | off | Mode batch sans fenêtre graphique |

### Sorties (figure 2×2)

- MAE r et MAE total vs nombre de trajectoires (échelle log)
- Longueur prédite vs vérité terrain (moy.)
- Trajectoires XY pour quelques points de la progression
- r(t) pour les mêmes points

```bash
python src/scripts/benchmark_linear.py --n-trajectories 5000 --n-test 50
python src/scripts/benchmark_linear.py --no-plot --output results/linear.csv
```

---

## compare_approaches.py

**Rôle** : démonstration centrale du projet — superpose sur un seul graphique les quatre
approches de simulation pour les mêmes conditions initiales (issues d'une expérience réelle) :
simulation physique déterministe, ML linéaire, ML MLP, et tracking réel (référence).

Toutes les courbes sont normalisées par R pour permettre la comparaison directe entre
l'espace physique (mètres) et l'espace pixel (coordonnées caméra).

**Prérequis** : `data/tracking_data.csv`.

**Ce que ce script prouve** : dans quelle mesure chaque approche reproduit la réalité,
et quel écart |r_pred − r_réel| / R persiste en fonction du temps.

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--test-id N` | dernier expID | ID de l'expérience test |
| `--passes N` | 3 | Passes d'entraînement ML |
| `--output PATH` | — | Sauvegarde la figure (.png) |

```bash
python src/scripts/compare_approaches.py
python src/scripts/compare_approaches.py --test-id 5 --output figures/compare.png
```

---

## benchmark_integrators.py

**Rôle** : benchmark de convergence des intégrateurs numériques — justifie le choix de
l'Euler-Cromer pour la simulation du cône.

Compare Euler explicite, Euler-Cromer et RK4 sur une grille de valeurs de `dt`
par rapport à une trajectoire de référence (RK4, dt = 1e-4 s).

**Ce que ce script prouve** :

- Euler et Euler-Cromer convergent en O(dt) (ordre 1) ; RK4 en O(dt⁴) (ordre 4)
- Euler-Cromer a une meilleure constante d'erreur que l'Euler explicite
- Pour dt = 0.01 s (valeur par défaut), RK4 est marginalement plus précis pour un coût CPU 4× plus élevé — Euler-Cromer est le meilleur compromis

**Prérequis** : aucun.

### Arguments

| Argument        | Défaut | Description                                       |
|-----------------|--------|---------------------------------------------------|
| `--output PATH` | —      | Sauvegarde la figure (.png) ou les données (.csv) |
| `--no-plot`     | off    | Mode batch sans fenêtre graphique                 |

```bash
python src/scripts/benchmark_integrators.py
python src/scripts/benchmark_integrators.py --output figures/integrators.png
python src/scripts/benchmark_integrators.py --no-plot --output results/integrators.csv
```

---

## analyze_ml_error.py

**Rôle** : quantifie l'accumulation d'erreur ML en prédiction récursive step-by-step.

Pour N conditions initiales aléatoires, compare la trajectoire prédite par chaque
modèle ML à la trajectoire physique de référence, et trace l'erreur médiane (+ bande
inter-quartile) en fonction de l'horizon de prédiction.

**Ce que ce script prouve** : l'erreur ML n'est pas nulle et croît avec l'horizon car
chaque pas injecte une nouvelle erreur — c'est la limite fondamentale de l'apprentissage
par imitation sur système dynamique récursif.

**Prérequis** : modèles `.pkl` dans `data/models/` (lancer `train_models.py`).

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--n-ic N` | 200 | Nombre de conditions initiales |
| `--horizon N` | 300 | Horizon max en pas (300 = 3 s) |
| `--context` | `100pct` | Contexte d'entraînement des modèles |
| `--seed N` | 42 | Graine aléatoire |
| `--output PATH` | — | Sauvegarde la figure |

```bash
python src/scripts/analyze_ml_error.py
python src/scripts/analyze_ml_error.py --n-ic 500 --horizon 500 --output figures/ml_error.png
```

---

## benchmark_mlp.py

**Rôle** : mesure la convergence de `MLPStepModel` en fonction du nombre de chunks
d'entraînement, de 1 chunk jusqu'à `--max-chunks`.

Contrairement au benchmark linéaire, il utilise les **chunks pré-calculés**
(`data/synthetic/`) car le MLP bénéficie de volumes de données plus importants.

À chaque étape `n` :
1. Un MLP vierge est entraîné depuis zéro sur les `n` premiers chunks.
2. `--epochs` passes avec shuffle des chunks à chaque epoch.
3. Les métriques sont **moyennées sur `--n-test` trajectoires de test indépendantes**
   générées à la volée (seed=999, jamais vues par le modèle).
4. La trajectoire du preset est prédite séparément pour la visualisation.

**Prérequis** : chunks dans `data/synthetic/`.

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--max-chunks N` | tous | Nombre max de chunks à utiliser |
| `--n-contexts N` | 12 | Points sur la progression géométrique |
| `--epochs N` | 3 | Passes par contexte |
| `--n-test N` | 20 | Trajectoires de test indépendantes pour les métriques |
| `--n-highlight N` | 5 | Trajectoires affichées sur les plots XY / r(t) |
| `--workers N` | 1 | Processus parallèles (max utile : `--n-contexts`) |
| `--output PATH` | — | Sauvegarde la figure (.png/.pdf) ou les données (.csv) |
| `--no-plot` | off | Mode batch sans fenêtre graphique |

### Sorties (figure 2×2)

- MAE r et MAE total vs chunks (échelle log)
- Longueur prédite vs vérité terrain
- Trajectoires XY pour quelques points
- r(t) pour les mêmes points

```bash
python src/scripts/benchmark_mlp.py --max-chunks 50 --epochs 2
python src/scripts/benchmark_mlp.py --no-plot --output results/mlp.csv
```

---

## benchmark_physics_levels.py

**Rôle** : compare les 4 niveaux de précision physique (L0–L3) sur le cône et la membrane.

Pour chaque simulateur, trace r(t)/R, énergie cinétique normalisée E(t)/E₀ et trajectoires
XY dans l'espace normalisé r/R, pour les 4 niveaux :

- L0 : glissement Coulomb (défaut)
- L1 : roulement pur (facteur 5/7)
- L2 : roulement + résistance au roulement (μr·g·cosβ)
- L3 : roulement + résistance + traînée quadratique (k·|v|·v)

La condition initiale est à la vitesse orbitale (trajectoire quasi-circulaire stable sans
friction) pour maximiser le contraste entre niveaux.

**Prérequis** : aucun.

### Arguments (benchmark_physics_levels)

| Argument        | Défaut | Description                                       |
| --------------- | ------ | ------------------------------------------------- |
| `--output PATH` | —      | Sauvegarde la figure (.png) ou les données (.csv) |
| `--no-plot`     | off    | Mode batch sans fenêtre graphique                 |

```bash
python src/scripts/benchmark_physics_levels.py
python src/scripts/benchmark_physics_levels.py --output figures/physics_levels.png
python src/scripts/benchmark_physics_levels.py --no-plot --output results/physics_levels.csv
```

---

## collect_metrics.py

**Rôle** : consolide les métriques de prédiction ML pour les 8 modèles pré-entraînés
(2 algorithmes × 4 contextes) en une seule table CSV.

Pour N conditions initiales de test, prédit une trajectoire avec chaque modèle et calcule :
`mae_r`, `rmse_r`, `mae_total` (erreur sur les 4 composantes), `stability_pct` (fraction
de trajectoires qui ne divergent pas), `mean_length` (longueur prédite), `ref_length`
(longueur physique de référence).

**Prérequis** : fichiers `.pkl` dans `data/models/` (lancer `train_models.py`).

### Arguments (collect_metrics)

| Argument           | Défaut | Description                                       |
| ------------------ | ------ | ------------------------------------------------- |
| `--n-test N`       | 100    | Conditions initiales de test                      |
| `--n-steps-pred N` | 500    | Horizon max de prédiction                         |
| `--min-steps N`    | 50     | Longueur minimale pour comptabiliser une IC       |
| `--seed N`         | 999    | Graine aléatoire (indépendante du train)          |
| `--output PATH`    | —      | Sauvegarde les métriques (.csv)                   |

```bash
python src/scripts/collect_metrics.py
python src/scripts/collect_metrics.py --n-test 200 --output results/metrics.csv
```

---

## train_direct_models.py

**Rôle** : entraîne les 8 modèles directs CI → trajectoire sur des trajectoires synthétiques
complètes (paradigme direct, opposé au paradigme step-by-step de `train_models.py`).

**Paradigme direct** :
- Entrée  : `(r₀, cos θ₀, sin θ₀, vr₀, vθ₀)` — 5 scalaires (conditions initiales encodées)
- Sortie  : trajectoire aplatie `(r₀, θ₀, vr₀, vθ₀, r₁, θ₁, …)` — 4 × `target_len` scalaires

**Différence avec le paradigme step-by-step** : le modèle prédit la trajectoire entière en
une seule inférence, sans itération récursive. Avantage : pas d'accumulation d'erreur.
Inconvénient : taille de sortie fixe, ne peut pas prédire au-delà de `target_len` pas.

### Algorithmes et contextes

| Contexte | Fraction des trajectoires | Modèles produits |
|----------|--------------------------|-----------------|
| `1pct`   | 1 %  | `direct_linear_1pct.pkl`, `direct_mlp_1pct.pkl` |
| `10pct`  | 10 % | `direct_linear_10pct.pkl`, `direct_mlp_10pct.pkl` |
| `50pct`  | 50 % | `direct_linear_50pct.pkl`, `direct_mlp_50pct.pkl` |
| `100pct` | 100 %| `direct_linear_100pct.pkl`, `direct_mlp_100pct.pkl` |

### Structure d'un fichier .pkl

```python
{
    "model":       Ridge | MLPRegressor,
    "scaler_X":    StandardScaler,   # fitté sur les CI d'entraînement
    "target_len":  int,              # longueur de la trajectoire prédite (pas)
    "context":     str,              # "1pct", "10pct", …
    "model_type":  str,              # "Ridge" ou "MLP"
    "n_train":     int,              # nombre de trajectoires d'entraînement
    "mae_r_train": float,            # MAE sur r (train, en mètres)
}
```

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--n-trajectories N` | 50 000 | Trajectoires totales pour 100pct |
| `--max-steps N` | 1 000 | Longueur max de la trajectoire cible (10 s à dt=0.01) |
| `--output-dir PATH` | `data/models/` | Dossier de sauvegarde |
| `--no-save` | off | Dry-run : entraîne mais ne sauvegarde pas |

```bash
python src/scripts/train_direct_models.py
python src/scripts/train_direct_models.py --n-trajectories 20000 --max-steps 500
```

**Prérequis** : aucun (les trajectoires sont générées à la volée).

---

## benchmark_direct.py

**Rôle** : benchmark comparatif direct vs step-by-step sur un jeu de test synthétique commun.

Évalue les 4 paradigmes × 4 contextes sur 500 trajectoires de test (seed=999, jamais
vues pendant l'entraînement) :

| Paradigme | Fichiers |
|-----------|---------|
| direct-Ridge | `direct_linear_{ctx}.pkl` |
| direct-MLP   | `direct_mlp_{ctx}.pkl` |
| step-Ridge   | `synth_linear_{ctx}.pkl` |
| step-MLP     | `synth_mlp_{ctx}.pkl` |

### Métriques

- **MAE r (m)** — erreur absolue moyenne sur le rayon polaire
- **Stabilité (%)** — fraction de trajectoires sans NaN ni divergence (r < 2R)

### Sorties

- `figures/benchmark_direct.png` — 2 panels : MAE r et stabilité vs contexte (échelle log)
- `results/benchmark_direct.csv` — table complète des métriques

### Arguments

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--n-test N` | 500 | Trajectoires de test |
| `--output PATH` | `figures/benchmark_direct.png` | Figure |
| `--csv PATH` | `results/benchmark_direct.csv` | CSV |
| `--no-plot` | off | Mode batch |

```bash
python src/scripts/benchmark_direct.py
python src/scripts/benchmark_direct.py --n-test 200 --no-plot
```

**Prérequis** :
- Modèles step-by-step : `data/models/synth_*.pkl` (lancer `train_models.py`)
- Modèles directs : `data/models/direct_*.pkl` (lancer `train_direct_models.py`)

---

## ablation_features.py

**Rôle** : justifie empiriquement le choix des 9 features ML en entraînant
`LinearStepModel` avec quatre sous-ensembles croissants de features en entrée.

Montre que retirer les produits croisés physiques (vθ²/r, vr·vθ/r, etc.)
dégrade significativement val_loss, MAE(r) et la stabilité des trajectoires.

**Prérequis** : chunks dans `data/synthetic/`.

| Sous-ensemble | Features | Note |
| --- | --- | --- |
| A — Base | r, cosθ, sinθ, vr, vθ | 5 features |
| B — + Centrifuge | + vθ²/r | terme dvr/dt |
| C — + Coriolis | + vr·vθ/r | terme dvθ/dt |
| D — Complet | + sinθ·vθ/r, cosθ·vθ/r | couplages angulaires |

**Arguments** : `--n-chunks N` (défaut 10), `--n-test N` (défaut 100), `--output PATH`, `--no-plot`.

```bash
python src/scripts/ablation_features.py
python src/scripts/ablation_features.py --n-chunks 20 --output figures/ablation.png
python src/scripts/ablation_features.py --no-plot --output results/ablation.csv
```
