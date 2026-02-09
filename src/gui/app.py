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
from utils import helpers

# Initialize the Dash app with FLATLY theme and allow callbacks for components not yet in the layout
# Initialize the Dash app with FLATLY theme and allow callbacks that reference
# components not yet present in the initial layout.
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css",
    ],
    suppress_callback_exceptions=True,
)
server = app.server

# Register centralized callbacks (e.g., color mode toggle).
helpers.register_all(app)

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


# First step: compute which section to render based on navbar button clicks
@app.callback(
    dash.Output("page-store", "data"),
    [
        dash.Input("btn-home", "n_clicks"),
        dash.Input("btn-activities", "n_clicks"),
        dash.Input("btn-simulations", "n_clicks"),
        dash.Input("btn-plots", "n_clicks"),
    ],
)
def compute_page_store(n_home, n_activities, n_simulations, n_plots):
    """
    Determine which section should render based on the most recent navbar button click.

    Returns:
        dict: {"page": str} where str is one of "/", "/activities", "/simulations", "/plots".
              Defaults to "/" (home) if nothing has triggered yet.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        page = "/"
    else:
        trig_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trig_id == "btn-home":
            page = "/"
        elif trig_id == "btn-activities":
            page = "/activities"
        elif trig_id == "btn-simulations":
            page = "/simulations"
        elif trig_id == "btn-plots":
            page = "/plots"
        else:
            page = "/"
    return {"page": page}


# Second step: render from the store
@app.callback(dash.Output("page-content", "children"), dash.Input("page-store", "data"))
def render_page(data):
    """
    Render the content area based on `page-store`.

    Args:
        data (dict | None): A dict with key "page" indicating which section to render.

    Returns:
        Dash component: The layout for the selected section.
                        Defaults to Home when absent or unknown.
    """
    page = (data or {}).get("page", "/")
    if page == "/activities":
        return activities.layout()
    elif page == "/simulations":
        return simulations.layout()
    elif page == "/plots":
        return plots.layout()
    else:
        return home.layout()


if __name__ == "__main__":
    app.run(debug=True)
