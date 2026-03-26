# Code Review — Simulation Trajectoire

> Revue complète du code source selon les principes de conception orientée objet :
> SOLID, Loi de Déméter, cohésion/couplage, responsabilité unique.
>
> Référence : https://fpluquet.github.io/cours-java/cours/genie-logiciel/conception-orientee-objet.html

---

## Table des matières

1. [Bilan général](#1-bilan-général)
2. [Analyse SOLID](#2-analyse-solid)
3. [Loi de Déméter](#3-loi-de-déméter)
4. [Cohésion & Couplage](#4-cohésion--couplage)
5. [Problèmes identifiés](#5-problèmes-identifiés)
6. [Points forts](#6-points-forts)
7. [Recommandations priorisées](#7-recommandations-priorisées)

---

## 1. Bilan général

| Critère | Note | Commentaire |
|---------|------|-------------|
| Structure des modules | ✅ Bonne | Séparation core / simulations / ui / utils |
| Responsabilité unique | ⚠️ Partielle | `MainWindow` cumule trop de rôles |
| Ouvert/Fermé | ✅ Bonne | Presets extensibles sans modifier les classes |
| Substitution de Liskov | ✅ Respecté | `Plot` → `Plot3dBase` → `PlotCone/Membrane` fonctionne |
| Ségrégation d'interface | ✅ Bonne | `BaseMode` n'expose qu'`apply()` |
| Inversion de dépendances | ⚠️ Partielle | Modes reçoivent `win` typé `MainWindow` concret |
| Loi de Déméter | ⚠️ Partielle | Quelques chaînes trop longues |
| Code mort | ❌ Présent | Version parallèle du cône désactivée mais présente |
| Sécurité des exceptions | ❌ Problème | `setup()` peut marquer `_ready=True` après une erreur |

**Note globale : 7/10**

---

## 2. Analyse SOLID

### S — Principe de responsabilité unique (SRP)

#### ❌ Violation principale : `MainWindow`

`MainWindow` (`src/ui/main_window.py`) cumule au moins **6 responsabilités distinctes** :

| Responsabilité | Méthodes concernées |
|----------------|---------------------|
| Gestion de la pile de pages | `show_menu()`, `show_presentation()`, `open_dashboard()`, `_open_theory()`, `_open_scenario()`, `_open_scenario_sim()` |
| Cycle de vie des simulations | `activate_sim()`, `next_sim()`, `prev_sim()`, `current_plot()`, `apply_current_preset()` |
| Construction du widget de présentation | `_build_presentation()`, `set_status()` |
| Construction des pages scénario | `_build_scenario_page()` (80+ lignes) |
| Gestion du cache | `_scenario_cache`, `_scen_sim_cache` |
| Filtrage clavier | `eventFilter()`, `keyPressEvent()` |

**Conséquence :** La classe fait plus de 400 lignes et est difficile à tester unitairement.

**Refactorisation suggérée :**

```
MainWindow
├── PageNavigator          → gérer le QStackedWidget et les indices de pages
├── SimulationManager      → plots[], keys[], dashboards[], presets
├── PresentationController → widget de présentation, labels, set_status()
└── ScenarioPageBuilder    → _build_scenario_page() extrait dans src/ui/
```

---

#### ✅ Respect du SRP : `BaseMode` et sous-classes

`BaseMode`, `LibreMode`, `PresentationMode`, `NormalMode` ont chacune **une seule mission** : configurer le comportement de la fenêtre selon le mode d'affichage. Aucun mode ne fait de physique ni de layout.

---

#### ✅ Respect du SRP : `simulate_cone()`, `simulate_membrane()`

Les fonctions de simulation sont des **fonctions pures** (données en entrée → données en sortie, aucun effet de bord UI). `PlotCone` orchestre le rendu, `simulate_cone()` fait le calcul. Bonne séparation.

---

### O — Principe Ouvert/Fermé (OCP)

#### ✅ Respect via le système de presets

Ajouter un nouveau preset à une simulation se fait **sans modifier les classes** : il suffit d'ajouter une entrée dans `PRESETS` du `@dataclass` correspondant.

```python
# ConeParams.PRESETS — extensible sans modifier PlotCone
PRESETS = {
    "orbite_stable": {"label": "Orbite stable", "slope": 0.20, ...},
    # Ajouter ici un nouveau preset sans toucher à rien d'autre
    "nouveau_preset": {"label": "Nouveau", "slope": 0.35, ...},
}
```

#### ✅ Respect via `BaseMode`

Ajouter un quatrième mode (ex: `KioskMode`) ne modifie pas les modes existants.

#### ~~⚠️ Violation partielle : indices de pages codés en dur~~ ✅ Résolu

```python
# src/ui/main_window.py — implémentation actuelle
class Page(IntEnum):
    PRES   = 0
    MENU   = 1
    DASH   = 2
    SCEN   = 3
    THEORY = 4
    STORY  = 5
    EXTREME = 6  # lazy-loaded ExtremeCasesView
```

`Page(IntEnum)` utilisé dans tous les `setCurrentIndex(Page.X)`. Ajouter une page ne nécessite plus de chasser les entiers magiques.

---

### L — Principe de substitution de Liskov (LSP)

#### ✅ Respecté dans la hiérarchie `Plot`

`Plot3dBase` hérite de `Plot` et respecte son contrat : `setup()`, `start()`, `stop()`, `reset()`, `apply_preset()` fonctionnent identiquement. `PlotCone` et `PlotMembrane` héritent de `Plot3dBase` et ne violent pas les préconditions parentales.

#### ✅ Respecté dans `BaseParams`

Tous les `@dataclass` enfants (`ConeParams`, `MCUParams`, etc.) héritent de `BaseParams` et implémentent `PRESETS` — `from_preset()` fonctionne pour chacun sans surprise.

---

### I — Principe de ségrégation d'interface (ISP)

#### ✅ `BaseMode` minimal

```python
class BaseMode(ABC):
    @abstractmethod
    def apply(self, win) -> None: ...
```

Interface la plus fine possible. Chaque mode n'implémente que ce dont il a besoin.

#### ⚠️ `Plot` : interface trop large pour `ScenarioSimView`

`ScenarioSimView` utilise `plot.start`, `plot.stop`, `plot.reset`, `plot.apply_preset`, `plot.widget` et `plot.params.PRESETS`. Elle dépend de l'implémentation concrète de `Plot`, pas d'une abstraction. Si on extrayait un protocole `IPlot`, `ScenarioSimView` serait plus découplée.

---

### D — Principe d'inversion de dépendances (DIP)

#### ⚠️ Les modes dépendent de `MainWindow` concret

```python
# src/ui/modes/libre.py
def eventFilter(self, win, event):
    win._allow_close = True      # accès direct à attribut privé
    win.show_menu()              # appel de méthode concrète
    win.current_plot()           # idem
```

Les modes dépendent de l'implémentation de `MainWindow` et non d'une abstraction. Si `MainWindow` est remplacé, tous les modes doivent être réécrits.

**Refactorisation suggérée :** définir une interface `IAppWindow` avec les méthodes que les modes ont le droit d'appeler.

```python
class IAppWindow(Protocol):
    def show_menu(self) -> None: ...
    def current_plot(self) -> Plot | None: ...
    def apply_current_preset(self, idx: int) -> None: ...
```

#### ✅ `SimDashboard` reçoit `plot` par injection

```python
class SimDashboard(QWidget):
    def __init__(self, sim_key: str, plot, parent=None):
```

Le dashboard ne crée pas le plot — il le reçoit. Bonne inversion de dépendance.

---

## 3. Loi de Déméter

**Règle :** Ne parler qu'à ses collaborateurs immédiats. Éviter `a.getB().getC().doSomething()`.

#### ❌ Violation dans `SimDashboard`

```python
# src/ui/dashboard/sim_dashboard.py:108
for i, (_key, preset) in enumerate(type(plot.params).PRESETS.items()):
```

Chaîne : `plot` → `.params` → `type(...)` → `.PRESETS`. Le dashboard navigue dans les entrailles du plot pour accéder à des métadonnées de configuration.

**Correction suggérée :** exposer une méthode dédiée sur `Plot`.

```python
# Dans Plot (base.py)
def get_presets(self) -> dict[str, dict]:
    return type(self.params).PRESETS

# Dans SimDashboard
for i, (_key, preset) in enumerate(plot.get_presets().items()):
```

#### ⚠️ Accès à `win._allow_close` dans les filtres

```python
# src/ui/modes/libre.py
win._allow_close = True
win.close()
```

Le filtre accède à un attribut **privé** de `MainWindow`. Violation de l'encapsulation.

**Correction suggérée :**

```python
# Dans MainWindow
def force_close(self) -> None:
    self._allow_close = True
    self.close()

# Dans _LibreFilter
win.force_close()
```

#### ✅ Conforme : `SimDashboard` connecte les signaux sans naviguer

```python
# SimDashboard
plot.frame_updated.connect(self._metrics.update)

# MetricsPanel
plot.frame_updated.connect(self._on_frame)
```

Communication via signaux Qt — aucune navigation dans l'arbre d'objets.

---

## 4. Cohésion & Couplage

### Cohésion

| Classe / Module | Cohésion | Commentaire |
|----------------|----------|-------------|
| `simulate_cone()` | ✅ Forte | Fait uniquement de la physique |
| `BaseParams` + sous-classes | ✅ Forte | Données + presets, rien d'autre |
| `PlotCone`, `PlotMembrane` | ✅ Bonne | Calcul + rendu de leur simulation spécifique |
| `theme.py` | ✅ Forte | Uniquement constantes de style |
| `MainWindow` | ❌ Faible | 6 responsabilités mélangées |
| `sim_dashboard.py` | ⚠️ Moyenne | `SimDashboard`, `ScenarioSimView`, `ComparisonView` dans un seul fichier |

### Couplage

| Relation | Type | Commentaire |
|----------|------|-------------|
| `MainWindow` ↔ `Plot` | Fort | Direct object references, listes indexées |
| `modes/` → `MainWindow` | Fort | Accès aux attributs privés `_allow_close` |
| `SimDashboard` → `Plot` | Moyen | Injection, mais accès à `.params` interne |
| `simulations/` → `core/params/` | Faible | Import de dataclass uniquement |
| `ui/` → `core/content/` | Faible | Lecture seule de dicts |

---

## 5. Problèmes identifiés

### 🔴 Sévérité haute

#### ~~P1 — Exception silencieuse dans `Plot.setup()`~~ ✅ Résolu

~~Si `_compute()` levait une exception, `_ready` pouvait devenir `True` avec un état incohérent.~~

Le passage à l'architecture QThread élimine le problème structurellement : `_ready = True` est désormais positionné **uniquement** dans `_on_compute_done()` (slot appelé dans le thread principal après succès du worker). En cas d'échec, `_on_compute_failed()` positionne `_ready = False`. Le chemin d'erreur et le chemin de succès sont des branches séparées.

#### ~~P2 — Code mort : version parallèle du cône~~ ✅ Résolu

~~`src/simulations/cone.py` contient ~200 lignes de code désactivé (`_simulate_cone_parallel`, `_cone_compute_chunk`) jamais appelées en production.~~

Le code parallèle a été supprimé de `cone.py`.

---

### 🟠 Sévérité moyenne

#### ~~P3 — Duplication de la logique d'initialisation 3D~~ ✅ Résolu

~~Ce patron devrait être extrait dans `Plot3dBase` sous forme de méthode template.~~

`Plot3dBase._setup_3d_scene(mesh, particle_color, trail_color, center_z)` extrait dans `base.py` — utilisé par `PlotCone`, `PlotMembrane` et `PlotChaos`.

#### ~~P4 — Duplication des boutons de préréglages~~ ✅ Résolu

~~Le même bloc de code apparaît dans `SimDashboard.__init__()` **et** `ScenarioSimView.__init__()`.~~

`build_preset_buttons(plot, layout)` extraite dans `src/ui/ui_helpers.py` — importée par `SimDashboard`, `ScenarioSimView` et `ExtremeCasesView`.

#### P5 — Clés magiques pour les simulations

La chaîne `"cone"`, `"mcu"`, `"membrane"`, `"ml"` apparaît dans :
- `SIMULATIONS` tuple (`src/simulations/__init__.py`)
- `SIM` dict (`src/core/content/simulations.py`)
- `PlotCone.SIM_KEY = "cone"` (non défini, absent)
- `SCENARIOS["..."]["sims"]` (`src/core/content/scenarios.py`)
- `self.keys` dans `MainWindow`

Un typo dans l'une de ces occurrences passe silencieusement (le dict retourne `{}`).

**Correction :** Définir un `Enum` partagé :

```python
# src/core/sim_keys.py
from enum import StrEnum

class SimKey(StrEnum):
    MCU = "mcu"
    CONE = "cone"
    MEMBRANE = "membrane"
    ML = "ml"
```

#### ~~P6 — Blocage du thread UI pendant `_compute()`~~ ✅ Résolu

~~`Plot.setup()` appelle `_compute()` dans le thread principal.~~

`_compute()` s'exécute dans un `_ComputeWorker` (via `moveToThread`) dans un `QThread` dédié. Les signaux `finished`/`failed` ramènent le résultat dans le thread principal via connexion *queued*. L'UI reste fluide pendant tout le calcul.

---

### 🟡 Sévérité faible

#### P7 — Cache de scénarios non borné

```python
self._scenario_cache: dict[str, QWidget] = {}
self._scen_sim_cache: dict[tuple[str, int], ScenarioSimView] = {}
```

Ces dictionnaires grandissent sans limite. Avec 10 scénarios × 4 simulations = 40 `ScenarioSimView` potentiels, l'impact mémoire reste faible aujourd'hui, mais constitue un antipattern.

#### ~~P8 — `_build_scenario_page()` trop longue~~ ✅ Résolu

~~La méthode fait **~115 lignes** dans `MainWindow`.~~

`build_scenario_page(key, on_open_sim, on_back)` déplacée dans `src/ui/menu/scenario_page.py` — `MainWindow` l'appelle simplement.

---

## 6. Points forts

### ✅ Architecture en couches propre

```
core/          → données pures (params, content, geometry)
simulations/   → calcul physique + rendu
ui/            → layout + interaction
utils/         → transversal (theme, shortcuts, logger)
```

Aucune dépendance cyclique. Les couches inférieures n'importent pas les couches supérieures.

### ✅ Patron Template Method bien utilisé

`Plot.setup()` → `_compute()` → `_draw_initial()` → `_draw(i)` est un Template Method classique. Les sous-classes surchargent les étapes sans dupliquer l'orchestration.

### ✅ Signaux Qt pour le découplage

`frame_updated` et `setup_done` permettent à `SimDashboard` et `ScenarioSimView` de réagir aux changements du plot **sans le connaître en détail**. C'est l'Observer Pattern appliqué correctement.

### ✅ Contenu éducatif séparé du code

`SIM`, `SCENARIOS`, `THEORY` sont des dictionnaires de données pures dans `src/core/content/`. Modifier le texte, ajouter une question ou une étape guidée ne touche jamais au code de simulation. Bonne séparation.

### ✅ Système de presets extensible

`BaseParams.from_preset()` combiné aux `PRESETS: ClassVar[dict]` dans chaque sous-classe constitue un patron de configuration simple et extensible. Ajouter un nouveau preset ne modifie aucune classe existante (OCP respecté).

### ✅ Thème centralisé

Toutes les couleurs et tailles de police sont des constantes dans `theme.py`. Aucune valeur codée en dur dans les fichiers UI. Un changement de design ne nécessite de modifier qu'un seul fichier.

---

## 7. Recommandations priorisées

### Priorité 1 — Corrections critiques

| # | Action | Fichier | Impact | Statut |
|---|--------|---------|--------|--------|
| R1 | ~~Corriger `_ready = True` après exception dans `setup()`~~ | `src/simulations/base.py` | Évite crash silencieux | ✅ Résolu — `_ready = True` n'est positionné que dans `_on_compute_done()`, jamais dans le chemin d'erreur |
| R2 | ~~Supprimer le code mort de la version parallèle~~ | `src/simulations/cone.py` | -200 lignes, clarté | ✅ Résolu |
| R3 | Encapsuler `_allow_close` via `force_close()` | `src/ui/main_window.py` | Encapsulation | ✅ Résolu |

### Priorité 2 — Améliorations OO

| # | Action | Fichier | Principe | Statut |
|---|--------|---------|----------|--------|
| R4 | ~~Extraire `build_preset_buttons()`~~ | `src/ui/ui_helpers.py` | DRY, SRP | ✅ Résolu |
| R5 | Créer `SimKey(StrEnum)` | `src/core/sim_keys.py` (nouveau) | Type safety, OCP | ⏳ Ouvert |
| R6 | ~~Exposer `plot.get_presets()`~~ | `src/simulations/base.py` | Loi de Déméter | ✅ Résolu |
| R7 | ~~Déplacer `_build_scenario_page()`~~ | `src/ui/menu/scenario_page.py` | SRP | ✅ Résolu |
| R8 | ~~Convertir indices de pages en `Enum`~~ | `src/ui/main_window.py` | OCP | ✅ Résolu — `Page(IntEnum)` avec EXTREME=6 |

### Priorité 3 — Qualité long terme

| # | Action | Impact | Statut |
|---|--------|--------|--------|
| R9 | ~~Thread `_compute()` via `QThread`~~ | UX : plus de gel UI | ✅ Résolu — `_ComputeWorker` + QThread |
| R10 | Définir protocole `IAppWindow` pour les modes | DIP | ⏳ Ouvert |
| R11 | ~~Extraire `Plot3dBase._setup_3d_common()`~~ | DRY | ✅ Résolu — `_setup_3d_scene()` |
| R12 | Borner les caches avec `functools.lru_cache` ou taille max | Mémoire | ⏳ Ouvert |
