# Prédiction ML de trajectoires

Le pipeline ML apprend à imiter le simulateur physique (ou des données réelles caméra) en prédisant, pas de temps par pas de temps, l'évolution de l'état de la bille.

---

## Vue d'ensemble

```
Données (synthetic chunks .npz  ou  tracking_data.csv)
    │
    ▼ state_to_features()
Features X (état t)  →  modèle apprend  Δ = feat(t+1) − feat(t)
    │
    ▼ predict_step() × n_steps
Trajectoire (r, θ, vr, vθ) complète
```

---

## 1. Représentation des états — `models.py`

### État brut

L'état physique est un vecteur `(r, θ, vr, vθ)` en coordonnées polaires.

### Encodage en features — `state_to_features()`

L'état brut est transformé en **9 features** avant d'être donné au modèle :

| Index | Feature | Formule | Rôle |
|---|---|---|---|
| 0 | `r` | r | position radiale |
| 1 | `cos θ` | cos θ | composante angulaire (évite la discontinuité ±π) |
| 2 | `sin θ` | sin θ | composante angulaire |
| 3 | `vr` | vr | vitesse radiale |
| 4 | `vθ` | vθ | vitesse tangentielle |
| 5 | centrifuge | vθ²/r | terme centrifuge dans dvr/dt |
| 6 | Coriolis | vr·vθ/r | terme de Coriolis dans dvθ/dt |
| 7 | couplage cos | sin θ · vθ/r | couplage angulaire dans d(cos θ)/dt |
| 8 | couplage sin | cos θ · vθ/r | couplage angulaire dans d(sin θ)/dt |

**Pourquoi les features 5–8 ?**

Les équations du mouvement physique contiennent des **produits** de variables :
- `dvr/dt` contient `vθ²/r` — produit non linéaire de vθ et 1/r
- `dvθ/dt` contient `vr·vθ/r` — idem pour le Coriolis
- `d(cos θ)/dt = −sin θ · dθ/dt = −sin θ · vθ/r` — couplage angulaire

Une régression linéaire ne peut pas représenter ces produits à partir des features de base séparées. Elle tenterait de les approcher avec des combinaisons linéaires de `vr`, `vθ`, `sin θ`… ce qui crée une boucle de rétroaction oscillante en prédiction récursive. En ajoutant les produits comme features explicites, la LR peut apprendre exactement ces termes.

### Décodage — `features_to_state()`

Seules les 5 premières features sont utilisées pour reconstruire l'état :
- `r = features[0]`
- `θ = arctan2(features[2], features[1])` (= arctan2(sin θ, cos θ))
- `vr = features[3]`
- `vθ = features[4]`

Les features 5–8 sont ignorées : elles seront recomputées depuis l'état reconstruit au pas suivant.

### Apprentissage résiduel (delta learning)

Les deux modèles apprennent `Δ = feat(état_{t+1}) − feat(état_t)` plutôt que `feat(état_{t+1})` directement.

Avantages :
- Les deltas sont ≈100× plus petits que les états absolus (dt = 0.01 s)
- L'accumulation d'erreur sur de longues séquences est réduite
- Le scaler StandardScaler normalise les deltas autour de 0 → meilleur conditionnement

---

## 2. Modèles — `models.py`

### LinearStepModel — Ridge via équations normales

**Principe :**

```
W = (XᵀX + λI)⁻¹ · Xᵀy
```

Les statistiques suffisantes `XᵀX` (matrice 10×10) et `Xᵀy` (matrice 10×9) sont accumulées chunk par chunk. Le système est résolu une seule fois à la première prédiction (`_finalize()`).

**Biais :** une colonne de 1 est ajoutée aux features scalées (`Xb = [X_scaled | 1]`), absorbant un terme constant dans W sans régularisation.

**Régularisation :** Ridge (`α·I`) sur les 9 features seulement (pas sur le biais) — évite la sur-simplification sans pénaliser le biais.

**Entraînement incrémental :**

```python
XᵀX += Xb.T @ Xb   # accumulé pour chaque chunk
Xᵀy += Xb.T @ ys
```

Avantage sur SGD : solution **exacte et reproductible**, pas de taux d'apprentissage à régler, pas d'oscillations en prédiction récursive.

### MLPStepModel — Réseau de neurones (warm_start)

Architecture : `(64, 32)` neurones cachés, activation ReLU, régularisation L2 (α = 0.001).

`warm_start=True` conserve les poids entre les appels à `fit()` : chaque chunk reprend là où le précédent s'est arrêté (entraînement incrémental).

`learning_rate="adaptive"` réduit le taux d'apprentissage quand le score stagne. `n_iter_no_change=10` arrête l'entraînement d'un chunk si la loss ne diminue plus.

---

## 3. Modèles directs — `direct_models.py` + `train_direct.py`

### Paradigme direct

```
ci_to_features(état_0)
  → (r₀, cos θ₀, sin θ₀, vr₀, vθ₀)   — 5 scalaires
      │
      ▼ DirectLinearModel.predict()  ou  DirectMLPModel.predict()
  → trajectoire aplatie (r₀, θ₀, vr₀, vθ₀, r₁, θ₁, …)  — 4 × target_len scalaires
      │
      ▼ reshape (target_len, 4)
  → trajectoire (r, θ, vr, vθ) de longueur fixe target_len
```

**Avantage** : pas d'accumulation d'erreur récursive — l'erreur de prédiction est bornée même sur de longues séquences.

**Limitation** : taille de sortie fixe (`target_len` pas). Avec peu de données, Ridge surpasse MLP car le problème est sous-déterminé (haute dimension de sortie, peu d'exemples d'entraînement).

### `ci_to_features(state)` — encodage des CI

Encode l'état initial `(r, θ, vr, vθ)` en `(r, cos θ, sin θ, vr, vθ)` (5 features).
Même raison que pour `state_to_features` : évite la discontinuité de θ à ±π.

### `DirectModelBase` — interface commune

| Méthode | Description |
|---------|-------------|
| `fit(X_ci, Y_traj)` | Entraîne le modèle. Fitte le scaler sur X_ci, calcule mae_r_train. |
| `predict(ic)` | Prédit la trajectoire depuis un état (r, θ, vr, vθ). Retourne `(target_len, 4)`. |
| `save(path)` | Sérialise en pickle (même interface que StepModelBase). |
| `DirectModelBase.load(path)` | Charge un modèle depuis un fichier pickle. |

Attributs publics après `fit()` : `target_len`, `n_train`, `mae_r_train`, `scaler_X`, `context`.

### `DirectLinearModel` — Ridge direct

Résout `W = (XᵀX + λI)⁻¹ Xᵀy` en une passe sur l'ensemble des données (pas incrémental). Solution exacte, pas de taux d'apprentissage à régler.

### `DirectMLPModel` — MLP direct

Architecture `(64, 32)`, early stopping activé si ≥ 10 exemples d'entraînement. La haute dimension de sortie (4 × `target_len` ≈ 4 000 scalaires) rend l'apprentissage difficile avec peu de données — à comparer à Ridge via `benchmark_direct.py`.

### Entraînement — `train_direct.py`

`train_direct_synth(phys_cfg, gen_cfg, contexts, n_total, max_steps, models_dir)` :
1. Génère `n_total` trajectoires complètes (seed=0, indépendant du jeu de test seed=999).
2. Calcule `target_len = min(médiane des longueurs, max_steps)` — partagé pour tous les contextes.
3. Pour chaque contexte : `DirectLinearModel.fit()` + `DirectMLPModel.fit()`, sauvegarde les `.pkl`.

**Scaler par contexte** (contrairement au scaler partagé du step-by-step) : ici `X_ctx` est entier en mémoire → statistiques représentatives par construction. Le step-by-step nécessite un scaler partagé car chaque chunk est trop petit pour estimer la distribution globale.

Fichiers produits : `direct_linear_{ctx}.pkl`, `direct_mlp_{ctx}.pkl`.

---

## 4. Entraînement step-by-step — `train.py`

### Données synthétiques — `train_synth()`

Les chunks `.npz` contiennent les paires `(X, y)` pré-générées par `generate_data.py`. L'entraînement charge un chunk à la fois, appelle `partial_fit()`, puis libère la RAM.

**Quatre contextes :** `1pct`, `10pct`, `50pct`, `100pct` — fraction des chunks utilisés. Permet de comparer l'effet de la quantité de données.

**Deux algos × quatre contextes = 8 modèles** entraînés en parallèle via `ProcessPoolExecutor`.

### Données réelles — `train_real()`

**Centrage par expérience — `compute_exp_centers()` :**

Pour compenser les décalages caméra inter-expériences, chaque expérience est centrée sur son propre point d'arrêt (médiane des 15 dernières positions). Les outliers (point d'arrêt anormalement éloigné du centre médian global) sont remplacés par la médiane globale.

**Conversion en (r, θ, vr, vθ) :**

```python
xc = x_px − cx_exp       # pixels centrés
yc = y_px − cy_exp
r      = √(xc² + yc²)   # pixels
θ      = arctan2(yc, xc)
vr     = (xc·vx + yc·vy) / r    # projection radiale de speedX/Y
vθ     = (xc·vy − yc·vx) / r    # projection tangentielle
```

`speedX/Y` est en unités `PositionsAnalytics` = `dx_px × (realWidth/videoWidth) × fps`.

**N passes :** les données réelles (limitées) sont parcourues plusieurs fois (`n_passes = 3` par défaut) pour consolider l'apprentissage.

---

## 4. Prédiction — `predict.py`

### Algorithme

```python
for i in range(n_steps):
    traj[i] = state                         # enregistre l'état courant
    if r ≥ r_max: return traj[:i+1]         # bille sortie
    if r ≤ r_min: return traj[:i+1]         # collision centrale
    if |v| < v_stop: return traj[:i+1]      # bille arrêtée
    state = model.predict_step(state)       # prédit l'état suivant
```

### `predict_step()` détaillé (LinearStepModel)

```
feat        = state_to_features(state)         # (r, cosθ, sinθ, vr, vθ, produits)
feat_scaled = scaler_X.transform(feat)         # normalisation
Xb          = [feat_scaled | 1]                # ajout du biais
delta_scaled = Xb @ W                          # prédiction du résidu normalisé
delta       = scaler_y.inverse_transform(...)  # dénormalisation
new_feat    = feat + delta                     # état t+1 en espace features
new_state   = features_to_state(new_feat)      # retour en (r, θ, vr, vθ)
```

### `predict_with_errors()` — comparaison avec une référence physique

Variante de `predict_trajectory` pour les scripts d'analyse scientifique :

```python
traj, errors = predict_with_errors(model, init_state, reference_traj, **kwargs)
# errors : (min(len(traj), len(ref)), 4) = |pred − ref| sur (r, θ, vr, vθ)
```

- `reference_traj` : trajectoire physique (N, 4) calculée depuis le même état initial
- `errors[:, 0]` : erreur absolue sur r — métrique principale pour les plots
- Utilisé par `analyze_ml_error.py` pour quantifier l'accumulation d'erreur
  en fonction de l'horizon de prédiction

### Paramètre `v_stop`

- **Mode synthétique :** en m/s (cohérent avec les vitesses synthétiques)
- **Mode réel :** doit être converti en unités PositionsAnalytics : `v_stop_real = v_stop_m/s × ppm × (realWidth/videoWidth)`

### `_clip_state()`

Si r < 0 (non physique, peut survenir si le modèle diverge légèrement) : `r` est clippé à 0 et `vr` est clippé à max(vr, 0) pour éviter une divergence continue.

---

## 5. Unités en mode réel vs synthétique

| | Synthétique | Réel |
|---|---|---|
| `r` | mètres | pixels centrés |
| `vr, vθ` | m/s | `dx_px × (realWidth/videoWidth) × fps` |
| `r_max` | R (m) | R × ppm (px) |
| `r_min` | center_radius (m) | center_radius × ppm (px) |
| `v_stop` | 0.002 m/s | `0.002 × ppm × realWidth/videoWidth` ≈ 0.48 units |
| Scaler | fittés sur états en m | fittés sur états en px |

Les scalers StandardScaler étant fittés sur les données d'entraînement dans leurs unités natives, la prédiction doit recevoir une entrée dans les **mêmes unités** que les données d'entraînement. Une erreur d'unité produit des prédictions absurdes même si le modèle est bon.
