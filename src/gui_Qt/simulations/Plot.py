from abc import ABC, abstractmethod
from typing import Any

from utils.params import (
    PlotParams,
    Simulation2dParams,
    Simulation3dParams,
    SimulationMLParams,
)

from PySide6.QtCore import QTimer


class Plot(ABC):
    """
    Abstract base class for simulation plot wrappers.

    Subclasses must initialize `self.widget` (a QWidget-like object) and may
    optionally provide `self.params` and/or `self.sim_params` dataclass-like
    objects used to hold plot/simulation parameters.

    The base class manages a QTimer (`self.animation_timer`), a simple frame
    index counter and a small parameter-update helper.
    """

    def __init__(
        self,
        sim_params: Simulation2dParams
        | Simulation3dParams
        | SimulationMLParams
        | None = None,
        params: PlotParams | None = None,
        frame_ms: int = 100,
    ) -> None:
        """
        Create the base plot controller.

        Parameters
        ----------
        frame_ms:
            Default frame interval in milliseconds used by the animation timer.
            Subclasses may override by providing a `frame_ms` field in their
            `sim_params` dataclass; `update_params` will keep the timer in sync.
        """
        # Public attributes subclasses are expected to set or override:
        self.widget: Any = None  # QWidget-like plotting widget (set by subclass)
        self.params = params
        self.sim_params = sim_params

        # Animation control
        self.animation_timer = QTimer()
        self._frame_ms = int(frame_ms)
        self.animation_timer.setInterval(self._frame_ms)
        self.animation_timer.timeout.connect(self._on_timer)
        self.current_frame = 0
        self._n_frames = 0

        # Internal flags
        self._prepared = False  # True when simulation data is prepared

    # ---- Abstract methods subclasses must implement ----
    @abstractmethod
    def _prepare_simulation(self) -> None:
        """Produce or recompute simulation/model outputs.

        Subclasses should fill any attributes needed by `_update_frame` such as
        trajectory arrays (xs, ys, zs, etc.) and set `self._n_frames`.
        Called by `setup_animation()` and when parameters change and require a
        recomputation.
        """
        raise NotImplementedError

    @abstractmethod
    def _update_frame(self, frame_index: int) -> None:
        """Render a single frame at `frame_index`.

        This method is the per-frame rendering hook invoked from the timer.
        It should update the visual elements on `self.widget` accordingly.
        """
        raise NotImplementedError

    def _draw_initial_frame(self) -> None:
        """Draw static elements and the first frame.

        Subclasses may override to draw static background items and place the
        first animated element. The default implementation simply calls
        `_update_frame(0)` if there is at least one frame.
        """
        if self._n_frames > 0:
            try:
                self._update_frame(0)
            except Exception:
                # Subclasses handle their own drawing errors.
                pass

    # ---- Animation lifecycle ----
    def setup_animation(self) -> None:
        """Prepare and initialize the animation.

        This triggers recomputation of simulation outputs and draws the
        initial static elements and first frame. It does not start the timer.
        """
        # Prepare simulation/model results using current parameters
        self._prepare_simulation()
        self._prepared = True

        # Reset frame counters and draw initial visuals
        self.current_frame = 0
        # _n_frames should be set by _prepare_simulation()
        if getattr(self, "_n_frames", 0) is None:
            self._n_frames = 0
        self._draw_initial_frame()

    def start_animation(self) -> None:
        """Start or resume the animation timer.

        The timer interval is aligned with `self.sim_params.frame_ms` if present,
        otherwise the value passed to the constructor is used.
        """
        # Keep timer interval in sync with sim_params if available
        if self.sim_params is not None and hasattr(self.sim_params, "frame_ms"):
            try:
                self._frame_ms = int(getattr(self.sim_params, "frame_ms"))
            except Exception:
                pass
        self.animation_timer.setInterval(max(1, int(self._frame_ms)))
        self.animation_timer.start()

    def stop_animation(self) -> None:
        """Stop the animation timer."""
        self.animation_timer.stop()

    def reset_animation(self) -> None:
        """Reset the animation to its initial state and draw the first frame."""
        self.stop_animation()
        self.current_frame = 0
        # attempt to draw initial frame again
        self._draw_initial_frame()

    # ---- Timer callback ----
    def _on_timer(self) -> None:
        """Internal timer callback advancing frames and calling `_update_frame`."""
        if not self._prepared:
            # Guard: ensure simulation data prepared
            try:
                self.setup_animation()
            except Exception:
                return

        if self._n_frames <= 0:
            # nothing to animate
            self.animation_timer.stop()
            return

        if self.current_frame < self._n_frames:
            try:
                self._update_frame(self.current_frame)
            except Exception:
                # swallow per-frame exceptions to keep UI responsive;
                # subclasses may log or rethrow if necessary
                pass
            self.current_frame += 1
        else:
            # end of animation
            self.animation_timer.stop()

    # ---- Parameter handling helper ----
    def update_params(self, **kwargs) -> None:
        """Generic parameter update routine.

        Writes incoming keyword values to `self.sim_params` and `self.params`
        if those attributes exist. If any parameter changed that requires a
        recompute, `_prepare_simulation()` is called and visuals are refreshed.

        Subclass-specific more advanced behavior can be implemented by
        overriding this method and calling `super().update_params(...)`.
        """
        if not kwargs:
            return

        need_prepare = False

        # Helper to set attribute if present and note change
        def _apply_to(target: Any, key: str, value: Any) -> bool:
            if target is None:
                return False
            if hasattr(target, key):
                try:
                    orig = getattr(target, key)
                    # attempt reasonable cast to orig type if possible
                    if orig is not None and not isinstance(orig, bool):
                        cast_type = type(orig)
                        try:
                            new_val = cast_type(value)
                        except Exception:
                            new_val = value
                    else:
                        # for booleans or None, coerce directly
                        new_val = bool(value) if isinstance(orig, bool) else value
                    if new_val != orig:
                        setattr(target, key, new_val)
                        return True
                except Exception:
                    # fallback: try setting raw value
                    try:
                        setattr(target, key, value)
                        return True
                    except Exception:
                        return False
            return False

        # Apply updates to simulation params first (they usually affect outputs)
        if self.sim_params is not None:
            for k, v in kwargs.items():
                changed = _apply_to(self.sim_params, k, v)
                if changed:
                    need_prepare = True

        # Apply updates to plot-level params
        if self.params is not None:
            for k, v in kwargs.items():
                changed = _apply_to(self.params, k, v)
                if changed:
                    # Some plot params may only affect visuals, still request redraw.
                    need_prepare = True

        # If anything changed that requires recompute/redraw do it now
        if need_prepare:
            try:
                # re-run preparation and redraw initial frame
                self.setup_animation()
            except Exception:
                # silently ignore errors to avoid blocking UI; subclasses can log
                pass

    # ---- Convenience utilities ----
    def set_frame_interval(self, ms: int) -> None:
        """Set the animation timer interval (ms)."""
        try:
            self._frame_ms = int(ms)
            self.animation_timer.setInterval(max(1, self._frame_ms))
        except Exception:
            pass

    # Subclasses may expose additional public helpers as needed.
