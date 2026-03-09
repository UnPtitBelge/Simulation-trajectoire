"""ML regression demo plot."""

from typing import Optional
import csv
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from simulations.Plot import Plot
from sklearn.linear_model import LinearRegression
from utils.params import SimulationMLParams
from utils.stylesheet import (
    CLR_PLOT_BG,
    CLR_PLOT_GRID,
    CLR_PLOT_MARKER,
    CLR_PLOT_PRED,
    CLR_PLOT_TRUE,
)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def estimate_mass_center(grouped_rows):
    """Estime le centre de masse à partir des trajectoires groupées."""
    all_x = []
    all_y = []

    for rows in grouped_rows.values():
        for point in rows:
            all_x.append(point["x"])
            all_y.append(point["y"])

    if not all_x or not all_y:
        return 0.0, 0.0

    return float(np.median(all_x)), float(np.median(all_y))


def parse_tracking_csv(csv_path, center_mode="auto"):
    """Parse le fichier CSV de tracking et retourne les données formatées."""
    grouped_rows = {}

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            exp_id = clean_row["expID"]

            if exp_id not in grouped_rows:
                grouped_rows[exp_id] = []

            grouped_rows[exp_id].append(
                {
                    "temps": float(clean_row["temps"]),
                    "x": float(clean_row["x"]),
                    "y": float(clean_row["y"]),
                    "speedX": float(clean_row["speedX"]),
                    "speedY": float(clean_row["speedY"]),
                }
            )

    if center_mode == "auto":
        center_x, center_y = estimate_mass_center(grouped_rows)
    elif center_mode is None:
        center_x, center_y = 0.0, 0.0
    else:
        center_x, center_y = center_mode

    parsed_data = []
    for exp_id in sorted(grouped_rows.keys(), key=lambda value: int(value)):
        rows = grouped_rows[exp_id]
        rows.sort(key=lambda point: point["temps"])

        first_point = rows[0]
        sample = {
            "initial": (
                first_point["x"] - center_x,
                first_point["y"] - center_y,
                first_point["speedX"],
                first_point["speedY"],
            ),
            "trajectory": [
                (point["x"] - center_x, point["y"] - center_y) for point in rows
            ],
        }
        parsed_data.append(sample)

    return parsed_data, (center_x, center_y)


_BG = _hex_to_rgb(CLR_PLOT_BG)
_GRID = _hex_to_rgb(CLR_PLOT_GRID)
_TRUE = _hex_to_rgb(CLR_PLOT_TRUE)
_PRED = _hex_to_rgb(CLR_PLOT_PRED)
_MARKER = _hex_to_rgb(CLR_PLOT_MARKER)


class PlotML(Plot):
    """ML regression demo plot backed by a pyqtgraph PlotWidget."""

    def __init__(self) -> None:
        sim_params = SimulationMLParams()
        super().__init__(sim_params, frame_ms=sim_params.frame_ms)
        self.sim_params: SimulationMLParams = sim_params

        # ── Widget ─────────────────────────────────────────────────────
        self.widget = pg.PlotWidget()
        self.widget.setBackground(CLR_PLOT_BG)
        self.widget.setMenuEnabled(False)
        self.widget.getViewBox().setAspectLocked(lock=True, ratio=1.0)

        # Hide both axes
        self.widget.hideAxis("bottom")
        self.widget.hideAxis("left")

        # Subtle grid using the grid colour token
        self.widget.showGrid(x=True, y=True, alpha=0.15)
        # Override grid pen to use our token colour
        for axis in ("bottom", "left"):
            self.widget.getPlotItem().getAxis(axis).setPen(pg.mkPen(color=(*_GRID, 80)))

        # ── Static curves ──────────────────────────────────────────────
        self.true_curve = self.widget.plot(
            [],
            [],
            pen=pg.mkPen(color=(*_TRUE, 200), width=2),
            name="True",
        )
        self.pred_curve = self.widget.plot(
            [],
            [],
            pen=pg.mkPen(
                color=(*_PRED, 200),
                width=2,
                style=Qt.PenStyle.DashLine,
            ),
            name="Predicted",
        )

        # ── Animated marker ────────────────────────────────────────────
        self.current_point = pg.ScatterPlotItem(
            size=self.sim_params.marker_size,
            brush=pg.mkBrush(*_MARKER, 230),
            pen=pg.mkPen(color=(*_MARKER, 255), width=1),
        )
        self.widget.addItem(self.current_point)

        # ── Model / data storage ───────────────────────────────────────
        self._model: Optional[LinearRegression] = None
        self._train_ref: list = []
        self._mass_center: tuple[float, float] = (0.0, 0.0)
        self._true_traj = np.zeros((0, 2), dtype=np.float32)
        self._pred_traj = np.zeros((0, 2), dtype=np.float32)

        self._build_and_train_model()

    # ── Model training ─────────────────────────────────────────────────

    def _build_and_train_model(self) -> None:
        """Charge les données du CSV et entraîne le modèle de régression."""
        # Chemin vers le fichier CSV
        csv_path = Path(__file__).resolve().parents[4] / "data" / "tracking_data.csv"

        # Charger les données depuis le CSV
        try:
            data, mass_center = parse_tracking_csv(csv_path, center_mode="auto")
            self._mass_center = mass_center

            if not data:
                print(
                    "Aucune donnée trouvée dans tracking_data.csv, utilisation de données par défaut"
                )
                data = self._get_default_data()
                self._mass_center = (0.0, 0.0)
        except Exception as e:
            print(
                f"Erreur lors du chargement du CSV: {e}, utilisation de données par défaut"
            )
            data = self._get_default_data()
            self._mass_center = (0.0, 0.0)

        # Préparer les données pour l'entraînement
        min_trajectory_len = min(len(sample["trajectory"]) for sample in data)

        X = np.array([s["initial"] for s in data], dtype=np.float32)
        Y = np.array(
            [
                [c for pt in s["trajectory"][:min_trajectory_len] for c in pt]
                for s in data
            ],
            dtype=np.float32,
        )

        # Entraîner le modèle
        try:
            self._model = LinearRegression().fit(X, Y)
            print(f"Modèle entraîné sur {len(data)} échantillons")
            print(f"Masse centrale estimée (px): {self._mass_center}")
            print(f"Longueur minimale commune: {min_trajectory_len}")
        except Exception as e:
            print(f"Erreur lors de l'entraînement: {e}")
            self._model = None

        self._train_ref = data

    def _get_default_data(self) -> list:
        """Retourne des données par défaut si le CSV ne peut pas être chargé."""
        return [
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

    # ── Abstract hook implementations ──────────────────────────────────

    def _prepare_simulation(self) -> None:
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
        if self._pred_traj.shape[0] == 0:
            return
        idx = min(frame_index, self._pred_traj.shape[0] - 1)
        x, y = self._pred_traj[idx]
        self.current_point.setData([x], [y])

    def _draw_initial_frame(self) -> None:
        # Afficher la trajectoire réelle uniquement si le paramètre est activé
        if self.sim_params.show_true_trajectory and self._true_traj.shape[0] > 0:
            self.true_curve.setData(self._true_traj[:, 0], self._true_traj[:, 1])
        else:
            self.true_curve.setData([], [])

        if self._pred_traj.shape[0] > 0:
            self.pred_curve.setData(self._pred_traj[:, 0], self._pred_traj[:, 1])
            x0, y0 = self._pred_traj[0]
            self.current_point.setData([x0], [y0], size=self.sim_params.marker_size)
        else:
            self.current_point.setData([], [])

    # ── Parameter update ───────────────────────────────────────────────

    def update_params(self, **kwargs) -> None:
        super().update_params(**kwargs)
        # Si le paramètre show_true_trajectory change, redessiner la frame
        if "show_true_trajectory" in kwargs:
            self._draw_initial_frame()

    # ── Prediction helper ──────────────────────────────────────────────

    def _predict_for_index(self, idx: int) -> np.ndarray:
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
