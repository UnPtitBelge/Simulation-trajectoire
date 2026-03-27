# Physique des simulations

Ce dossier contient les backends de simulation numérique. Chaque module calcule une trajectoire complète en coordonnées polaires (r, θ, vr, vθ) avant que l'affichage commence.

---

## Coordonnées et conventions

Toutes les simulations (sauf MCU) utilisent des **coordonnées polaires sur la surface** :

| Variable | Signification |
|---|---|
| r | distance radiale au centre (m) |
| θ | angle azimutal (rad) |
| vr = dr/dt | vitesse radiale (m/s) |
| vθ = r·dθ/dt | vitesse tangentielle (m/s) |

Le choix vθ = r·dθ/dt (plutôt que dθ/dt seule) rend les deux composantes homogènes (m/s)
et simplifie l'expression du moment cinétique L = r·vθ.

---

## 1. MCU — Mouvement Circulaire Uniforme (`mcu.py`)

### Équations

Solution analytique exacte, sans intégration numérique :

```
x(t) = r · cos(θ₀ + ω·t)
y(t) = r · sin(θ₀ + ω·t)
```

### Paramètres

| Paramètre | Symbole | Unité |
|---|---|---|
| Rayon d'orbite | r | m |
| Angle initial | θ₀ | rad |
| Vitesse angulaire | ω | rad/s |

### Pertinence

Le MCU est le cas limite d'une bille sur le cône **sans frottement** démarrée exactement à
la vitesse orbitale v_orb. Il sert de référence idéale pour comprendre les simulations
plus complexes.

---

## 2. Cône (`cone.py`)

### Surface

```
z(r) = -s·(R - r)     avec s = depth/R  (pente constante)
```

Le bord (r = R) est à z = 0 et le centre (r = 0) à z = -depth.

### Dérivation — Lagrangien

L'élément de longueur sur la surface conique est :

```
ds² = (1 + s²)·dr² + r²·dθ²
```

car dz = s·dr. Le Lagrangien par unité de masse est donc :

```
L = ½·[(1+s²)·ṙ² + r²·θ̇²] + g·s·(R-r)
  = énergie cinétique sur surface - énergie potentielle
```

Les équations d'Euler-Lagrange donnent :

```
d/dt[(1+s²)·ṙ]  -  r·θ̇²  +  g·s  =  0   (coordonnée r)
d/dt[r²·θ̇]                         =  0   (coordonnée θ → conservation de L)
```

### Équations du mouvement (avec frottement)

En passant aux variables (vr, vθ) et en ajoutant un frottement linéaire -μ·v :

```
dvr/dt = (vθ²/r  -  g·s) / (1 + s²)  -  μ·vr

dvθ/dt = -(vr·vθ) / r  -  μ·vθ
```

**Interprétation terme par terme :**

| Terme | Rôle physique |
|---|---|
| `vθ²/r` | Force centrifuge effective (pousse vers l'extérieur) |
| `-g·s` | Composante radiale de la gravité sur la pente (pousse vers l'intérieur) |
| `1/(1+s²)` | Facteur métrique — la pente augmente la masse effective en direction radiale |
| `-vr·vθ/r` | Terme de Coriolis — conserve L = r·vθ sans frottement |
| `-μ·vr`, `-μ·vθ` | Frottement de glissement (modèle visqueux linéaire, μ en 1/s) |

### Vitesse orbitale

L'orbite circulaire impose l'équilibre centrifuge–gravité (dvr/dt = 0, vr = 0) :

```
vθ²/r = g·s   →   v_orb(r) = sqrt(g·s·r)
```

La vitesse orbitale **croît avec r** : les orbites extérieures sont plus rapides.
Démarrer à vθ = v_orb donne une orbite circulaire ; le frottement réduit vθ
progressivement, brisant l'équilibre et provoquant une spirale vers le centre.

### Moment cinétique

```
dL/dt = d(r·vθ)/dt = -μ·L   →   L(t) = L₀·exp(-μ·t)
```

Le rayon orbital décroît selon r_orb(t) = (L(t) / sqrt(g·s))^(2/3).

---

## 3. Membrane (`membrane.py`)

### Surface

```
z(r) = k·ln(r/R)     (k = F/(2πT), paramètre de courbure)
```

Le bord (r = R) est à z = 0. La surface plonge vers -∞ au centre (singularité
logarithmique). La simulation s'arrête à r = r_ball.

### Dérivation — Lagrangien

La pente locale varie : dz/dr = k/r. L'élément de longueur est :

```
ds² = [1 + (k/r)²]·dr² + r²·dθ²
```

Le Lagrangien est le même que pour le cône mais avec une métrique dépendant de r.
La dérivée temporelle d/dt[1+(k/r)²] produit un terme supplémentaire
(terme de connexion géodésique) absent sur le cône.

### Équations du mouvement

```
dvr/dt = (vθ²/r  -  g·k/r  +  k²·vr²/r³) / (1 + (k/r)²)  -  μ·vr

dvθ/dt = -(vr·vθ) / r  -  μ·vθ
```

**Différences par rapport au cône :**

| Terme | Origine | Absent dans le cône ? |
|---|---|---|
| `-g·k/r` | Gravité sur pente variable k/r | Non (analogue à -g·s) |
| `+k²·vr²/r³` | Dérivée temporelle de la métrique (k/r)² | **Oui** — pente constante sur le cône |
| `1+(k/r)²` | Facteur métrique variable avec r | Non (valeur fixe 1+s² sur le cône) |

### Vitesse orbitale — propriété remarquable

L'équilibre dvr/dt = 0, vr = 0 donne :

```
vθ²/r = g·k/r   →   v_orb = sqrt(g·k)   (indépendante de r !)
```

La vitesse orbitale est **la même à tous les rayons**. C'est une propriété unique
du puits gravitationnel logarithmique : la pente k/r augmente vers le centre
exactement assez vite pour que la gravité compense toujours la même force centrifuge,
quel que soit le rayon.

Conséquence directe : une bille démarrée à vθ = v_orb depuis n'importe quel r₀
ne dépasse jamais r₀ — la trajectoire spirale vers l'intérieur sans jamais s'éloigner
du point de départ.

### Moment cinétique

```
L(t) = L₀·exp(-μ·t)   →   r_orb(t) = (r₀·v₀ / v_orb)·exp(-μ·t)
```

Le rayon orbital décroît **linéairement avec L** (et non en puissance 2/3 comme sur le cône).

---

## 4. Intégrateur numérique

### Semi-implicite Euler (symplectique)

Les deux simulations utilisent un intégrateur **semi-implicite Euler** :

```python
vr     += dt * ar(r, vr, vθ)     # vitesses mises à jour en premier
vθ     += dt * aθ(r, vr, vθ)
r      += dt * vr                 # positions calculées avec les nouvelles vitesses
θ      += dt * vθ / r
```

L'ordre d'application (vitesses avant positions) est essentiel : il rend le schéma
**symplectique**, c'est-à-dire qu'il conserve exactement une énergie modifiée proche
de l'énergie physique. Contrairement à l'Euler explicite, il ne dissipe pas l'énergie
numériquement et ne diverge pas pour des systèmes oscillatoires.

### Choix des pas de temps

| Simulation | dt (s) | Justification |
|---|---|---|
| Cône | 0.01 | Pente constante, dynamique modérée |
| Membrane | 0.005 | Pente k/r → ∞ près du centre ; pas plus petit requis pour la stabilité |

### Conditions d'arrêt

| Condition | Critère |
|---|---|
| Collision | r ≤ r_ball (bille centrale) |
| Sortie | r ≥ R (bord de la surface) |
| Complet | n_steps atteint |

---

## Comparaison cône / membrane

| Propriété | Cône | Membrane |
|---|---|---|
| Surface z(r) | -s·(R-r)  linéaire | k·ln(r/R)  logarithmique |
| Pente dz/dr | s  (constante) | k/r  (croît vers le centre) |
| Métrique (ds/dr)² | 1+s²  (constante) | 1+(k/r)²  (variable) |
| v_orb(r) | sqrt(g·s·r)  (croît avec r) | sqrt(g·k)  (**constante**) |
| Terme de connexion | absent | +k²·vr²/r³ |
| r_orb(t) avec frottement | r₀·exp(-2μt/3) | r₀·exp(-μt) |
| Spirale avec μ > 0 | ~21 tours avant collision | ~27 tours, r_max = r₀ |
