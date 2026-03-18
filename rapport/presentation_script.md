# Script de présentation — Comment les ordinateurs simulent-ils la réalité ?

---

## Thème général

**Question centrale : Comment les ordinateurs simulent-ils la réalité ?**

L'objectif est de montrer, à travers une expérience concrète et plusieurs simulations,
ce qu'est un modèle, la réflexion qui se cache derrière sa construction, et la différence
fondamentale entre modéliser avec des équations et laisser la machine apprendre le modèle
elle-même par apprentissage automatique.

---

## Structure narrative

L'enchaînement des onglets suit un fil conducteur volontaire :

```
Expérience réelle → Vidéo → 2D MCU → 3D Cône → 3D Membrane → Machine Learning
```

> **"Voici le phénomène réel. Regardons maintenant comment on essaie de le décrire."**

---

## 0. L'expérience réelle

Avant toute simulation, le public est invité à manipuler le dispositif physique :
une bille lancée sur une surface courbée (cône ou membrane en caoutchouc).

**Ce que le public doit observer :**
- La bille ne tombe pas en ligne droite vers le centre — elle orbite.
- L'orbite n'est pas un cercle parfait — elle se décale à chaque tour (précession).
- Avec le temps, la bille spirale lentement vers le centre sous l'effet du frottement.

**Ce qu'on veut susciter :** une question naturelle.
*Pourquoi la bille fait-elle ça ? Peut-on le prédire ? Peut-on le reproduire par ordinateur ?*

---

## 1. La vidéo — ancrer dans la réalité

**Rôle dans la présentation :**
Montrer l'expérience filmée pour que le public garde une référence visuelle concrète
tout au long de la présentation. Chaque simulation sera inconsciemment comparée à cette image.

**Message clé :**
> "C'est ça qu'on essaie de simuler. Gardez cette image en tête."

---

## 2. Le MCU 2D — qu'est-ce qu'un modèle ?

**Ce qu'on montre :**
Un mouvement circulaire uniforme. La position est donnée par une formule exacte :

```
x(t) = R · cos(ω·t)
y(t) = R · sin(ω·t)
```

Il n'y a pas d'approximation, pas d'intégration numérique, pas d'erreur.
L'équation *est* la réalité — du moins pour ce cas particulier.

**Message clé :**
> "Un modèle, c'est un ensemble de décisions sur ce qu'on garde et ce qu'on ignore.
> Ici on a choisi un cas si simple qu'on peut tout décrire exactement.
> La plupart des phénomènes réels ne sont pas aussi simples."

**Ce que ce modèle illustre :**
- La définition d'un modèle : remplacer un phénomène physique par un objet mathématique
  qu'on peut interroger, prédire, modifier.
- Ses limites immédiates : dès qu'on ajoute du frottement, une surface en 3D,
  ou des conditions initiales complexes, cette formule ne suffit plus.

---

## 3. Le cône 3D — modéliser avec Newton

**Ce qu'on montre :**
Une bille glissant sur un cône de pente constante, sous l'effet de la gravité et
d'un frottement de Coulomb. Intégration numérique par Euler semi-implicite.

**La physique :**

La surface est décrite par :
```
z(r) = -pente · (R - r)
```
La pente est constante → la composante gravitationnelle le long de la surface
est **la même partout** :
```
a_gravité = g · sin(α)   (constant)
```

**Les choix de modélisation (simplifications explicites) :**
- On ignore la résistance de l'air.
- On ignore la rotation propre de la bille (pas de moment d'inertie).
- On traite la bille comme un point matériel.
- On suppose la pente parfaitement constante.

Chaque simplification est un choix justifié. On les mentionne parce que
**un bon modèle, c'est un modèle dont on connaît les hypothèses.**

**Un seul paramètre à mesurer :** la pente du cône — mesurable avec un rapporteur.

**Ce que ce modèle produit :**
Des orbites en rosette qui précèdent (l'ellipse tourne sur elle-même à chaque révolution).
Ce n'est pas une ellipse fermée — les lois de Kepler ne s'appliquent pas ici.

**Message clé :**
> "Ce modèle est simple, ses paramètres sont mesurables directement,
> et il correspond bien à ce qu'on observe. C'est un bon modèle."

---

## 4. La membrane 3D — plus d'équations, pas forcément meilleur

**Ce qu'on montre :**
La même bille, lancée dans les mêmes conditions initiales, mais sur une surface
décrite par l'équation de Laplace pour une membrane élastique sous charge centrale.

**La physique :**

La surface est la solution exacte de l'équation de Laplace pour une membrane
circulaire en tension T [N/m], soumise à une charge ponctuelle F [N] au centre,
fixée au bord :
```
z(r) = -(F / 2πT) · ln(R / r)
```

La pente varie en **1/r** → la force augmente à mesure qu'on se rapproche du centre :
```
dz/dr = F / (2πT · r)
```

**Ce que ce modèle fait mieux :**
- La projection de la gravité sur le plan tangent exact (pas d'approximation petits angles).
- La correction de la force normale pour le frottement (inclinaison prise en compte).
- L'intégration numérique est d'ordre 2 (Verlet vitesse) — plus précise que le cône.

**Ce que ce modèle fait moins bien :**
- La membrane en caoutchouc réelle a une forme proche d'un cône (pente quasi-constante),
  pas d'un profil logarithmique.
- Près du bord, la pente logarithmique est quasi nulle → la force est trop faible.
- Près du centre, la pente diverge en 1/r → la force est trop forte.
- Les paramètres T et F sont difficiles à mesurer avec précision sur une membrane réelle.

**Comparaison des orbites (mêmes conditions initiales) :**

| Propriété | Cône | Membrane |
|---|---|---|
| Loi de force | Constante | Croît en 1/r |
| Précession par orbite | ≈ 151° | ≈ 105° |
| Spiral final vers le centre | Uniforme | Brutal (divergence 1/r) |
| Correspondance avec la réalité | Meilleure | Moins bonne |
| Complexité mathématique | Faible | Élevée |

**Message clé — le paradoxe central de la présentation :**
> "L'équation de Laplace est une vraie loi physique. Elle est mathématiquement rigoureuse.
> Mais elle décrit une membrane idéale — tension uniforme, déformation linéaire, charge ponctuelle.
> La membrane en caoutchouc devant vous n'est rien de tout ça.
> Le cône, qui ne prétend à aucune rigueur théorique, correspond mieux à la réalité
> parce que sa simplification (pente constante) colle mieux à l'objet physique réel.
>
> Un modèle n'est pas jugé au nombre d'équations qu'il contient.
> Il est jugé par la pertinence de ses hypothèses par rapport à l'objet qu'il décrit."

---

## 5. Le Machine Learning — et si on supprimait les équations ?

**Ce qu'on montre :**
Un modèle entraîné sur des trajectoires réelles (ou simulées). La machine a vu
beaucoup d'exemples. Elle a appris à prédire la position suivante à partir des positions
précédentes. Elle n'a jamais vu une équation. Elle ne sait pas ce qu'est la gravité.

**Ce que le modèle ML fait :**
- Il reconnaît des patterns dans les données.
- Il prédit la trajectoire dans des conditions proches de celles qu'il a apprises.
- Il produit un résultat visuellement plausible.

**Ce que le modèle ML ne fait pas :**
- Il ne comprend pas pourquoi la bille se déplace ainsi.
- Il ne peut pas s'adapter à une nouvelle surface qu'il n'a pas vue.
- Il ne peut pas vous dire quelle force agit, ni à quelle vitesse la bille arrive.
- Hors de sa distribution d'entraînement, il échoue — souvent sans le signaler.

**La différence fondamentale avec les modèles à équations :**

| Propriété | Modèle à équations | Machine Learning |
|---|---|---|
| Encode | De la compréhension | Des patterns |
| Extrapolation | Oui (physiquement cohérent) | Non (interpolation seulement) |
| Explicabilité | Totale (on peut lire les équations) | Nulle (boîte noire) |
| Données nécessaires | Peu (paramètres mesurables) | Beaucoup |
| Fonctionne hors entraînement | Oui | Non |
| Connaissance préalable requise | Oui (physique) | Non |

**Message clé :**
> "Le machine learning ne modélise pas la réalité — il mémorise des exemples de la réalité.
> C'est puissant quand on ne comprend pas le phénomène, ou quand les équations sont trop complexes.
> Mais dès qu'on sort des conditions connues, le modèle ne tient plus.
> Un modèle physique, lui, peut prédire ce qu'on n'a jamais observé,
> parce qu'il encode une compréhension du phénomène, pas juste ses traces."

---

## Le message de synthèse

**Qu'est-ce qu'un modèle ?**

Un modèle est un ensemble de décisions sur ce qu'on garde et ce qu'on ignore.
Tout modèle est faux. La question n'est pas *"est-il exact ?"* mais
*"est-il faux d'une manière qui compte pour ce qu'on veut faire ?"*

**Les trois leçons de cette présentation :**

1. **La complexité ne garantit pas la précision.**
   La membrane (Laplace) est plus rigoureuse que le cône (Newton).
   Elle décrit pourtant moins bien la réalité de l'expérience.

2. **Modéliser, c'est choisir.**
   Chaque simplification est un choix. Un bon modèle est un modèle dont on connaît
   et assume les hypothèses — pas un modèle qui prétend tout capturer.

3. **Comprendre et apprendre sont deux choses différentes.**
   Le machine learning apprend des exemples. Les modèles physiques encodent
   une compréhension. Les deux ont leur place — selon ce qu'on sait, ce qu'on a,
   et ce qu'on cherche à faire.

---

## Notes techniques pour le mode présentation

Lancer avec :
```bash
python src/gui_Qt/main.py --presentation
```

- La barre d'onglets est cachée.
- Les touches **1 à 5** changent d'onglet et lancent automatiquement la simulation.
- **Échap** ferme l'application.

Ordre des touches en mode présentation :

| Touche | Onglet |
|---|---|
| 1 | 2D MCU |
| 2 | 3D Cône |
| 3 | 3D Membrane |
| 4 | Machine Learning |
| 5 | Vidéo |

> **Suggestion :** commencer sur la vidéo (touche 5) pour ancrer le public
> dans la réalité physique, puis passer au MCU (touche 1) pour débuter la démonstration.

---

## Conditions initiales scriptées conseillées

Pour que la comparaison cône / membrane soit parlante, utiliser les **mêmes conditions initiales** sur les deux :

```
x0 = 0.55 m,  y0 = 0.0 m
v_i = 0.55 m/s,  theta = 88°
friction_coef = 0.012
```

Cela produit 4 à 5 boucles de précession clairement visibles avant que la bille
n'atteigne le centre — suffisant pour que le public voie la différence entre les deux orbites.
