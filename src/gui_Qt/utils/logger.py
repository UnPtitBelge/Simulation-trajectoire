"""Logging configuration for the Qt simulation application.

Call ``setup_logging`` once — at the very start of ``main.py``, before
any other module is imported — to attach two handlers to the root logger:

1. **StreamHandler** — prints to *stderr* (visible in the terminal).
2. **RotatingFileHandler** — writes to ``<project_root>/logs/app.log``,
   rotating at 1 MB and keeping three backup files.

All child loggers (one per module, obtained via
``logging.getLogger(__name__)``) inherit these handlers automatically,
so every module only needs::

    import logging
    log = logging.getLogger(__name__)

and can then call ``log.debug(...)``, ``log.info(...)``, etc.

Log levels
----------
``DEBUG``
    Detailed, high-frequency events: individual animation frames,
    per-field parameter updates, widget resize events, slider ticks.
    Hidden at default level; enabled with ``--debug`` on the CLI.

``INFO``
    Coarse lifecycle events: application start/stop, tab construction,
    animation start/pause/reset, video file loaded, parameter changed.
    Shown by default.

``WARNING``
    Recoverable unexpected states: type-cast failures, empty frames,
    missing attributes, backend quirks.

``ERROR``
    Failures that degraded the visible output but did not crash the app.

Rotating file policy
--------------------
- Maximum file size : 1 MB  (``maxBytes=1_048_576``)
- Backup count      : 3     (``app.log``, ``app.log.1``, ``app.log.2``, ``app.log.3``)
- Encoding          : UTF-8

The log file path is resolved relative to this file's location so it
works regardless of the working directory the user launches the app from.
"""

import logging
import logging.handlers
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

# This file lives at:   <project_root>/src/gui_Qt/utils/logger.py
# We need to reach:     <project_root>/logs/app.log
#
#   Path(__file__)                      → .../utils/logger.py
#   .parents[0]  (utils/)
#   .parents[1]  (gui_Qt/)
#   .parents[2]  (src/)
#   .parents[3]  (<project_root>/)

_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
_LOG_DIR: Path = _PROJECT_ROOT / "logs"
_LOG_FILE: Path = _LOG_DIR / "app.log"

# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------

_LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def setup_logging(debug: bool = False) -> None:
    """Configure the root logger with terminal and file handlers.

    Safe to call multiple times — subsequent calls are no-ops so that
    re-importing this module in tests or interactive sessions does not
    double-up the handlers.

    Args:
        debug: When ``True`` the root logger level is set to
            ``logging.DEBUG``; otherwise ``logging.INFO``.

    Side effects:
        - Creates ``<project_root>/logs/`` if it does not already exist.
        - Attaches a ``StreamHandler`` (stderr) and a
          ``RotatingFileHandler`` to the root logger.
        - Both handlers use the shared ``_LOG_FORMAT`` / ``_DATE_FORMAT``
          formatter.
    """
    root = logging.getLogger()

    # Guard: skip only when *our* RotatingFileHandler is already attached,
    # which means setup_logging() was already called in this process.
    # A bare StreamHandler left behind by logging.basicConfig() does NOT
    # count — we strip those stale handlers and replace them with ours so
    # the format and level are consistent across restarts / re-imports.
    already_configured = any(
        isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers
    )
    if already_configured:
        return

    # Remove any handlers that may have been attached by a previous
    # basicConfig() call or an earlier import of this module that failed
    # before it could install the RotatingFileHandler.
    for stale in list(root.handlers):
        root.removeHandler(stale)
        stale.close()

    level = logging.DEBUG if debug else logging.INFO
    root.setLevel(level)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # ------------------------------------------------------------------
    # 1. Terminal handler — always shows INFO+ (or DEBUG+ in debug mode)
    # ------------------------------------------------------------------
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # ------------------------------------------------------------------
    # 2. Rotating file handler
    # ------------------------------------------------------------------
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=_LOG_FILE,
            maxBytes=1_048_576,  # 1 MB per file
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # always capture everything in the file
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError as exc:
        # If we cannot create the log file (e.g. permission error on a
        # read-only filesystem) fall back gracefully to terminal-only
        # logging and warn the user.
        root.warning(
            "Could not open log file %s (%s). Logging to terminal only.",
            _LOG_FILE,
            exc,
        )

    root.debug(
        "Logging initialised — file: %s | level: %s",
        _LOG_FILE,
        logging.getLevelName(level),
    )


def get_log_path() -> Path:
    """Return the absolute path of the active log file.

    Useful for displaying the log location in an About dialog or
    status bar.

    Returns:
        Absolute ``Path`` to ``<project_root>/logs/app.log``.
    """
    return _LOG_FILE
