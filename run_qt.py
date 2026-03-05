#!/usr/bin/env python
"""Root-level launcher for the Qt simulation application.

Run the app from anywhere inside the project tree::

    python run_qt.py
    python run_qt.py --debug

This script is an intentionally thin shim — it contains no application
logic of its own.  Everything lives in ``src/gui_Qt/main.py``; this file
only does the two things that ``main.py`` cannot do for itself when it is
invoked from the project root:

1. **Verify** the expected source directory exists and give a clear error
   message if the project layout has been broken.
2. **Patch sys.path** so that the bare package imports inside
   ``src/gui_Qt/`` (``utils``, ``widgets``, ``simulations``) resolve
   correctly regardless of the working directory.

After those two steps it imports ``main`` and delegates entirely to
``main.main()``.  All argument parsing, logging setup, window creation
and the Qt event loop live there.

Why a wrapper script rather than ``cd src/gui_Qt && python main.py``?
----------------------------------------------------------------------
- It lets any tooling (IDE run configurations, shell aliases, ``make``)
  target a single, stable entry point at the project root.
- It keeps ``main.py`` runnable *both* ways — directly from inside
  ``src/gui_Qt/`` and via this launcher — without any changes to
  ``main.py`` itself.
- It avoids hard-coding a ``sys.path`` manipulation inside ``main.py``,
  which would break if ``main.py`` were ever packaged or installed.

Why ``sys.path.insert(0, ...)`` rather than append?
----------------------------------------------------
Prepending gives ``src/gui_Qt/`` priority over any same-named package
that might be installed globally (e.g. a stale ``utils`` from another
project in the same venv).  The insertion is skipped when the directory
is already present so re-importing this module is idempotent.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate src/gui_Qt/ relative to this file
# ---------------------------------------------------------------------------

# This file lives at:  <project_root>/run_qt.py
# Target directory:    <project_root>/src/gui_Qt/
_PROJECT_ROOT = Path(__file__).resolve().parent
_GUI_QT_DIR = _PROJECT_ROOT / "src" / "gui_Qt"

if not _GUI_QT_DIR.is_dir():
    sys.exit(
        f"[run_qt] ERROR: Qt app directory not found:\n"
        f"  {_GUI_QT_DIR}\n"
        f"Make sure the project structure is intact "
        f"(expected src/gui_Qt/ at the project root)."
    )

# ---------------------------------------------------------------------------
# Patch sys.path so bare imports inside src/gui_Qt/ resolve correctly
# ---------------------------------------------------------------------------

_GUI_QT_DIR_STR = str(_GUI_QT_DIR)
if _GUI_QT_DIR_STR not in sys.path:
    sys.path.insert(0, _GUI_QT_DIR_STR)

# ---------------------------------------------------------------------------
# Hand off to main.py — no logic duplication
# ---------------------------------------------------------------------------

# Importing ``main`` runs its module-level code: CLI arg parsing and
# logging setup.  The ``if __name__ == "__main__"`` guard inside main.py
# is NOT triggered here (because __name__ == "main", not "__main__"),
# so the Qt event loop is only started by the explicit main.main() call
# below.
import main  # noqa: E402  (intentional late import after sys.path patch)  # type: ignore[import-not-found]

if __name__ == "__main__":
    main.main()
