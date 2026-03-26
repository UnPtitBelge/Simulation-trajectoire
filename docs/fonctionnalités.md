# Fonctionnalités de l'application

## Vue d'ensemble

Application de simulation physique + ML éducative, lancée en trois modes :

```bash
python main.py              # Mode normal (défaut)
python main.py presentation # Mode présentation (plein écran, auto-démarrage)
python main.py libre        # Mode libre (plein écran, menu d'entrée)
```

---

## Simulations disponibles

| # | Simulation | Description |
|---|-----------|-------------|
| 1 | **MCU** — Mouvement Circulaire Uniforme | Orbite 2D avec amortissement optionnel |
| 2 | **Cône** | Bille sur cône 3D avec gravité et frottement |
| 3 | **Membrane** | Membrane de Laplace 3D avec profil logarithmique |
| 4 | **ML** — Machine Learning | Régression linéaire sur trajectoire parabolique |
| 5 | **Chaos** | Effet papillon : N billes aux conditions initiales légèrement différentes |

> **Note :** La simulation Chaos (5) n'est pas disponible en mode présentation.

---

## Mode normal

**Fenêtre :** 1280×800, redimensionnable
**Page initiale :** Vue simulation (MCU actif)

### Simulations
- Les 5 simulations sont accessibles via les touches `1`–`5`
- Navigation cyclique avec `←` / `→`
- Passage au menu principal avec `Échap`

### Interface
- Affichage plein cadre de la simulation active
- Panneau de paramètres masqué par défaut (`Ctrl+P` pour afficher)
- Pas de tableau de bord ni de scénarios guidés

### Raccourcis clavier

| Touche | Action |
|--------|--------|
| `1`–`5` | Changer de simulation |
| `←` / `→` | Simulation précédente / suivante |
| `Espace` | Lecture / Pause |
| `R` | Réinitialiser |
| `F1` / `F2` / `F3` | Appliquer le preset 1 / 2 / 3 |
| `Ctrl+P` | Afficher/masquer le panneau de paramètres |
| `Échap` | Retour au menu principal |
| `Ctrl+Alt+Échap` | Forcer la fermeture |

---

## Mode présentation

**Fenêtre :** Plein écran
**Page initiale :** MCU lancé automatiquement

Conçu pour une utilisation en amphithéâtre ou en classe, sans distraction.

### Simulations
- **4 simulations uniquement** : MCU, Cône, Membrane, ML (pas le Chaos)
- Navigation par touches `1`–`4` ou flèches `←` / `→` (démarrage automatique)
- Indicateur de progression affiché dans l'en-tête (`1/4`, `2/4`, …)

### Interface
- **En-tête :** titre de la simulation + sous-titre + badge de progression + message d'état
- **Aide contextuelle :** `1-4 · ←→ · Espace · R · F1–F3 · Échap`
- Aucun menu, tableau de bord ou scénario accessible
- Panneau de paramètres masqué par défaut (`Ctrl+P` pour un accès discret)

### Presets de présentation (F1–F3)

Chaque simulation dispose de presets spécifiquement optimisés pour la démonstration visuelle en classe :

| Simulation | F1 | F2 | F3 |
|-----------|----|----|-----|
| **MCU** | Orbite parfaite (R=8, ω=1,5, drag=0) | Spirale amortie | Rotation rapide |
| **Cône** | Conditions standard | v₀ = 0,63 m/s | v₀ = 0,63 + φ₀ = 135° |
| **Membrane** | Orbite gravitationnelle | Spirale vers le centre | Puits profond |
| **ML** | Données idéales | Données bruitées | Peu d'observations |

### Raccourcis clavier

| Touche | Action |
|--------|--------|
| `1`–`4` | Aller directement à la simulation (MCU/Cône/Membrane/ML) |
| `←` / `→` | Simulation précédente / suivante dans le cycle |
| `Espace` | Lecture / Pause |
| `R` | Réinitialiser |
| `F1` / `F2` / `F3` | Appliquer le preset de présentation 1 / 2 / 3 |
| `Ctrl+P` | Afficher/masquer le panneau de paramètres |
| `Échap` | Quitter l'application |

---

## Mode libre

**Fenêtre :** Plein écran
**Page initiale :** Menu principal

Conçu pour l'exploration autonome des étudiants, avec accès aux scénarios guidés et à la théorie.

### Menu principal

- **Grille de simulations** (4 cartes) : MCU, Cône, Membrane, ML
  - Chaque carte affiche le titre et une courte description
  - Bouton "Ouvrir" → ouvre le tableau de bord de la simulation
- **Bouton "Cas Extrêmes"** → vue dédiée aux cas limites et paramètres extrêmes
- **Bouton "Théorie de la modélisation"** → accès à la page de théorie
- **Bouton "Comparer deux simulations"** → vue côte-à-côte de toutes les simulations
- **Parcours guidés** : trois scénarios pédagogiques pas-à-pas

| Scénario | Niveau | Description |
|----------|--------|-------------|
| **Cône vs Membrane** | Intermédiaire | Paradoxe : le modèle simple (cône) surpasse le complexe (Laplace) |
| **Effet du frottement** | Débutant | Comparer frottement ON/OFF — spirale vs orbite perpétuelle |
| **Limites du ML** | Intermédiaire | Explorer les limites d'interpolation et d'extrapolation du modèle ML |

Chaque scénario inclut : instructions pas-à-pas, application automatique de presets, textes d'observation et questions de réflexion.

### Tableau de bord (ouvert depuis le menu)

**Panneau gauche :**
- Titre et description de la simulation
- Équations associées
- Sliders pour tous les paramètres ajustables (débounce 300ms)
- Boutons de presets (F1 / F2 / F3)
- Bouton de retour au menu

**Panneau droit (4 zones) :**
1. Visualisation live (rendu 2D ou 3D OpenGL)
2. Panneau de métriques en direct (`MetricsPanel`) — valeurs numériques actualisées à chaque frame
3. Graphe r(t) (`_LiveChartsPanel`) — courbe de la distance radiale au cours du temps (simulations 3D)
4. Boutons Lecture / Pause / Réinitialiser + contrôle de vitesse

### Vue Cas Extrêmes (accessible depuis le menu)

- **Panneau gauche :** sélecteur de simulation (MCU, Cône, Membrane, Chaos) + liste des cas extrêmes paramétrés
- **Panneau droit :** simulation en direct — démarre automatiquement dès la sélection d'un cas
- Chaque cas extrême inclut : nom, description pédagogique, paramètres appliqués automatiquement
- Conçu pour illustrer les comportements limites (orbites instables, spirales catastrophiques, effet papillon…)

### Page de théorie

- Contenu pédagogique complet sur la modélisation physique
- Explications à trois niveaux : Débutant / Intermédiaire / Avancé
- Disponible pour chaque simulation
- Bouton de retour au menu

### Vue de comparaison

- Affichage simultané de toutes les simulations
- Contrôles synchronisés
- Retour au menu via bouton dédié

### Raccourcis clavier (depuis le tableau de bord)

| Touche | Action |
|--------|--------|
| `Espace` | Lecture / Pause |
| `R` | Réinitialiser |
| `F1` / `F2` / `F3` | Appliquer le preset 1 / 2 / 3 |
| `Ctrl+P` | Afficher/masquer le panneau de paramètres overlay |
| `Échap` | Retour au menu principal |
| `Ctrl+Échap` | Forcer la fermeture |

---

## Paramètres des simulations

### MCU

| Paramètre | Plage | Pas |
|-----------|-------|-----|
| R — Rayon | 2,0 – 20,0 | 0,5 |
| ω — Facteur de vitesse (adimensionnel) | 0,1 – 6,0 | 0,1 |
| drag — Amortissement | 0,0 – 1,0 | 0,01 |

> **Note :** ω n'est **pas** en rad/s. C'est un multiplicateur adimensionnel : ω=1 correspond à une révolution complète sur la durée totale de la simulation. La position est calculée analytiquement par `x = R·cos(ω·t)`, `y = R·sin(ω·t)` où `t ∈ [0, 2π]`.

**Presets standards :** Orbite stable · Spirale · Rapide

---

### Cône

| Paramètre | Plage | Pas |
|-----------|-------|-----|
| α — Pente du cône | 0,05 – 0,50 | 0,005 |
| μ — Frottement | 0,0 – 0,30 | 0,002 |
| r₀ — Position initiale | 0,05 – 0,39 m | 0,01 |
| v₀ — Vitesse initiale | 0,0 – 3,0 m/s | 0,05 |
| φ₀ — Angle initial | 0 – 360° | 5° |

**Presets standards :** Présentation · Sans frottement · Pente forte

---

### Membrane

| Paramètre | Plage | Pas |
|-----------|-------|-----|
| F — Force centrale | 0,1 – 15,0 N | 0,1 |
| T — Tension de la membrane | 1,0 – 50,0 N/m | 0,5 |
| μ — Frottement | 0,0 – 0,30 | 0,002 |
| r₀ — Position initiale | 0,05 – 0,39 m | 0,01 |
| v₀ — Vitesse initiale | 0,0 – 3,0 m/s | 0,05 |
| φ₀ — Angle initial | 0 – 360° | 5° |

**Presets standards :** Présentation · Puits profond · Sans frottement

---

### ML

| Paramètre | Plage | Pas |
|-----------|-------|-----|
| σ — Bruit | 0,0 – 5,0 | 0,1 |
| ratio — Proportion d'observations | 0,05 – 1,0 | 0,05 |

**Presets standards :** Données propres · Données bruitées · Observations rares

---

### Chaos

| Paramètre | Plage | Pas |
|-----------|-------|-----|
| n — Nombre de billes | 2 – 10 | 1 |
| Δφ — Écart angulaire par bille | 0 – 15°/bille | 0,5° |
| Δr — Écart radial | 0 – 0,05 m/bille | 0,002 |
| Δv — Écart de vitesse | 0 – 0,20 m/s/bille | 0,01 |
| intervalle — Décalage de lancement | 0 – 200 frames | 10 |
| α, μ, r₀, v₀, φ₀ | Mêmes plages que Cône | — |
| e — Coefficient de restitution | 0 – 1 | — |

**Presets standards :** Papillon · Tempête · Décalé

---

## Panneau de paramètres (Ctrl+P)

Disponible dans tous les modes, masqué par défaut.

- Overlay ancré sur le bord droit, pleine hauteur
- Sliders avec 200 pas pour un contrôle précis
- Affichage de la valeur courante en temps réel
- Débounce de 300 ms sur les changements (évite les recalculs excessifs)
- Paramètres lus dynamiquement depuis `PARAM_RANGES` de la simulation active

---

## Tableau comparatif des modes

| Fonctionnalité | Normal | Présentation | Libre |
|---------------|--------|--------------|-------|
| Simulations accessibles | 5 (1–5) | 4 (1–4, sans Chaos) | 4 en menu + toutes dans les vues dédiées |
| Navigation | Clavier (`1–5`, `←→`) | Clavier (`1–4`, `←→`, auto-démarrage) | Clics dans le menu |
| Tableau de bord (sliders) | Non | Non | Oui (panneau gauche complet) |
| Panneau de paramètres | `Ctrl+P` overlay | `Ctrl+P` overlay | `Ctrl+P` overlay |
| Métriques en direct | Non | Non | Oui (`MetricsPanel`) |
| Graphe r(t) | Non | Non | Oui (`_LiveChartsPanel`) |
| Page de théorie | Non | Non | Oui |
| Scénarios guidés | Non | Non | Oui (3 scénarios) |
| Cas extrêmes | Non | Non | Oui (`ExtremeCasesView`) |
| Vue de comparaison | Non | Non | Oui |
| Presets | F1–F3 (standards) | F1–F3 (versions présentation) | F1–F3 (depuis tableau de bord) |
| Quitter | `Ctrl+Alt+Échap` | `Échap` | `Ctrl+Échap` |
| Retour au menu | `Échap` | — | `Échap` |
