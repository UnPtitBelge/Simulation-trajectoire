# Project Guidelines

## Scope

- Applies to the whole workspace.
- Use this file as the single workspace instruction source (do not add `AGENTS.md` unless replacing this file).

## Language

- Respond in French for user-facing explanations.
- Keep code identifiers, APIs, and technical terms in their original language.

## Build and Run

- Python version: 3.11+.
- Install runtime deps: `pip install -e .`
- Install dev deps: `pip install -e ".[dev]"`
- Main app: `python src/app.py`
- First-run prerequisites:
  - `python src/scripts/generate_data.py [--workers N]`
  - `python src/scripts/train_models.py [--workers N]`

## Validation Commands

- Format: `black src/`
- Lint: `flake8 src/`
- Type-check: `pyright`
- Physics sanity checks: `python src/scripts/test_simulations.py`
- ML pretrained checks: `python src/scripts/test_ml_models.py`
- Full synth train+predict loop: `python src/scripts/test_synth_training.py [--chunks N]`
- Real-data train+predict loop: `python src/scripts/test_real_training.py [--test-id N] [--passes N]`

## Architecture Landmarks

- App entrypoint and startup checks: `src/app.py`
- Config loading and merge behavior: `src/config/loader.py`
- Physics engines: `src/physics/`
- ML models/training/prediction: `src/ml/models.py`, `src/ml/train.py`, `src/ml/predict.py`
- UI simulation lifecycle and threading contract: `src/ui/base_sim_widget.py`
- Data generation/training scripts: `src/scripts/`

## Project-Specific Conventions

- Internal simulation state is polar: `(r, theta, vr, vtheta)` with `vtheta = r * dtheta/dt`.
- ML learns residuals (`delta features`) rather than absolute next-state features.
- Synthetic and UI cone depth must remain consistent (`cone.toml` vs `ml.toml`), validated at startup.
- Real-data ML pipeline uses pixel/time-step units (no px->m conversion).
- In Qt worker flows, do not replace signal-slot methods with lambdas for cross-thread completion handling.

## Pitfalls to Avoid

- `src/app.py` blocks startup if `src/data/tracking_data.csv` or required synthetic model `.pkl` files are missing.
- Refactors of multiprocessing code in scripts must keep worker functions at module top-level for pickling.
- Keep rendering assumptions aligned:
  - Cone/Membrane widgets are 3D OpenGL.
  - MCU/ML widgets are 2D pyqtgraph.

## Link, Don’t Embed

- General project usage and quickstart: `README.md`
- High-level architecture notes: `docs/architecture.md`
- ML deep dive: `src/ml/README.md`
- Physics details: `src/physics/README.md`
- Script pipeline details: `src/scripts/README.md`
- Additional project conventions and rationale: `CLAUDE.md`

## Editing Guidance

- Prefer minimal, focused diffs.
- Preserve existing public APIs and naming unless a task explicitly requires breaking changes.
- When changing behavior, update nearby docs/README in the same area if they become stale.
