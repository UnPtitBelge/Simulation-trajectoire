"""
Multipage Dash application shell.

- Uses a Bootstrap-themed navbar (dbc.themes.FLATLY).
- URL-based routing via `dcc.Location(id="url")` to enable proper page links.
- A small in-file "README" (below) explains how teammates can extend this app.

Team README:
1) Architecture
   - Multipage app: the URL (from `dcc.Location`) determines which page layout is rendered.
   - Pages are implemented in `src/gui/pages/*.py` as functions returning Dash components.
   - The navbar should use link components (e.g., `dcc.Link` or `dbc.NavLink`) to navigate and update the URL.

2) Adding a new section
   - Create a function `layout()` in `src/gui/pages/<new>.py`.
   - Add a new navbar link to the target path (e.g., "/new").
   - Update the routing callback to map the new path to your page.

3) Callbacks
   - All global callbacks (e.g., theme toggles) are registered in `utils/helpers.py`.
   - URL routing callback is defined in `utils/callbacks.py` (reads `dcc.Location` instead of an in-memory store).

4) Styling
   - Use dash_bootstrap_components (dbc) to get theme-aware components.
   - Avoid custom CSS unless absolutely required; prefer dbc components.

5) Debugging
   - If content shows "Loading" indefinitely, check for exceptions in page layout functions.
   - Use `suppress_callback_exceptions=True` to allow components not in the initial layout.

"""

import dash
from components import navbar

# Multipage routing uses callbacks; remove direct page imports to avoid unused warnings
from utils import callbacks
from utils.ui import EXTERNAL_STYLESHEETS, page_shell

app = dash.Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    suppress_callback_exceptions=True,
)
server = app.server

# Register all callbacks centrally from utils.callbacks.
callbacks.register_all(app)

# Define the app layout with a navbar and content
# Application layout:
# - `dcc.Location(id="url")` tracks the current URL for multipage navigation.
# - `navbar.render()` returns the static navbar.
# - `page-content` is wrapped in dcc.Loading so only content shows a spinner while updating.
app.layout = page_shell(
    navbar_component=navbar.render(),
    url_id="url",
    content_id="page-content",
    loader_type="circle",
    fluid=True,
)

if __name__ == "__main__":
    app.run(debug=True)
