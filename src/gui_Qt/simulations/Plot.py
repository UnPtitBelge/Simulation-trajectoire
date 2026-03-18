import logging
from abc import ABC, abstractmethod
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal
from utils.params import (
    SimulationConeParams,
    SimulationMCUParams,
    SimulationMembraneParams,
    SimulationMLParams,
)

log = logging.getLogger(__name__)


class Plot(QObject):
    """Abstract base class for simulation plot wrappers.

    Subclasses must set self.widget in their __init__ before calling any
    animation method, and must implement the three abstract hooks below.

    Attributes:
        widget:          The pyqtgraph / OpenGL widget used for rendering.
        sim_params:      Simulation parameter dataclass.
        animation_timer: QTimer that fires _on_timer every frame_ms ms.
        current_frame:   Index of the frame rendered on the next tick.
        _frame_ms:       Current timer interval in milliseconds.
        _n_frames:       Total frames produced by _prepare_simulation.
        _prepared:       True once setup_animation has run successfully.
    """
    
    frame_updated = Signal(int)

    def __init__(
        self,
        sim_params: (
            SimulationMCUParams
            | SimulationConeParams
            | SimulationMembraneParams
            | SimulationMLParams
            | None
        ) = None,
        frame_ms: int = 100,
    ) -> None:
        super().__init__()
        self.widget: Any = None
        self.sim_params = sim_params

        self.animation_timer = QTimer()
        self._frame_ms = int(frame_ms)
        self.animation_timer.setInterval(self._frame_ms)
        self.animation_timer.timeout.connect(self._on_timer)

        self.current_frame: int = 0
        self._n_frames: int = 0
        self._prepared: bool = False

        log.debug(
            "%s.__init__ — frame_ms=%d sim_params=%s",
            type(self).__name__,
            self._frame_ms,
            type(sim_params).__name__ if sim_params is not None else "None",
        )

    # -----------------------------------------------------------------------
    # Abstract hooks
    # -----------------------------------------------------------------------

    @abstractmethod
    def _prepare_simulation(self) -> None:
        """Compute all simulation outputs and set self._n_frames."""
        raise NotImplementedError

    @abstractmethod
    def _update_frame(self, frame_index: int) -> None:
        """Render visual elements for frame_index."""
        raise NotImplementedError

    def _draw_initial_frame(self) -> None:
        """Render frame 0 to initialise the display.

        The base implementation simply calls ``_update_frame(0)`` when at
        least one frame is available.  It does **not** draw any static
        geometry — that responsibility is delegated to subclasses.
        Subclasses that need persistent background elements should override
        this method, draw those elements first, then call
        ``_update_frame(0)`` explicitly.
        """
        if self._n_frames > 0:
            try:
                self._update_frame(0)
                self.frame_updated.emit(0)
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Animation lifecycle
    # -----------------------------------------------------------------------

    def setup_animation(self) -> None:
        """Prepare simulation data and draw the initial frame.

        Sets ``_prepared`` to True only if ``_prepare_simulation`` completes
        without raising an exception.  On failure the error is logged and the
        method returns early, leaving ``_prepared`` as False.
        """
        log.debug("%s.setup_animation — preparing simulation", type(self).__name__)
        self._prepared = False
        try:
            self._prepare_simulation()
        except Exception as exc:
            log.error(
                "%s.setup_animation — _prepare_simulation failed: %s",
                type(self).__name__,
                exc,
            )
            return
        self._prepared = True
        self.current_frame = 0
        log.info(
            "%s.setup_animation — ready | n_frames=%d",
            type(self).__name__,
            self._n_frames,
        )
        self._draw_initial_frame()

    def start_animation(self) -> None:
        """Start or resume the animation timer."""
        if self.sim_params is not None and hasattr(self.sim_params, "frame_ms"):
            try:
                self._frame_ms = int(getattr(self.sim_params, "frame_ms"))
            except Exception:
                log.warning(
                    "%s.start_animation — could not read frame_ms from sim_params",
                    type(self).__name__,
                )
        self.animation_timer.setInterval(max(1, int(self._frame_ms)))
        self.animation_timer.start()
        log.info(
            "%s.start_animation — timer started | frame_ms=%d current_frame=%d",
            type(self).__name__,
            self._frame_ms,
            self.current_frame,
        )

    def stop_animation(self) -> None:
        """Stop the animation timer without resetting the frame counter."""
        self.animation_timer.stop()
        log.info(
            "%s.stop_animation — timer stopped | current_frame=%d",
            type(self).__name__,
            self.current_frame,
        )

    def reset_animation(self) -> None:
        """Stop the timer, rewind to frame 0, and redraw the initial frame."""
        self.stop_animation()
        self.current_frame = 0
        log.info("%s.reset_animation — rewound to frame 0", type(self).__name__)
        self._draw_initial_frame()

    # -----------------------------------------------------------------------
    # Timer callback
    # -----------------------------------------------------------------------

    def _on_timer(self) -> None:
        """Advance the animation by one frame."""
        if not self._prepared:
            log.warning(
                "%s._on_timer — data not prepared; running setup_animation as fallback",
                type(self).__name__,
            )
            try:
                self.setup_animation()
            except Exception as exc:
                log.error(
                    "%s._on_timer — fallback setup_animation failed: %s",
                    type(self).__name__,
                    exc,
                )
                return

        if self._n_frames <= 0:
            log.warning(
                "%s._on_timer — no frames available; stopping timer",
                type(self).__name__,
            )
            self.animation_timer.stop()
            return

        if self.current_frame < self._n_frames:
            if self.current_frame % 100 == 0:
                log.debug(
                    "%s._on_timer — rendering frame %d / %d",
                    type(self).__name__,
                    self.current_frame,
                    self._n_frames,
                )
            try:
                self._update_frame(self.current_frame)
                self.frame_updated.emit(self.current_frame)
            except Exception as exc:
                log.error(
                    "%s._on_timer — _update_frame(%d) raised: %s",
                    type(self).__name__,
                    self.current_frame,
                    exc,
                )
            self.current_frame += 1
        else:
            log.info(
                "%s._on_timer — animation complete (%d frames)",
                type(self).__name__,
                self._n_frames,
            )
            self.animation_timer.stop()

    # -----------------------------------------------------------------------
    # Parameter update
    # -----------------------------------------------------------------------

    def update_params(self, **kwargs) -> None:
        """Write new parameter values and unconditionally recompute the simulation.

        Applies each kwarg to self.sim_params when the attribute exists, casting
        to the original field type so that integer fields stay integers.
        Calls setup_animation once if at least one known field was present in kwargs.

        ``stop_animation()`` is called only when at least one recognised
        parameter key is present in *kwargs* and a recompute is actually
        needed — it is **not** called unconditionally at the top of the method.

        The previous design compared old vs new values to detect changes, but
        ParamsController writes values directly to sim_params before calling this
        method, so the comparison always saw identical values and setup_animation
        was never triggered.  The fix is to skip that comparison entirely: if the
        caller passed a key that belongs to sim_params, we trust that a recompute
        is warranted.

        Subclasses that need extra logic should override this and call
        super().update_params(**kwargs) at the end.
        """
        if not kwargs:
            return

        log.debug(
            "%s.update_params — incoming keys: %s",
            type(self).__name__,
            list(kwargs.keys()),
        )

        need_prepare = False

        if self.sim_params is not None:
            for k, v in kwargs.items():
                if not hasattr(self.sim_params, k):
                    continue
                need_prepare = True
                break

        if need_prepare:
            self.stop_animation()

        need_prepare = False

        if self.sim_params is not None:
            for k, v in kwargs.items():
                if not hasattr(self.sim_params, k):
                    continue
                # Cast to the original field type so int fields stay int.
                orig = getattr(self.sim_params, k)
                if orig is not None and not isinstance(orig, bool):
                    try:
                        v = type(orig)(v)
                    except Exception:
                        pass
                elif isinstance(orig, bool):
                    v = bool(v)
                setattr(self.sim_params, k, v)
                log.info(
                    "%s.update_params — sim_params.%s = %r",
                    type(self).__name__,
                    k,
                    v,
                )
                need_prepare = True

        if need_prepare:
            log.debug(
                "%s.update_params — triggering setup_animation",
                type(self).__name__,
            )
            try:
                self.setup_animation()
            except Exception as exc:
                log.error(
                    "%s.update_params — setup_animation failed: %s",
                    type(self).__name__,
                    exc,
                )
