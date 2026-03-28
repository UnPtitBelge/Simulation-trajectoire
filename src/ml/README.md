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

## 3. Entraînement — `train.py`

### Données synthétiques — `train_synth()`

Les chunks `.npz` contiennent les paires `(X, y)` pré-générées par `generate_data.py`. L'entraînement charge un chunk à la fois, appelle `partial_fit()`, puis libère la RAM.

**Trois contextes :** `10pct`, `50pct`, `100pct` — fraction des chunks utilisés. Permet de comparer l'effet de la quantité de données.

**Deux algos × trois contextes = 6 modèles** entraînés en parallèle via `ProcessPoolExecutor`.

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
