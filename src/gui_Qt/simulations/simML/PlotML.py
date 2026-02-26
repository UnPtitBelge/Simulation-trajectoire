from typing import Optional

import numpy as np
import pyqtgraph as pg
from simulations.Plot import Plot
from sklearn.linear_model import LinearRegression
from utils.params import SimulationMLParams


class PlotML(Plot):
    """
    Lightweight plot wrapper for the ML regression demo.

    Inherits common animation and parameter handling from `Plot`. This class
    implements the ML-specific preparation and per-frame rendering hooks and
    provides an update_params override to support retraining and interactive
    visualization parameters.
    """

    def __init__(self, parent=None):
        # Initialize base plot with UI-driven default frame interval
        self.sim_params: SimulationMLParams = SimulationMLParams()
        super().__init__(
            self.sim_params, frame_ms=int(getattr(self.sim_params, "frame_ms", 100))
        )

        # Create the plotting area
        self.widget = pg.PlotWidget(title="ML Regression Trajectory")
        self.widget.setBackground("w")
        self.widget.showGrid(x=True, y=True, alpha=0.3)
        try:
            self.widget.getViewBox().setAspectLocked(lock=True, ratio=1.0)
        except Exception:
            pass

        # Plot items
        self.true_curve = self.widget.plot(
            [], [], pen=pg.mkPen(color=(50, 150, 50), width=2), name="True"
        )
        self.pred_curve = self.widget.plot(
            [],
            [],
            pen=pg.mkPen(color=(200, 50, 50), width=2, style=pg.QtCore.Qt.DashLine),
            name="Predicted",
        )
        self.current_point = pg.ScatterPlotItem(
            size=self.sim_params.marker_size,
            brush=pg.mkBrush(30, 30, 220),
            pen=pg.mkPen("k"),
        )
        self.widget.addItem(self.current_point)

        # Internal state: model/data storage
        self._model: Optional[object] = None
        self._train_ref = []
        self._true_traj = np.zeros((0, 2))
        self._pred_traj = np.zeros((0, 2))

        # Ensure frame count is tracked by base class when we prepare
        self._n_points = 0

        # Build and train the initial model and prepare simulation data
        self._build_and_train_model()
        # Prepare initial visuals (base.setup_animation will call our _prepare_simulation)
        try:
            self.setup_animation()
        except Exception:
            pass

    def _build_and_train_model(self):
        """Create the toy dataset and fit the selected model type.

        The implementation supports a LinearRegression fallback. If sklearn is
        not available, the predictor will be a no-op identity copier.
        """
        # Toy dataset (same shape as the original demo)
        data = [
            {
                "initial": (1.0, 0.0, 0.0, 1.2),
                "trajectory": [
                    (0.99, 0.06),
                    (0.97, 0.12),
                    (0.94, 0.18),
                    (0.90, 0.24),
                    (0.85, 0.30),
                    (0.79, 0.35),
                    (0.72, 0.40),
                    (0.64, 0.44),
                    (0.55, 0.48),
                    (0.45, 0.51),
                    (0.35, 0.53),
                    (0.24, 0.54),
                    (0.13, 0.54),
                    (0.02, 0.53),
                    (-0.09, 0.51),
                    (-0.20, 0.48),
                    (-0.30, 0.44),
                    (-0.39, 0.39),
                    (-0.47, 0.33),
                    (-0.54, 0.26),
                ],
            },
            {
                "initial": (1.5, 0.0, 0.0, 1.0),
                "trajectory": [
                    (1.49, 0.05),
                    (1.47, 0.10),
                    (1.44, 0.15),
                    (1.40, 0.20),
                    (1.35, 0.25),
                    (1.29, 0.29),
                    (1.22, 0.33),
                    (1.14, 0.36),
                    (1.05, 0.39),
                    (0.95, 0.41),
                    (0.85, 0.42),
                    (0.74, 0.43),
                    (0.63, 0.43),
                    (0.52, 0.42),
                    (0.41, 0.40),
                    (0.30, 0.37),
                    (0.20, 0.33),
                    (0.11, 0.28),
                    (0.03, 0.22),
                    (-0.04, 0.15),
                ],
            },
            {
                "initial": (0.8, 0.0, 0.0, 1.4),
                "trajectory": [
                    (0.79, 0.07),
                    (0.76, 0.14),
                    (0.72, 0.21),
                    (0.66, 0.27),
                    (0.59, 0.33),
                    (0.51, 0.38),
                    (0.42, 0.42),
                    (0.32, 0.45),
                    (0.21, 0.47),
                    (0.10, 0.48),
                    (-0.01, 0.48),
                    (-0.12, 0.47),
                    (-0.23, 0.45),
                    (-0.33, 0.42),
                    (-0.42, 0.38),
                    (-0.50, 0.33),
                    (-0.57, 0.27),
                    (-0.63, 0.20),
                    (-0.68, 0.12),
                    (-0.72, 0.04),
                ],
            },
        ]

        # Format dataset for regression
        X = []
        Y = []
        for sample in data:
            X.append(sample["initial"])
            traj = sample["trajectory"]
            flat = [coord for point in traj for coord in point]
            Y.append(flat)
        X = np.array(X, dtype=np.float32)
        Y = np.array(Y, dtype=np.float32)

        # Fit model if available
        if LinearRegression is not None and int(self.sim_params.model_type) == 0:
            try:
                model = LinearRegression()
                model.fit(X, Y)
                self._model = model
            except Exception:
                self._model = None
        else:
            self._model = None

        # Keep the training reference and precompute the default true trajectory
        self._train_ref = data
        self._true_traj = np.array(self._train_ref[0]["trajectory"], dtype=np.float32)
        self._n_points = self._true_traj.shape[0]

    def _predict_for_index(self, idx: int) -> np.ndarray:
        """Return predicted trajectory for the training sample index `idx`.

        Applies optional synthetic noise from sim_params.noise_level.
        """
        if not self._train_ref:
            return np.array([], dtype=np.float32)

        idx = max(0, min(int(idx), len(self._train_ref) - 1))
        initial = np.array([self._train_ref[idx]["initial"]], dtype=np.float32)
        if self._model is not None:
            try:
                pred_flat = self._model.predict(initial)[0]
                pred_traj = np.reshape(pred_flat, (-1, 2)).astype(np.float32)
            except Exception:
                pred_traj = np.array(
                    self._train_ref[idx]["trajectory"], dtype=np.float32
                )
        else:
            pred_traj = np.array(self._train_ref[idx]["trajectory"], dtype=np.float32)

        # Optionally add noise for visualization/debugging
        noise_level = float(getattr(self.sim_params, "noise_level", 0.0))
        if noise_level and noise_level > 0.0:
            pred_traj = pred_traj + np.random.normal(
                scale=noise_level, size=pred_traj.shape
            )

        return np.array(pred_traj, dtype=np.float32)

    def _prepare_simulation(self) -> None:
        """Prepare predicted trajectory and static data for animation.

        This hook is used by the base class `setup_animation()` to recompute the
        necessary arrays from current parameters.
        """
        # Ensure we have the training data available (built by _build_and_train_model)
        if not self._train_ref:
            self._pred_traj = np.zeros((0, 2), dtype=np.float32)
            self._true_traj = np.zeros((0, 2), dtype=np.float32)
            self._n_frames = 0
            return

        # Determine index and compute prediction
        idx = int(getattr(self.sim_params, "test_initial_idx", 0))
        idx = max(0, min(idx, len(self._train_ref) - 1))

        # True trajectory for the selected sample
        self._true_traj = np.array(self._train_ref[idx]["trajectory"], dtype=np.float32)
        # Predicted trajectory
        self._pred_traj = self._predict_for_index(idx)

        # Number of frames is the max of true/pred lengths
        self._n_frames = max(self._true_traj.shape[0], self._pred_traj.shape[0])

    def _update_frame(self, frame_index: int) -> None:
        """Render a single frame by advancing the moving marker."""
        if self._n_frames == 0:
            return

        idx = (
            frame_index % self._pred_traj.shape[0]
            if self._pred_traj.shape[0] > 0
            else 0
        )
        if self._pred_traj.shape[0] > 0:
            x, y = self._pred_traj[idx]
            # Update the marker position
            try:
                self.current_point.setData([x], [y])
            except Exception:
                # On older pyqtgraph versions current_point.setData may accept different args.
                try:
                    self.widget.removeItem(self.current_point)
                except Exception:
                    pass
                self.current_point = pg.ScatterPlotItem(
                    size=int(getattr(self.sim_params, "marker_size", 10)),
                    brush=pg.mkBrush(30, 30, 220),
                    pen=pg.mkPen("k"),
                )
                self.widget.addItem(self.current_point)
                self.current_point.setData([x], [y])

    def _draw_initial_frame(self) -> None:
        """Draw static curves and configure marker size before animation."""
        # Static curves
        try:
            self.true_curve.setData(self._true_traj[:, 0], self._true_traj[:, 1])
            self.pred_curve.setData(self._pred_traj[:, 0], self._pred_traj[:, 1])
        except Exception:
            # If data is empty the calls above may fail silently
            pass

        # Ensure marker has the right size (recreate if necessary)
        try:
            self.current_point.setSize(int(getattr(self.sim_params, "marker_size", 10)))
        except Exception:
            try:
                self.widget.removeItem(self.current_point)
            except Exception:
                pass
            self.current_point = pg.ScatterPlotItem(
                size=int(getattr(self.sim_params, "marker_size", 10)),
                brush=pg.mkBrush(30, 30, 220),
                pen=pg.mkPen("k"),
            )
            self.widget.addItem(self.current_point)

        # Place marker at the first predicted point if available
        if self._pred_traj.shape[0] > 0:
            x0, y0 = self._pred_traj[0]
            self.current_point.setData([x0], [y0])
        else:
            self.current_point.setData([], [])

    # The base class `_on_timer` drives per-frame updates by calling `_update_frame`.
    # We keep `_step` for backward compatibility but forward it to the base hook.
    def _step(self):
        """Compatibility wrapper: forward to the base frame step implementation."""
        # Base class uses current_frame/_n_frames and calls _update_frame internally,
        # so simply delegate to that behavior by invoking the base handler.
        self._on_timer()

    def start_animation(self):
        """Start the animation timer (align interval to current sim_params)."""
        # Use sim_params.frame_ms if present
        try:
            self._frame_ms = int(getattr(self.sim_params, "frame_ms", self._frame_ms))
        except Exception:
            pass
        super().start_animation()

    def stop_animation(self):
        """Stop the animation timer."""
        if self.animation_timer is None:
            return
        self.animation_timer.stop()

    def reset_animation(self):
        """Stop and reset animation to initial state."""
        self.stop_animation()
        self._index = 0
        if self._pred_traj.shape[0] > 0:
            x0, y0 = self._pred_traj[0]
            self.current_point.setData([x0], [y0])
        else:
            self.current_point.setData([], [])

    def update_params(self, **kwargs):
        """
        Apply parameter updates coming from the UI controls.

        This override detects model-type/retrain requests before delegating to
        the base class which writes kwargs into `sim_params`/`params` and calls
        `setup_animation()`. After the base update runs we ensure marker sizing
        and a current prediction are reflected in the view.
        """
        # Detect model-type or retrain flags early so we can retrain before prepare
        need_retrain = False
        if "model_type" in kwargs or "retrain_on_update" in kwargs:
            need_retrain = True

        # If model_type/retrain flags are present and request retrain, apply them to sim_params
        # (we'll rely on base.update_params to call setup_animation/_prepare_simulation)
        if need_retrain:
            # apply preliminary changes to sim_params if available
            if self.sim_params is not None:
                for k in ("model_type", "retrain_on_update"):
                    if k in kwargs and hasattr(self.sim_params, k):
                        try:
                            setattr(
                                self.sim_params,
                                k,
                                type(getattr(self.sim_params, k))(kwargs[k]),
                            )
                        except Exception:
                            try:
                                setattr(self.sim_params, k, kwargs[k])
                            except Exception:
                                pass
            # trigger rebuild if explicitly requested
            try:
                if getattr(self.sim_params, "retrain_on_update", False) or (
                    "model_type" in kwargs
                ):
                    self._build_and_train_model()
            except Exception:
                pass

        # Now let the base class apply incoming parameters and call setup_animation()
        super().update_params(**kwargs)

        # After the base setup, ensure marker sizing and predicted data are visible
        try:
            # update marker size if requested
            if hasattr(self.sim_params, "marker_size"):
                try:
                    self.current_point.setSize(
                        int(getattr(self.sim_params, "marker_size"))
                    )
                except Exception:
                    # recreate marker if setSize is unavailable
                    try:
                        self.widget.removeItem(self.current_point)
                    except Exception:
                        pass
                    self.current_point = pg.ScatterPlotItem(
                        size=int(getattr(self.sim_params, "marker_size")),
                        brush=pg.mkBrush(30, 30, 220),
                        pen=pg.mkPen("k"),
                    )
                    self.widget.addItem(self.current_point)
            # update predicted curve (setup_animation already set pred arrays, but ensure plotted)
            try:
                self.pred_curve.setData(self._pred_traj[:, 0], self._pred_traj[:, 1])
            except Exception:
                pass
        except Exception:
            pass
