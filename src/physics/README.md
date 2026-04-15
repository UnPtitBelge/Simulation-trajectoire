# Simulations physiques

Trois simulateurs indépendants. Cône et membrane partagent la même convention d'état polaire ; MCU est purement analytique.

---

## Système de coordonnées (cône et membrane)

État interne : **(r, θ, vr, vθ)**

| Variable | Définition |
|---|---|
| `r` | distance radiale au centre (m) |
| `θ` | angle polaire (rad) |
| `vr` | composante radiale = dr/dt (m/s) |
| `vθ` | composante tangentielle = **r · dθ/dt** (m/s) |

Le choix `vθ = r·dθ/dt` rend les deux composantes homogènes en m/s et simplifie l'expression de la force centrifuge (`vθ²/r`) et du terme de Coriolis (`−vr·vθ/r`).

---

## MCU — Mouvement Circulaire Uniforme (`mcu.py`)

Solution analytique exacte, sans intégration numérique :

```
x(t) = r · cos(θ₀ + ω·t)
y(t) = r · sin(θ₀ + ω·t)
```

Retourne un tableau `(n_steps, 2)` en Cartésien. Aucune condition d'arrêt, orbite parfaite.

---

## Cône (`cone.py`)

### Géométrie

Surface conique plane : `z(r) = slope · (r − R_centre)` avec `slope = depth / R`.

- `depth` : dénivelé entre le bord (`r = R`) et le centre (`r ≈ 0`)
- L'angle de la pente est **constant** : `α = arctan(slope)`
- `g_radial = −g · sin(α)` et `g_friction = μ · g · cos(α)` sont donc des constantes

### Équations du mouvement

Bille glissante (pas de roulement) → la masse se simplifie. Modèle de frottement de **Coulomb** (force proportionnelle à la normale, direction opposée à la vitesse) :

```
dvr/dt =  vθ²/r                           [centrifuge]
        − g·sin(α)                         [gravité radiale, vers le centre]
        − μ·g·cos(α) · vr / |v|           [Coulomb radial, opposé à v]

dvθ/dt = −vr·vθ / r                        [Coriolis — conserve L = r·vθ sans friction]
        − μ·g·cos(α) · vθ / |v|           [Coulomb tangentiel]
```

`|v| = √(vr² + vθ²)` est la norme totale de vitesse. Le frottement de Coulomb a une amplitude constante `μ·g·cos(α)` sur le cône.

**Équilibre orbital (`dvr/dt = 0`, `vr = 0`) :**

```
vθ_orb(r) = √(g · sin(α) · r)
```

La vitesse orbitale croît avec r. Avec friction, le moment cinétique `L = r·vθ` décroît → la bille spirale vers le centre.

### Cas vitesse nulle (frottement statique)

Quand `|v| = 0`, on teste la condition de glissement statique :

- `|g·sin(α)| > μ·g·cos(α)` → `tan(α) > μ` : la pente est trop raide, la bille repart vers le centre (`ar = g_radial + g_friction` pour compenser)
- `|g·sin(α)| ≤ μ·g·cos(α)` → `tan(α) ≤ μ` : frottement statique suffit, la bille reste immobile (`ar = at = 0`)

**Snap-to-zero** : si `|v| < μ·g·cos(α)·dt` après la mise à jour de vitesse ET que le frottement statique tient → on force `vr = vθ = 0` pour absorber les oscillations numériques.

---

## Membrane (`membrane.py`)

### Géométrie

Surface logarithmique : `z(r) = k · ln(r / R)` avec `k = F / (2πT)`.

- `F` : force exercée au centre (poids de la bille centrale)
- `T` : tension de la membrane (N/m)
- La pente locale `dz/dr = k/r` varie avec r : douce au bord, forte au centre

L'angle local `β(r) = arctan(k/r)`. Contrairement au cône, β n'est pas constant.

### Équations du mouvement

Même structure que le cône, mais `sin β` et `cos β` dépendent de r à chaque pas :

```
local_slope = k / r
inv_norm    = 1 / √(1 + (k/r)²)     [= cos β(r)]

dvr/dt =  vθ²/r
        − g · (k/r) · inv_norm        [gravité radiale = g·sin β(r)]
        − μ·g · inv_norm · vr/|v|    [Coulomb = μ·g·cos β(r)]

dvθ/dt = −vr·vθ / r
        − μ·g · inv_norm · vθ/|v|
```

**Propriété remarquable — vitesse orbitale constante :**

```
vθ_orb = √(g · k)     (indépendante de r)
```

La pente `k/r` croît exactement assez vite vers le centre pour que `g·sin β(r)` compense toujours la même force centrifuge `vθ²/r`, quel que soit r. Toutes les orbites circulaires ont la même vitesse tangentielle.

### Cas vitesse nulle

Identique au cône, avec `a_gravity = −g · (k/r) · inv_norm` à la place de `g·sin(α)`.

---

## Intégrateurs disponibles (`cone.py`)

`compute_cone` accepte un paramètre `method` pour choisir l'intégrateur :

| `method` | Ordre | Évaluations f/pas | Notes |
| --- | --- | --- | --- |
| `"euler"` | 1 | 1 | Euler explicite — position avec ancienne vitesse. Instable à grand dt |
| `"euler_cromer"` | 1 | 1 | Semi-implicite **(défaut)** — vitesse d'abord, position ensuite. Conservatif |
| `"rk4"` | 4 | 4 | Runge-Kutta 4 — 4× plus coûteux, erreur en O(dt⁴) |

### Euler-Cromer (semi-implicite, défaut)

Les positions sont calculées avec les vitesses **déjà mises à jour** :

```python
# 1. Mise à jour des vitesses (accélérations calculées à l'état courant)
vr     += dt * ar
vθ     += dt * at
# 2. Avancement des positions avec les nouvelles vitesses
r      += dt * vr
θ      += dt * vθ / r
```

Cet ordre rend le schéma **symplectique** : il conserve une forme d'énergie modifiée proche de l'énergie physique. L'Euler explicite pur dissiperait (ou accumulerait) de l'énergie artificiellement.

### RK4

Quatre évaluations de `f = (dr/dt, dθ/dt, dvr/dt, dvθ/dt)` via la fonction `_derivatives()` :

```text
k1 = f(r,             θ,             vr,             vθ)
k2 = f(r + ½dt·k1[0], θ + ½dt·k1[1], vr + ½dt·k1[2], vθ + ½dt·k1[3])
k3 = f(r + ½dt·k2[0], ...)
k4 = f(r +  dt·k3[0], ...)
r  += (dt/6) · (k1[0] + 2·k2[0] + 2·k3[0] + k4[0])
...
```

Utilisé comme trajectoire de référence dans `benchmark_integrators.py`.

### Snap-to-zero

Après chaque mise à jour de vitesse (tous intégrateurs) : si `|v| < g_friction·dt` et que le frottement statique tient (`|g_radial| ≤ g_friction`), on force `vr = vθ = 0` pour absorber les oscillations numériques autour de l'équilibre statique.

### Conditions d'arrêt

| Condition | Critère |
|---|---|
| Sortie du bord | `r ≥ R` |
| Collision centrale | `r ≤ center_radius` |
| Bille immobile | `|v| = 0` et frottement statique tient |
| Borne de sécurité | `n_steps` atteint |

---

## Niveaux de précision physique (cône et membrane)

Les deux simulateurs acceptent trois paramètres optionnels qui permettent d'affiner progressivement le modèle physique :

| Niveau | Paramètre | Valeur typique | Description |
| --- | --- | --- | --- |
| 0 (défaut) | — | `rolling=False` | Glissement pur — Coulomb cinétique μ constant |
| 1 | `rolling=True` | — | Roulement sans glissement — facteur de masse effective f = 5/7 (sphère pleine, I = 2/5·m·r²), Coulomb supprimé |
| 2 | `rolling_resistance` | 0.001–0.005 | + Résistance au roulement μ_r · m · g · cos β — force bien plus faible que Coulomb (rapport ×10 à ×50) |
| 3 | `drag_coeff` | 0.01–0.1 m⁻¹ | + Traînée aérodynamique quadratique k · ‖v‖ · v, avec k = ρ_air · C_d · A / (2m) |

Les niveaux 2 et 3 sont **cumulatifs** : `rolling=True, rolling_resistance=0.003, drag_coeff=0.05` active les 4 effets simultanément.

### Équations — roulement pur (Niveau 1)

Pour une sphère pleine (`I = 2/5·m·r²`), la contrainte de roulement sans glissement introduit un facteur effectif f = 5/7 dans les équations de Newton :

```text
dvr/dt = (vθ²/r − g·sin α) · f          [f = 5/7 pour sphère pleine]
dvθ/dt = (−vr·vθ / r) · f
```

Le terme de Coulomb disparaît. Sans résistance au roulement ni traînée, le système est **conservatif** (énergie mécanique + rotationnelle conservée) — la bille orbite indéfiniment.

### Équations — résistance au roulement (Niveau 2)

La résistance au roulement est une force dissipative proportionnelle à la normale, mais d'amplitude μ_r ≪ μ :

```text
f_rr = μ_r · m · g · cos β    (cône : cos β = cos α constant)
                               (membrane : cos β = 1/√(1+(k/r)²) variable)

dvr/dt += −f_rr/m · vr / |v|
dvθ/dt += −f_rr/m · vθ / |v|
```

### Équations — traînée aérodynamique (Niveau 3)

```text
F_drag = −k · |v| · v     (quadratique en vitesse)

dvr/dt += −k · |v| · vr
dvθ/dt += −k · |v| · vθ
```

### Snap-to-zero unifié

Le critère d'arrêt est adapté au mode :

- Glissement : `|v| < g_friction · dt` ET `|g_radial| ≤ g_friction`
- Roulement : `|v| < rolling_resistance_force · dt` ET `|g_radial| · f ≤ rolling_resistance_force`

Sans résistance au roulement (`rolling=True, rolling_resistance=0`), le snap-to-zero ne se déclenche jamais — la bille conserve sa vitesse indéfiniment.

---

## Comparaison cône / membrane

| | Cône | Membrane |
|---|---|---|
| Profil `z(r)` | linéaire `slope·r` | logarithmique `k·ln(r/R)` |
| Pente `dz/dr` | `slope` **constant** | `k/r` **variable**, → ∞ près du centre |
| Angle local β | constant, calculé une fois | recalculé à chaque pas |
| `g·sin β` | constant | croît vers le centre |
| `μ·g·cos β` | constant | décroît vers le centre |
| Vitesse orbitale | `√(g·sin(α)·r)` croît avec r | `√(g·k)` **constante** |
