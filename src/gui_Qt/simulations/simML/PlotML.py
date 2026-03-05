from typing import Optional

import numpy as np
import pyqtgraph as pg
from simulations.Plot import Plot
from sklearn.linear_model import LinearRegression
from utils.params import SimulationMLParams


class PlotML(Plot):
    """ML regression demo plot.

    Inherits all animation lifecycle (setup, start, stop, reset, timer) from
    Plot. Only the three hooks required by the contract are implemented here:
      - _prepare_simulation : compute true/predicted trajectories
      - _update_frame       : advance the moving marker
      - _draw_initial_frame : draw static curves + place marker at frame 0

    update_params is overridden only to trigger a model retrain when
    model_type changes, before delegating entirely to super().
    """

    def __init__(self):
        sim_params = SimulationMLParams()
        # Pass sim_params to base — it stores it as self.sim_params and wires
        # the timer. No need to assign self.sim_params before super().__init__.
        super().__init__(sim_params, frame_ms=sim_params.frame_ms)

        self.widget = pg.PlotWidget(title="ML Regression Trajectory")
        self.widget.setBackground("w")
        self.widget.showGrid(x=True, y=True, alpha=0.3)
        self.widget.getViewBox().setAspectLocked(lock=True, ratio=1.0)

        # Static curves (data filled by _draw_initial_frame)
        self.true_curve = self.widget.plot(
            [], [], pen=pg.mkPen(color=(50, 150, 50), width=2), name="True"
        )
        self.pred_curve = self.widget.plot(
            [],
            [],
            pen=pg.mkPen(color=(200, 50, 50), width=2, style=pg.QtCore.Qt.DashLine),
            name="Predicted",
        )

        # Moving marker — created once, repositioned via setData() every frame
        self.current_point = pg.ScatterPlotItem(
            size=self.sim_params.marker_size,
            brush=pg.mkBrush(30, 30, 220),
            pen=pg.mkPen("k"),
        )
        self.widget.addItem(self.current_point)

        # Model + data (populated by _build_and_train_model)
        self._model: Optional[object] = None
        self._train_ref: list = []
        self._true_traj = np.zeros((0, 2), dtype=np.float32)
        self._pred_traj = np.zeros((0, 2), dtype=np.float32)

        # Train once — SimWidget calls setup_animation() afterwards
        self._build_and_train_model()

    # ------------------------------------------------------------------ #
    # Model training                                                       #
    # ------------------------------------------------------------------ #

    def _build_and_train_model(self) -> None:
        """Build the toy dataset and fit a LinearRegression model."""
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

        X = np.array([s["initial"] for s in data], dtype=np.float32)
        Y = np.array(
            [[c for pt in s["trajectory"] for c in pt] for s in data],
            dtype=np.float32,
        )

        try:
            self._model = LinearRegression().fit(X, Y)
        except Exception:
            self._model = None

        self._train_ref = data

    # ------------------------------------------------------------------ #
    # Abstract hooks — the only three methods PlotML must implement       #
    # ------------------------------------------------------------------ #

    def _prepare_simulation(self) -> None:
        """Compute true + predicted trajectories for the selected sample."""
        if not self._train_ref:
            self._true_traj = np.zeros((0, 2), dtype=np.float32)
            self._pred_traj = np.zeros((0, 2), dtype=np.float32)
            self._n_frames = 0
            return

        idx = max(
            0, min(int(self.sim_params.test_initial_idx), len(self._train_ref) - 1)
        )
        self._true_traj = np.array(self._train_ref[idx]["trajectory"], dtype=np.float32)
        self._pred_traj = self._predict_for_index(idx)
        self._n_frames = max(self._true_traj.shape[0], self._pred_traj.shape[0])

    def _update_frame(self, frame_index: int) -> None:
        """Advance the marker to position frame_index along the predicted trajectory."""
        if self._pred_traj.shape[0] == 0:
            return
        # Clamp to valid range (pred may be shorter than true)
        idx = min(frame_index, self._pred_traj.shape[0] - 1)
        x, y = self._pred_traj[idx]
        self.current_point.setData([x], [y])

    def _draw_initial_frame(self) -> None:
        """Draw static curves and place the marker at position 0."""
        if self._true_traj.shape[0] > 0:
            self.true_curve.setData(self._true_traj[:, 0], self._true_traj[:, 1])
        if self._pred_traj.shape[0] > 0:
            self.pred_curve.setData(self._pred_traj[:, 0], self._pred_traj[:, 1])
            x0, y0 = self._pred_traj[0]
            self.current_point.setData([x0], [y0], size=self.sim_params.marker_size)
        else:
            self.current_point.setData([], [])

    # ------------------------------------------------------------------ #
    # update_params — only override to trigger retrain when needed        #
    # ------------------------------------------------------------------ #

    def update_params(self, **kwargs) -> None:
        """Retrain the model if model_type changed, then delegate to super().

        super().update_params() writes all kwargs into self.sim_params and
        calls setup_animation() → _prepare_simulation() + _draw_initial_frame().
        There is no need to duplicate any of that logic here.
        """
        if "model_type" in kwargs or kwargs.get("retrain_on_update", False):
            # Apply the two retrain-relevant fields early so _build_and_train_model
            # sees the updated model_type before fitting.
            for key in ("model_type", "retrain_on_update"):
                if key in kwargs and hasattr(self.sim_params, key):
                    setattr(
                        self.sim_params,
                        key,
                        type(getattr(self.sim_params, key))(kwargs[key]),
                    )
            self._build_and_train_model()

        # Delegate everything else (param writing + setup_animation) to the base
        super().update_params(**kwargs)

    # ------------------------------------------------------------------ #
    # Private helper                                                       #
    # ------------------------------------------------------------------ #

    def _predict_for_index(self, idx: int) -> np.ndarray:
        """Return the predicted trajectory for training sample `idx`."""
        idx = max(0, min(idx, len(self._train_ref) - 1))
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

        noise = float(self.sim_params.noise_level)
        if noise > 0.0:
            pred_traj = pred_traj + np.random.normal(scale=noise, size=pred_traj.shape)

        return pred_traj.astype(np.float32)
