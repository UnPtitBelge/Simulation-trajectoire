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
