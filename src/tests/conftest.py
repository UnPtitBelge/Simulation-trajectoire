"""pytest configuration — adds src/gui_Qt/ to sys.path.

This allows test files to import the simulation modules with the same bare
imports used by the application itself (``from utils.params import ...``).
"""
import sys
from pathlib import Path

_GUI_QT = Path(__file__).resolve().parent.parent / "gui_Qt"
if str(_GUI_QT) not in sys.path:
    sys.path.insert(0, str(_GUI_QT))
