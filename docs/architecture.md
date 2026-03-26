# Architecture — Simulation Trajectoire

> Diagrammes de l'architecture du projet au format Mermaid.

---

## Table des matières

1. [Vue d'ensemble des couches](#1-vue-densemble-des-couches)
2. [Diagramme de classes complet](#2-diagramme-de-classes-complet)
3. [Hiérarchie des simulations](#3-hiérarchie-des-simulations)
4. [Flux de données : params → physique → rendu → UI](#4-flux-de-données--params--physique--rendu--ui)
5. [Navigation entre les pages](#5-navigation-entre-les-pages)
6. [Cycle de vie d'une animation](#6-cycle-de-vie-dune-animation)
7. [Dépendances inter-modules](#7-dépendances-inter-modules)
8. [Modes d'application](#8-modes-dapplication)

---

## 1. Vue d'ensemble des couches

```mermaid
graph TD
    subgraph Entry["Point d'entrée"]
        main["main.py"]
        app["application/app.py\nMainApplication"]
    end

    subgraph Core["core/ — Données pures"]
        params["params/\nBaseParams\nConeParams · MCUParams\nMembraneParams · MLParams · ChaosParams"]
        content["content/\nSIM · SCENARIOS\nTHEORY · EXTREME_CASES"]
        geo["geometry.py\ndisk_xy()"]
        phys["physics_constants.py\nGRAVITY · radii"]
    end

    subgraph Sims["simulations/ — Calcul & Rendu"]
        base["base.py\nPlot · Plot3dBase"]
        cone["cone.py\nPlotCone\nsimulate_cone()"]
        mcu["mcu.py\nPlotMCU"]
        membrane["membrane.py\nPlotMembrane\nsimulate_membrane()"]
        ml["ml.py\nPlotML\nsimulate_ml()"]
        chaos["chaos.py\nPlotChaos"]
    end

    subgraph UI["ui/ — Interface"]
        mw["main_window.py\nMainWindow"]
        modes["modes/\nLibreMode · PresentationMode\nNormalMode"]
        dash["dashboard/\nSimDashboard · ScenarioSimView\nExtremeCasesView · ComparisonView\nMetricsPanel"]
        menu["menu/\nbuild_menu()"]
        theory["theory.py\nTheoryPage"]
    end

    subgraph Utils["utils/ — Transversal"]
        theme["theme.py\nCLR_* · FS_* · STYLESHEET"]
        shortcuts["shortcuts.py\nPRESENTATION_KEYS"]
        logger["logger.py"]
    end

    main --> app
    app --> mw
    app --> modes
    mw --> dash
    mw --> menu
    mw --> theory
    dash --> base
    base --> params
    cone --> params
    mcu --> params
    membrane --> params
    ml --> params
    mw --> content
    menu --> content
    dash --> content
    UI --> Utils
    Sims --> Utils
```

---

## 2. Diagramme de classes complet

```mermaid
classDiagram
    %% ── Params ───────────────────────────────────────────────
    class BaseParams {
        +PRESETS : ClassVar[dict]
        +from_preset(name: str) Self
    }
    class ConeParams {
        +slope: float
        +friction: float
        +r0: float
        +v0: float
        +phi0: float
        +R_cone: float
        +PRESETS: ClassVar[dict]
    }
    class MCUParams {
        +R: float
        +omega: float
        +drag: float
        +center_radius: float
        +n_frames: int
        +PRESETS: ClassVar[dict]
    }
    class MembraneParams {
        +F: float
        +T: float
        +friction: float
        +r0: float
        +v0: float
        +phi0: float
        +R_membrane: float
        +A: float
        +PRESETS: ClassVar[dict]
    }
    class MLParams {
        +noise: float
        +observation_ratio: float
        +use_csv: bool
        +PRESETS: ClassVar[dict]
    }
    class ChaosParams {
        +n_balls: int
        +delta_phi: float
        +delta_r: float
        +delta_v: float
        +launch_interval: int
        +r0: float
        +v0: float
        +phi0: float
        +slope: float
        +friction: float
        +enable_collisions: bool
        +restitution: float
        +PRESETS: ClassVar[dict]
    }

    BaseParams <|-- ConeParams
    BaseParams <|-- MCUParams
    BaseParams <|-- MembraneParams
    BaseParams <|-- MLParams
    BaseParams <|-- ChaosParams

    %% ── Simulations ──────────────────────────────────────────
    class Plot {
        <<abstract>>
        +params: Any
        +widget: Any
        +frame_updated: Signal
        +setup_done: Signal
        +anim_finished: Signal
        +setup()
        +start()
        +stop()
        +reset()
        +restart()
        +apply_preset(index: int)
        +apply_presentation_preset(index: int)
        +set_speed(factor: float)
        +format_metrics() str
        +get_metrics_schema() list
        +get_frame_metrics(i: int) dict
        +get_chart_data() dict
        +get_presets() dict
        #_compute()*
        #_draw(i: int)*
        #_draw_initial()
        #_get_cache_data() dict
        #_set_cache_data(data: dict)
    }
    class Plot3dBase {
        +widget: GLViewWidget
    }
    class PlotCone {
        +params: ConeParams
        +traj: list
        #_compute()
        #_draw(i: int)
        #_draw_initial()
        #_build_cone_mesh() GLMeshItem
    }
    class PlotMembrane {
        +params: MembraneParams
        +traj: list
        #_compute()
        #_draw(i: int)
        #_draw_initial()
    }
    class PlotMCU {
        +params: MCUParams
        #_compute()
        #_draw(i: int)
        #_draw_initial()
    }
    class PlotML {
        +params: MLParams
        +metrics: dict
        +format_metrics() str
        #_compute()
        #_draw(i: int)
        #_draw_initial()
    }
    class PlotChaos {
        +params: ChaosParams
        +get_metrics_schema() list
        +get_frame_metrics(i: int) dict
        #_compute()
        #_draw(i: int)
        #_draw_initial()
    }

    Plot <|-- Plot3dBase
    Plot3dBase <|-- PlotCone
    Plot3dBase <|-- PlotMembrane
    Plot <|-- PlotChaos
    Plot <|-- PlotMCU
    Plot <|-- PlotML

    PlotCone --> ConeParams
    PlotMembrane --> MembraneParams
    PlotMCU --> MCUParams
    PlotML --> MLParams
    PlotChaos --> ChaosParams

    %% ── UI ───────────────────────────────────────────────────
    class MainWindow {
        +plots: list[Plot]
        +keys: list[str]
        +dashboards: list[SimDashboard]
        +show_menu()
        +show_presentation()
        +open_dashboard(idx: int)
        +activate_sim(idx: int, auto_start: bool)
        +_open_scenario(key: str)
        +_open_scenario_sim(scenario_key: str, sim_idx: int)
        +_open_comparison()
        +_open_theory()
        +current_plot() Plot
        +apply_current_preset(idx: int)
        +set_status(text: str)
        -_scenario_cache: dict
        -_scen_sim_cache: dict
    }
    class SimDashboard {
        +sim_key: str
        +plot: Plot
        +showEvent(event)
        -_sim_host: QWidget
        -_sim_host_lay: QVBoxLayout
    }
    class ExtremeCasesView {
        -_plots: list[Plot]
        -_current_sim_idx: int
        -_plot_host: QWidget
        +showEvent(event)
        -_select_case(idx: int)
        -_apply_current_case()
        -_init_sim_view(idx: int)
    }
    class ScenarioSimView {
        +scenario_key: str
        +sim_key: str
        +plot: Plot
    }
    class ComparisonView {
        -_plots: list[Plot]
        -_keys: list[str]
        -_refresh()
        -_start()
        -_pause()
        -_rst()
    }
    class MetricsPanel {
        +__init__(plot: Plot, parent)
        -_on_frame(i: int)
    }
    class TheoryPage {
        #_build_topic(topic: dict) QFrame
    }

    MainWindow --> SimDashboard
    MainWindow --> ExtremeCasesView
    MainWindow --> ScenarioSimView
    MainWindow --> ComparisonView
    MainWindow --> TheoryPage
    SimDashboard --> Plot
    SimDashboard --> MetricsPanel
    ExtremeCasesView --> Plot
    ScenarioSimView --> Plot
    ComparisonView --> Plot

    %% ── Modes ────────────────────────────────────────────────
    class BaseMode {
        <<abstract>>
        +apply(win)*
    }
    class NormalMode {
        +apply(win)
    }
    class PresentationMode {
        +apply(win)
    }
    class LibreMode {
        +apply(win)
    }

    BaseMode <|-- NormalMode
    BaseMode <|-- PresentationMode
    BaseMode <|-- LibreMode
```

---

## 3. Hiérarchie des simulations

```mermaid
graph LR
    subgraph Abstractions
        QObject["QObject\n(PySide6)"]
        Plot["Plot\n◆ setup()\n◆ start() / stop() / reset()\n◆ apply_preset()\n◆ _compute() abstract\n◆ _draw(i) abstract"]
        Plot3dBase["Plot3dBase\n+ GLViewWidget\n+ caméra 3D"]
    end

    subgraph Concret["Implémentations concrètes"]
        PlotCone["PlotCone\nCône · Euler semi-implicite\nOpenGL 3D"]
        PlotMembrane["PlotMembrane\nLaplace · Verlet vitesse\nOpenGL 3D"]
        PlotChaos["PlotChaos\nEnsemble N billes · Euler\nPyQtGraph/OpenGL mixte"]
        PlotMCU["PlotMCU\nMCU · Analytique\nPyQtGraph 2D"]
        PlotML["PlotML\nRégression linéaire\nPyQtGraph 2D"]
    end

    QObject --> Plot
    Plot --> Plot3dBase
    Plot3dBase --> PlotCone
    Plot3dBase --> PlotMembrane
    Plot --> PlotChaos
    Plot --> PlotMCU
    Plot --> PlotML
```

---

## 4. Flux de données : params → physique → rendu → UI

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant D as SimDashboard
    participant P as Plot (ex: PlotCone)
    participant W as _ComputeWorker (QThread)
    participant GL as GLViewWidget

    U->>D: clic "▶ Lecture"
    D->>P: plot.start()
    P->>P: _check_cache()
    alt Cache HIT
        P->>GL: _draw_initial()
        P->>D: emit setup_done
        P->>P: timer.start() [16ms]
    else Cache MISS
        P->>W: spawn QThread → _compute()
        note over W: calcul physique\ndans le thread worker
        W-->>P: signal finished (queued)
        P->>P: _store_cache()
        P->>GL: _draw_initial()
        P->>D: emit setup_done
        P->>P: timer.start() [16ms]
    end

    loop Chaque tick (16ms)
        P->>P: _tick() — frame accumulator × speed
        P->>GL: _draw(i) — setData(pos=traj[i])
        P->>D: emit frame_updated(i)
    end

    U->>D: clic "F2: Sans frottement"
    D->>P: plot.apply_preset(1)
    P->>P: params = ConeParams.from_preset("sans_frottement")
    P->>W: spawn QThread → _compute() [async]
    W-->>P: signal finished
    P->>GL: _draw_initial()
```

---

## 5. Navigation entre les pages

```mermaid
stateDiagram-v2
    [*] --> Menu : LibreMode.apply()
    [*] --> Présentation : NormalMode / PresentationMode

    Menu --> Dashboard : clic carte simulation
    Menu --> Scénario : clic carte scénario
    Menu --> Théorie : clic "Théorie"
    Menu --> Comparaison : clic "Comparer"
    Menu --> CasExtrêmes : clic "Cas Extrêmes"

    Dashboard --> Menu : ← Retour
    CasExtrêmes --> Menu : ← Retour

    Scénario --> ScénarioSim : clic "Ouvrir la simulation →"
    Scénario --> Menu : ← Retour

    ScénarioSim --> Scénario : ← Retour au scénario

    Théorie --> Menu : ← Retour
    Comparaison --> Menu : ← Retour

    Présentation --> Présentation : touches 1-4 / ← →
    Présentation --> [*] : Échap (PresentationMode)
    Présentation --> Menu : Échap (LibreMode)

    note right of ScénarioSim
        Panneau gauche : étapes + observation
        Panneau droit : simulation + contrôles
    end note
    note right of CasExtrêmes
        Panneau gauche : sélecteur de simulation
        + liste des cas + description
        Panneau droit : simulation (auto-démarrage)
    end note
```

---

## 6. Cycle de vie d'une animation

```mermaid
stateDiagram-v2
    [*] --> Créé : Plot.__init__()

    Créé --> Initialisé : setup() appelé
    Initialisé --> Initialisé : Cache HIT\n→ _draw_initial()
    Initialisé --> Calcul : Cache MISS\n→ _compute()
    Calcul --> Initialisé : résultat stocké\n→ _draw_initial()

    Initialisé --> EnCours : start()
    EnCours --> EnCours : _tick() → _draw(i)
    EnCours --> Pausé : stop()
    Pausé --> EnCours : start()
    EnCours --> Terminé : frame == n_frames
    Terminé --> Initialisé : reset()

    Initialisé --> Recalcul : apply_preset() / restart()
    Recalcul --> Calcul : nouveaux params\n→ cache MISS
    note right of Recalcul
        restart() force le recalcul\net démarre l'animation\nautomatiquement à la fin
    end note
```

---

## 7. Dépendances inter-modules

```mermaid
graph LR
    main["main.py"]
    app["application/\napp.py"]
    mw["ui/\nmain_window.py"]
    modes["ui/modes/"]
    dash["ui/dashboard/"]
    menu["ui/menu/"]
    theory["ui/theory.py"]
    sims["simulations/"]
    base_sim["simulations/\nbase.py"]
    core_params["core/params/"]
    core_content["core/content/"]
    core_geo["core/geometry.py"]
    core_phys["core/physics_constants.py"]
    theme["utils/theme.py"]
    shortcuts["utils/shortcuts.py"]
    logger["utils/logger.py"]

    main --> app
    app --> mw
    app --> modes
    app --> theme
    app --> logger

    mw --> dash
    mw --> menu
    mw --> theory
    mw --> sims
    mw --> core_content
    mw --> theme

    modes --> shortcuts
    dash --> core_content
    dash --> theme
    menu --> core_content
    menu --> shortcuts
    menu --> theme
    theory --> core_content
    theory --> theme

    sims --> base_sim
    base_sim --> core_params
    sims --> core_params
    sims --> core_phys
    sims --> core_geo
    sims --> theme

    style main fill:#e8f0fe,stroke:#1a73e8
    style app fill:#e8f0fe,stroke:#1a73e8
    style theme fill:#fce8e6,stroke:#ea4335
    style core_content fill:#e6f4ea,stroke:#34a853
    style core_params fill:#e6f4ea,stroke:#34a853
```

> Aucune dépendance circulaire. Les couches `core/` ne dépendent d'aucune couche supérieure.

---

## 8. Modes d'application

```mermaid
graph TD
    CLI["main.py\n--mode [normal|presentation|libre]"]

    CLI --> NM["NormalMode\n• Fenêtré 1280×800\n• Démarre sur la sim 0\n• Touche Esc ferme"]
    CLI --> PM["PresentationMode\n• Plein écran\n• Touches 1–4 : changer sim\n• ← → : précédent/suivant\n• Espace/R : lecture/reset\n• F1–F3 : presets\n• Esc : ferme"]
    CLI --> LM["LibreMode\n• Plein écran\n• Démarre sur le menu\n• Esc : retour menu\n• Ctrl+Esc : quitter"]

    NM --> MW["MainWindow"]
    PM --> MW
    LM --> MW

    MW --> KF["Filtre clavier\n_key_filter installé\nselon le mode actif"]

    subgraph Pages["7 pages dans QStackedWidget\n(enum Page dans main_window.py)"]
        P0["0 · PRES — Présentation\n(mode présentation/normal)"]
        P1["1 · MENU — Menu principal\n(mode libre)"]
        P2["2 · DASH — Dashboard simulation"]
        P3["3 · SCEN — Page scénario"]
        P4["4 · THEORY — Page théorie"]
        P5["5 · STORY — Simulation scénario\n(étapes + sim côte à côte)"]
        P6["6 · EXTREME — Cas extrêmes\n(lazy-loaded, mode libre)"]
    end

    MW --> Pages
```
