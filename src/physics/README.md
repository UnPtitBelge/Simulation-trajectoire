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

## Intégrateur commun — Euler semi-implicite

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

### Conditions d'arrêt

| Condition | Critère |
|---|---|
| Sortie du bord | `r ≥ R` |
| Collision centrale | `r ≤ center_radius` |
| Bille immobile | `|v| = 0` et frottement statique tient |
| Borne de sécurité | `n_steps` atteint |

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
