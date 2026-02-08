# GUI README

This document outlines the structure, conventions, and how to run and develop the Dash-based GUI under `src/gui`. The app is a single-page Dash app: the navbar controls which content layout is displayed, without changing the URL.

## Overview

- Framework: Dash + dash-bootstrap-components (dbc)
- Theme: `dbc.themes.FLATLY`
- Structure:
  - `app.py`: Application entrypoint, app initialization, layout, and main callbacks.
  - `components/`: Reusable view components (e.g., `navbar.py`).
  - `pages/`: Page layout functions. Even though the app is single-page, these modules provide content blocks (Home, Activities, Simulations, Plots).
  - `utils/`: Shared utilities and centralized callback registration (`helpers.py`).
  - `assets/`: Front-end assets automatically loaded by Dash (e.g., theme init JS).

## Directory Layout

- `src/gui/app.py`
  - Creates the Dash app, applies the FLATLY theme and Font Awesome.
  - Uses a single-page approach: the navbar buttons drive the content displayed via a store (`page-store`).
  - Wraps only the content area (`page-content`) in `dcc.Loading` for a scoped spinner.
  - Registers centralized callbacks from `utils/helpers.py`.

- `src/gui/components/navbar.py`
  - Exposes `Navbar` with a static `render()` method returning native Dash components.
  - Provides a color mode switch (`dbc.Switch`) with moon/sun labels.
  - Uses `dbc.Button` for nav controls so FLATLY theme styles apply.
  - Export convenience: `navbar = Navbar`.

- `src/gui/pages/`
  - `home.py`, `activities.py`, `simulations.py`, `plots.py` each expose a `layout()` function returning content for the page.
  - These are pure layout functions returning only native Dash/dbc components and Python dict/list for figures.

- `src/gui/utils/helpers.py`
  - `register_all(app)`: Centralized callback registrations.
  - Contains a clientside callback that toggles Bootstrap color theme via the navbar switch.
  - Contains example server callbacks kept minimal and safe (`no_update` default behavior).

- `src/gui/assets/`
  - `init-theme.js`: Sets initial Bootstrap theme to `light` before Dash renders.
  - You can add other assets as needed (CSS/JS) — Dash will auto-load them.

## Running the App

1. Ensure dependencies are installed:
   - Python 3.10+
   - dash
   - dash-bootstrap-components
   - (Optional) plotly (if you need advanced figures)

2. Start the app:
   - From the project root, run the Python module or script that starts `src/gui/app.py`.
   - Typical command: `python -m src.gui.app` or `python src/gui/app.py` depending on your environment setup.

3. Open the app:
   - Visit `http://127.0.0.1:8050` in your browser.

## Conventions

- Components:
  - Prefer `dbc` components over raw `html` when UI styling should follow the Bootstrap theme.
  - Use `className` (not `class_name`) for CSS classes on Dash components.

- Figures:
  - Use pure Python dict/list structures for `dcc.Graph(figure=...)` to avoid non-serializable objects in props.

- Classes:
  - If a class is used for a component, provide static methods (e.g., `Navbar.render()`) so it can be used without instantiation.

- Callbacks:
  - Centralize callback registration in `utils/helpers.py` with a single `register_all(app)`.
  - For lightweight UI effects (like theme toggle), prefer clientside callbacks — return `window.dash_clientside.no_update` when you don’t intend to update any Dash props.

- Single-page behavior:
  - The app does not rely on URL routing. Navbar buttons trigger callbacks that set the selected section in `dcc.Store`.
  - The content area is re-rendered from the store. The navbar stays fixed.

- Loading behavior:
  - Only the content area (`page-content`) is wrapped in `dcc.Loading`. This keeps the navbar static and applies spinner only where it matters.
  - Avoid global overlays: no custom CSS is required for loading states.

## Theming and Color Mode

- Initial theme:
  - Set to `light` by `assets/init-theme.js` at startup.

- Color mode switch:
  - Located in the navbar (`dbc.Switch` with moon/sun labels).
  - A clientside callback toggles `data-bs-theme` between `"light"` and `"dark"` based on the switch value.
  - This approach avoids changing any Dash props and keeps the theme toggle instantaneous.

## Extending Pages

- Each page module exposes `layout()`. Keep these functions:
  - Stateless (no side effects, just return components).
  - Using only native `dash.html`, `dash.dcc`, and `dbc` components.
  - Figures defined as plain dict/list structures.

- If adding heavy components (e.g., large graphs), consider wrapping those components in `dcc.Loading` at the component level for more granular feedback.

## Debugging Tips

- Use the browser console:
  - Client-side errors (e.g., malformed scripts) will block rendering; look for errors there.

## How to Contribute

- Follow the existing file structure and conventions.
- Keep callbacks centralized and minimal.
- When introducing new dependencies, confirm compatibility and document them in this README.
- Write clear docstrings for functions and classes:
  - Explain what they return and any constraints (e.g., props must be serializable).

## Quick Reference

- Entry: `src/gui/app.py`
- Navbar: `src/gui/components/navbar.py` (`Navbar.render()`)
- Pages: `src/gui/pages/*.py` (`layout()` functions)
- Callbacks: `src/gui/utils/helpers.py` (`register_all(app)`)
- Assets: `src/gui/assets/` (auto-loaded by Dash)

## Example Development Flow

1. Add a new content section:
   - Create `src/gui/pages/new_section.py` with `layout()` returning components.

2. Wire it to the navbar:
   - Add a `dbc.Button` in the navbar with a unique `id`.
   - Update the store computing callback in `app.py` to handle the new button id and set a corresponding `page` value.
   - Extend the rendering callback to dispatch to `new_section.layout()`.

3. Run and verify:
   - Start the app and use the navbar to switch sections.
   - Confirm theming (FLATLY) and loading behavior is scoped to the content area only.

---
