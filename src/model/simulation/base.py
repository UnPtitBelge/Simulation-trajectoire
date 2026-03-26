"""Base classes for all simulation plot backends.

Plot: abstract base owning a widget + animation timer.
  - _compute() runs in a background QThread (no UI blocking).
  - _draw_initial() and _draw() always execute in the main thread via
    Qt's queued signal mechanism.
Plot3dBase: adds OpenGL GLViewWidget + shared 3D scene setup.
"""

import logging
from typing import Any

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import QObject, QThread, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QSizePolicy

from src.model.params.physics_constants import LARGE_BALL_RADIUS, SMALL_BALL_RADIUS
from src.util.theme import RGB_CENTER_BALL

log = logging.getLogger(__name__)


class _ComputeWorker(QObject):
    """Runs Plot._compute() in a QThread and signals completion.

    Lives in a worker thread (moveToThread). Emits finished/failed
    back to the main thread via Qt's automatic queued connection.
    """

    finished = Signal()
    failed = Signal(str)

    def __init__(self, plot: "Plot"):
        super().__init__()
        self._plot = plot

    @Slot()
    def run(self) -> None:
        try:
            self._plot._compute()
            self.finished.emit()
        except Exception as e:
            self.failed.emit(str(e))


class Plot(QObject):
    """Abstract simulation renderer: widget + animation lifecycle."""

    frame_updated = Signal(int)
    setup_done = Signal()
    anim_finished = Signal()  # emitted when the last frame is drawn

    def __init__(self, params: Any = None, frame_ms: int = 16):
        super().__init__()
        self.widget: Any = None
        self.params = params
        self._frame_ms = frame_ms
        self._speed: float = 1.0
        self.timer = QTimer()
        self.timer.setInterval(frame_ms)
        self.timer.timeout.connect(self._tick)
        self.frame = 0
        self._n_frames = 0
        self._ready = False
        self._computing = False
        self._start_after_setup = False
        self._pending_params: Any = None
        self._thread: QThread | None = None
        self._worker: _ComputeWorker | None = None
        self._frame_acc: float = 0.0
        self._cache: dict = {}
        self._last_params_hash = None

    # --- abstract interface ---

    def _compute(self) -> None:
        raise NotImplementedError

    def _draw(self, i: int) -> None:
        raise NotImplementedError

    def format_metrics(self) -> str:
        """Return a formatted string of post-computation metrics. Subclasses override."""
        return ""

    def get_metrics_schema(self) -> list[dict]:
        """Static description of real-time metrics for this simulation.

        Each entry: {key, label, unit, fmt, color}
        Subclasses override to drive the MetricsPanel.
        """
        return []

    def get_frame_metrics(self, i: int) -> dict[str, float]:
        """Values for the metrics at frame i.  Keys must match get_metrics_schema()."""
        return {}

    def get_chart_data(self) -> dict | None:
        """Return precomputed r(t) data for the libre-mode chart panel.

        Keys: 't' (time array s), 'r' (radius array m), 'label' (y-axis label).
        Returns None if this simulation type has no chart.
        """
        return None

    def get_presets(self) -> dict[str, Any]:
        """Return the PRESETS dict for the current params type (Loi de Déméter)."""
        if self.params is None:
            return {}
        return type(self.params).PRESETS

    def _draw_initial(self) -> None:
        if self._n_frames > 0:
            self._draw(0)
            self.frame_updated.emit(0)

    def _post_scene_rebuild(self) -> None:
        """Called after _draw_initial completes. Plot3dBase overrides to restore markers."""

    # --- cache helpers ---

    def _get_params_hash(self):
        if not self.params:
            return None
        return hash(tuple(vars(self.params).values()))

    def _get_cache_data(self) -> dict:
        """Return the computed state to cache. Subclasses override."""
        return {}

    def _set_cache_data(self, data: dict) -> None:
        """Restore computed state from cache. Subclasses override."""

    def _check_cache(self) -> bool:
        current_hash = self._get_params_hash()
        if current_hash == self._last_params_hash and self._cache:
            cached_data = self._cache.get(current_hash)
            if cached_data:
                self._set_cache_data(cached_data)
                return True
        return False

    def _store_cache(self) -> None:
        current_hash = self._get_params_hash()
        if not current_hash:
            return
        data = self._get_cache_data()
        if data:
            self._cache[current_hash] = data
            self._last_params_hash = current_hash

    # --- public API ---

    def setup(self) -> None:
        """Start the computation pipeline.

        Cache hit  → immediate: _draw_initial() then optionally start timer.
        Cache miss → async: spawns _ComputeWorker in QThread; _on_compute_done()
                    is called from the main thread when the worker finishes.
        """
        self._ready = False

        try:
            if self._check_cache():
                self.frame = 0
                self._draw_initial()
                self._post_scene_rebuild()
                self._ready = True
                self.setup_done.emit()
                if self._start_after_setup:
                    self._start_after_setup = False
                    self.timer.start()
                return
        except Exception as e:
            log.error("%s._draw_initial (cache) failed: %s", type(self).__name__, e)
            return

        if self._computing:
            # Thread is already running — result will arrive via _on_compute_done.
            return

        self._computing = True
        self._thread = QThread()
        self._worker = _ComputeWorker(self)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_compute_done)
        self._worker.failed.connect(self._on_compute_failed)
        # Stop thread when worker signals completion
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        # Clean up references once the thread's event loop exits
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def set_speed(self, factor: float) -> None:
        """Adjust playback speed multiplier (0.25–4.0).

        Speed is implemented via frame accumulation, not timer frequency, so
        it works even when the render time exceeds the base timer interval.
        At speed < 1 the accumulator delays frame advances; at speed > 1 it
        advances several physics frames per tick.
        """
        self._speed = max(0.25, min(4.0, factor))

    def start(self) -> None:
        """Start the animation, computing in the background if needed."""
        if self.params:
            self._frame_ms = int(self.params.frame_ms)
        self.timer.setInterval(self._frame_ms)

        if self._ready:
            self.timer.start()
        else:
            # Ask setup() to start the timer once computation is done.
            self._start_after_setup = True
            self.setup()

    def stop(self) -> None:
        self.timer.stop()

    def reset(self) -> None:
        self.stop()
        self.frame = 0
        self._frame_acc = 0.0
        if self._ready:
            self._draw_initial()
            self._post_scene_rebuild()

    def restart(self) -> None:
        """Force recomputation with current params and auto-start when done.

        Use this after mutating params in-place (e.g. applying an extreme case).
        Unlike setup(), guarantees the animation starts as soon as the worker
        thread finishes — the caller does not need to press Play manually.
        """
        self.stop()
        self.frame = 0
        self._frame_acc = 0.0
        self._start_after_setup = True
        self.setup()

    def apply_preset(self, index: int) -> None:
        """Switch to a preset.

        If a background computation is in progress, the new params are queued
        in _pending_params and applied once the current computation finishes.
        """
        if self.params is None:
            return
        cls = type(self.params)
        keys = list(cls.PRESETS.keys())
        if not (0 <= index < len(keys)):
            return

        self.timer.stop()
        new_params = cls.from_preset(keys[index])

        if self._computing:
            # Don't touch self.params while the thread is reading it.
            self._pending_params = new_params
            return

        self.params = new_params
        self._start_after_setup = False
        self.setup()

    def apply_preset(self, index: int) -> None:
        """Switch to a preset."""
        if self.params is None:
            return
        cls = type(self.params)
        presets = cls.PRESETS
        keys = list(presets.keys())
        if not (0 <= index < len(keys)):
            return

        self.timer.stop()
        new_params = cls.from_preset(keys[index])

        if self._computing:
            self._pending_params = new_params
            return

        self.params = new_params
        self._start_after_setup = False
        self.setup()

    # --- internal slots (always called in main thread via queued signals) ---

    @Slot()
    def _on_compute_done(self) -> None:
        """Called in the main thread after _compute() succeeds."""
        try:
            self._store_cache()
            self.frame = 0
            self._draw_initial()
            self._post_scene_rebuild()
            self._ready = True
            self.setup_done.emit()
        except Exception as e:
            log.error("%s._on_compute_done failed: %s", type(self).__name__, e)
            self._ready = False
            self._start_after_setup = False
            self._pending_params = None
            return

        # Handle a preset that was requested while we were computing.
        if self._pending_params is not None:
            self.params = self._pending_params
            self._pending_params = None
            self._start_after_setup = True
            self.setup()
            return

        if self._start_after_setup:
            self._start_after_setup = False
            self.timer.start()

    @Slot(str)
    def _on_compute_failed(self, msg: str) -> None:
        """Called in the main thread after _compute() raises."""
        log.error("%s._compute failed: %s", type(self).__name__, msg)
        self._ready = False
        self._computing = False
        self._start_after_setup = False
        self._pending_params = None

    @Slot()
    def _cleanup_thread(self) -> None:
        """Release thread and worker references after the thread exits."""
        self._computing = False
        self._thread = None
        self._worker = None

    def _tick(self) -> None:
        if not self._ready:
            # Computing in background — skip this tick.
            return

        # Accumulate fractional frames so any speed (including non-integer
        # multipliers like ×1.5) is applied accurately over time.
        self._frame_acc += self._speed
        while self._frame_acc >= 1.0:
            self._frame_acc -= 1.0
            if self.frame < self._n_frames:
                try:
                    self._draw(self.frame)
                    self.frame_updated.emit(self.frame)
                except Exception as e:
                    log.error("%s._draw(%d): %s", type(self).__name__, self.frame, e)
                self.frame += 1
            else:
                self._frame_acc = 0.0
                self.timer.stop()
                self.anim_finished.emit()
                return


_RGB_MARKER = (0.18, 0.82, 0.28, 1.0)  # vert vif — distinct du bleu/rouge/orange


class Plot3dBase(Plot):
    """3D simulation base with an OpenGL GLViewWidget."""

    def __init__(self, params=None, frame_ms=16):
        super().__init__(params, frame_ms)
        self.widget = gl.GLViewWidget()
        self.widget.setCameraPosition(distance=2.5, elevation=35, azimuth=45)
        self.widget.setBackgroundColor("k")
        self.widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Marqueurs statiques (repères visuels) — (position, couleur)
        self._markers: list[tuple[np.ndarray, tuple]] = []
        self._marker_items: list[gl.GLScatterPlotItem] = []

    def _setup_3d_scene(
        self,
        mesh: gl.GLMeshItem,
        particle_color: tuple,
        trail_color: tuple,
        center_z: float = 0.0,
    ) -> tuple[gl.GLScatterPlotItem, gl.GLLinePlotItem]:
        """Clear the GL widget, then add mesh, grid, particle, trail and center ball.

        Eliminates the duplicated setup sequence in PlotCone and PlotMembrane.
        Returns (particle, trail) for use in _draw().
        """
        for item in list(self.widget.items):
            self.widget.removeItem(item)
        self.widget.addItem(mesh)

        grid = gl.GLGridItem()
        grid.setSize(2, 2)
        grid.setSpacing(0.1, 0.1)
        self.widget.addItem(grid)

        particle = gl.GLScatterPlotItem(
            pos=np.array([[0.0, 0.0, 0.0]]),
            size=SMALL_BALL_RADIUS * 2,
            color=particle_color,
            pxMode=False,
        )
        self.widget.addItem(particle)

        trail = gl.GLLinePlotItem(
            pos=np.array([[0.0, 0.0, 0.0]]),
            color=trail_color,
            width=2,
            antialias=True,
        )
        self.widget.addItem(trail)

        center_ball = gl.GLScatterPlotItem(
            pos=np.array([[0.0, 0.0, center_z]]),
            size=LARGE_BALL_RADIUS * 2,
            color=RGB_CENTER_BALL,
            pxMode=False,
        )
        self.widget.addItem(center_ball)

        return particle, trail

    def add_marker(self, pos: np.ndarray, color: tuple = _RGB_MARKER) -> None:
        """Ajoute une bille statique (repère) à la position pos (coordonnées 3D monde)."""
        self._markers.append((pos.copy(), color))
        item = gl.GLScatterPlotItem(
            pos=pos.reshape(1, 3),
            size=SMALL_BALL_RADIUS * 2.5,
            color=color,
            pxMode=False,
        )
        self._marker_items.append(item)
        self.widget.addItem(item)

    def clear_markers(self) -> None:
        """Supprime tous les repères de la scène."""
        for item in self._marker_items:
            self.widget.removeItem(item)
        self._marker_items.clear()
        self._markers.clear()

    def get_current_3d_pos(self) -> np.ndarray | None:
        """Retourne la position 3D actuelle de la particule, ou None si pas prêt."""
        traj = getattr(self, "traj", None)
        if traj and 0 <= self.frame < len(traj):
            return np.array(traj[self.frame])
        return None

    def _post_scene_rebuild(self) -> None:
        """Recrée les GL items des repères après que _setup_3d_scene a vidé la scène."""
        self._marker_items.clear()
        for pos, color in self._markers:
            item = gl.GLScatterPlotItem(
                pos=pos.reshape(1, 3),
                size=SMALL_BALL_RADIUS * 2.5,
                color=color,
                pxMode=False,
            )
            self._marker_items.append(item)
            self.widget.addItem(item)

    def get_chart_data(self) -> dict | None:
        """r(t) chart data for 3D simulations that store trajectory as self.traj."""
        traj = getattr(self, "traj", None)
        if not traj:
            return None
        traj_np = np.array(traj)
        r_arr = np.sqrt(traj_np[:, 0] ** 2 + traj_np[:, 1] ** 2)
        t_arr = np.arange(len(traj)) * self.params.dt
        return {"t": t_arr, "r": r_arr, "label": "r (m)"}
