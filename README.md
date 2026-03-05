# Simulation de trajectoires

Interactive physics simulation suite modelling a particle orbiting a heavy sphere resting on a deformable membrane. Includes a Qt desktop application, standalone Newtonian and ML simulations, and a video ball-tracking tool.

---

## Project structure

```
Simulation-trajectoire/
├── run_qt.py                         # Entry point for the Qt application
├── requirements.txt
├── src/
│   ├── gui_Qt/                       # Qt desktop application
│   │   ├── main.py                   # Window, tab layout, app bootstrap
│   │   ├── widgets/
│   │   │   ├── SimWidget.py          # Base simulation widget + playback controls
│   │   │   └── VideoPlayerWidget.py
│   │   ├── simulations/
│   │   │   ├── Plot.py               # Abstract animation base class
│   │   │   ├── sim2d/                # 2D orbital simulation (pyqtgraph)
│   │   │   ├── sim3d/                # 3D membrane simulation (pyqtgraph OpenGL)
│   │   │   └── simML/                # ML linear-regression trajectory demo
│   │   └── utils/
│   │       ├── stylesheet.py         # Centralised colour tokens and QSS strings
│   │       ├── params.py             # Simulation parameter dataclasses
│   │       ├── params_controller.py  # Auto-generated parameter UI panel
│   │       ├── math_helpers.py       # Membrane deformation model and geometry
│   │       └── logger.py
│   ├── simulations/                  # Standalone (non-Qt) simulations
│   │   ├── simu_newtonienne/
│   │   └── simu_machine_learning/
│   └── tracking/                     # OpenCV ball-tracking tool
├── data/
└── logs/
```

---

## Physics model

The 3D simulation models a circular rubber-sheet membrane of radius **R** and tension **T** loaded at its centre by a sphere of mass **m**. The vertical deflection follows:

```
z(r) = -F / (2πT) · ln(R / r),   F = m · g
```

A particle is launched from an initial position with a configurable speed and angle. Its trajectory is integrated with explicit Euler steps, accounting for the surface gradient (gravitational slope) and viscous friction. The simulation stops when the particle reaches the rim, contacts the central sphere, or exhausts the step budget.

The 2D simulation models a particle orbiting a central body under Newtonian gravity with optional linear drag, integrated with Velocity-Verlet.

---

## Requirements

- Python ≥ 3.13
- An OpenGL-capable display (required for the 3D tab)

---

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running

### Qt application (all simulations)

```bash
python run_qt.py          # normal mode
python run_qt.py --debug  # verbose logging to console and logs/
```

The application opens full-screen with four tabs:

| Tab | Description |
|-----|-------------|
| **2D Simulation** | Top-down orbital trajectory with Newtonian gravity and drag |
| **3D Simulation** | 3D membrane deformation with a rolling particle (OpenGL) |
| **ML Simulation** | Linear-regression trajectory prediction demo |
| **Video Player** | Load and play local video files |

Press **Ctrl+P** (or click **⚙ Controls**) in any simulation tab to open the parameter panel. All parameters update the simulation live. Other shortcuts:

| Shortcut | Action |
|----------|--------|
| `Space` | Pause / resume |
| `Ctrl+R` | Reset to frame 0 |
| `Ctrl+P` | Toggle parameter panel |

### Standalone simulations

```bash
# Newtonian simulation
cd src/simulations/simu_newtonienne && python3 main.py

# Machine-learning simulation
cd src/simulations/simu_machine_learning && python3 main.py
```

### Ball-tracking tool

```bash
python src/tracking/main.py [--path_video PATH_VIDEO] [--save_data]
```

| Option | Description |
|--------|-------------|
| `--path_video PATH` | Path to the video (relative to `src/tracking/resources/`). Defaults to `big_blue.mp4`. |
| `--save_data` | Append tracked positions to `src/tracking/outputs/tracking_data.csv`. |

Processed images and videos are saved under `src/tracking/outputs/`. To clear all output files:

```bash
./src/tracking/cleanOutputs.sh
```

---

## Simulation parameters (3D)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `surface_tension` | Membrane tension T [N/m] | 13.0 |
| `surface_radius` | Membrane radius R [m] | 0.8 |
| `center_radius` | Central sphere radius [m] | 0.05 |
| `center_mass` | Central sphere mass [kg] — controls deformation depth via F = m·g | 0.8 |
| `g` | Gravitational acceleration [m/s²] | 9.81 |
| `particle_radius` | Moving particle radius [m] | 0.025 |
| `x0`, `y0` | Initial particle position [m] | 0.8, 0.0 |
| `v_i` | Initial speed [m/s] | 0.5 |
| `theta` | Launch angle [°] (0 = radially inward, 90 = tangential CCW) | 45.0 |
| `friction_coef` | Viscous friction coefficient [kg/s] | 0.3 |
| `time_step` | Euler integration step dt [s] | 0.01 |
| `num_steps` | Maximum integration steps | 800 |

---

## Theming

All colours and QSS strings are defined in a single file:

```
src/gui_Qt/utils/stylesheet.py
```

Colour tokens are plain string constants at the top (e.g. `CLR_ACCENT`, `CLR_PANEL_BG`, `CLR_TEXT`). Pre-built style strings (`APP_STYLESHEET`, `PARAM_PANEL_STYLE`, `VIDEO_PLAYER_STYLE`, …) are composed from those tokens. To retheme the entire application, only this file needs to change.

---

## Logs

Log files are written to the `logs/` directory at the project root. Run with `--debug` to enable verbose output.
```

---

Since I don't have a file-write tool available in this session, you'll need to paste the above into `README.md` yourself. The content covers:

- **Project structure** — full directory tree with one-line descriptions of each important file
- **Physics model** — the membrane deflection formula and a plain-English summary of both 2D and 3D simulations
- **Installation** — venv setup and pip install
- **Running** — the Qt launcher, standalone sims, and the tracking tool, each with their CLI options
- **Parameters table** — all 3D sim fields with units and defaults
- **Theming** — where to find and change colours
- **Logs** — where log files go and how to enable debug output
