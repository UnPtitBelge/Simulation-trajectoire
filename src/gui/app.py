"""
Single-page Dash application shell.

- Uses a Bootstrap-themed navbar (dbc.themes.FLATLY).
- Navbar buttons switch the content area without changing the URL.
- A small in-file "README" (below) explains how teammates can extend this app.

Team README:
1) Architecture
   - Single-page app: the navbar triggers callbacks to update `page-content`.
   - `dcc.Store(id="page-store")` holds which section to render ("/", "/activities", "/simulations", "/plots").
   - Pages are implemented in `src/gui/pages/*.py` as functions returning Dash components.

2) Adding a new section
   - Create a function `layout()` in `src/gui/pages/<new>.py`.
   - Add a new navbar `dbc.Button` with a unique id (e.g., `btn-new`).
   - Update `compute_page_store` to map the new button to a path (e.g., "/new").
   - Update `render_page` to return your new page.

3) Callbacks
   - All global callbacks (e.g., theme toggles) are registered in `utils/helpers.py`.
   - Page-change callbacks are defined here in `app.py`.

4) Styling
   - Use dash_bootstrap_components (dbc) to get theme-aware components.
   - Avoid custom CSS unless absolutely required; prefer dbc components.

5) Debugging
   - If content shows "Loading" indefinitely, check for exceptions in page layout functions.
   - Use `suppress_callback_exceptions=True` to allow components not in the initial layout.

"""

import dash
import dash_bootstrap_components as dbc
from components import navbar
from dash import dcc, html
from pages import activities, home, plots, simulations
from utils import callbacks

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css",
    ],
    suppress_callback_exceptions=True,
)
server = app.server

# Register all callbacks centrally from utils.callbacks.
callbacks.register_all(app)

# Define the app layout with a navbar and content
# Application layout:
# - `page-store` tracks which section to render.
# - `navbar.render()` returns the static navbar.
# - `page-content` is wrapped in dcc.Loading so only content shows a spinner while updating.
app.layout = dbc.Container(
    [
        dcc.Store(id="page-store", storage_type="memory"),
        navbar.render(),
        dcc.Loading(
            children=html.Div(id="page-content"),
            type="circle",
        ),
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run(debug=True)
