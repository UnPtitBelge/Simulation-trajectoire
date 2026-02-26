from __future__ import annotations

import dash


def register_theme_clientside(
    app: dash.Dash,
    switch_id: str = "switch",
    target_span_id: str = "color-mode-switch",
) -> None:
    app.clientside_callback(
        """
        function (switchOn) {
            var root = document.documentElement;
            var mode = switchOn ? "light" : "dark";
            try {
                root.setAttribute("data-bs-theme", mode);
            } catch (e) {
                console && console.warn && console.warn("Theme toggle failed:", e);
            }
            return window.dash_clientside.no_update;
        }
        """,
        dash.Output(target_span_id, "children"),
        dash.Input(switch_id, "value"),
    )


__all__ = ["register_theme_clientside"]
