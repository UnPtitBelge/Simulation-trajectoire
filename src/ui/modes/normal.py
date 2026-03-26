"""Normal application mode."""

from typing import Any

from src.ui.modes.base import BaseMode


class NormalMode(BaseMode):
    def apply(self, win: Any) -> None:
        win.resize(1280, 800)
        win.show()
        win.activate_sim(0)
