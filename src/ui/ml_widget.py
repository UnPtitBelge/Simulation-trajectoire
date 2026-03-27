"""Vue ML — affichage 2D (vue du dessus) de trajectoires prédites.

Utilisée pour les deux modes :
  - mode="real"  : modèles entraînés au lancement (fournis via `models`)
  - mode="synth" : modèles pré-entraînés sur données synthétiques,
                   sélectionnables par contexte (10%/50%/100%) et algo.

Affichage : trajectoire prédite (x, y) en coordonnées cartésiennes,
vue de dessus — même repère visuel que la physique polaire.
"""

from pathlib import Path

import numpy as np
import pyqtgraph as pg

from config.theme import CLR_ML_PRED, RGB_MARKER
from ml.models import LinearStepModel, MLPStepModel
from ml.predict import predict_trajectory
from ui.base_sim_widget import BaseSimWidget


class MLWidget(BaseSimWidget):
    R_MAX = 0.4

    def __init__(self, cfg: dict, mode: str, models: dict | None = None, parent=None):
        """
        mode   : "real" ou "synth"
        models : {"linear": LinearStepModel, "mlp": MLPStepModel} pour mode="real"
        """
        super().__init__(cfg, parent)
        self.R_MAX   = cfg["tracking"]["R"]
        self._mode   = mode
        self._models = models or {}  # pour mode "real"
        self._models_dir = Path(cfg["paths"]["models_dir"])

        # Sélection active
        self._active_algo    = "linear"
        self._active_context = "100pct"   # ignoré en mode "real"
        self._traj: np.ndarray | None = None

        # ── pyqtgraph 2D ──
        self._pw: pg.PlotWidget = pg.PlotWidget()
        self._pw.setAspectLocked(True)
        self._pw.setBackground("#1F2937")
        lim = self.R_MAX * 1.1
        self._pw.setXRange(-lim, lim)
        self._pw.setYRange(-lim, lim)
        self._pw.showGrid(x=True, y=True, alpha=0.15)

        # Cercle de bord (rayon R)
        angles = np.linspace(0, 2 * np.pi, 200)
        self._pw.plot(
            self.R_MAX * np.cos(angles), self.R_MAX * np.sin(angles),
            pen=pg.mkPen(color="#555555", width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
        )

        self._traj_curve = self._pw.plot(
            pen=pg.mkPen(color=CLR_ML_PRED, width=2),
        )
        self._particle_item = self._pw.plot(
            pen=None, symbol="o", symbolSize=10,
            symbolBrush=CLR_ML_PRED, symbolPen="w",
        )
        self._markers_items: list[pg.PlotDataItem] = []
        self._init_plot(self._pw)

    # ── Sélection algo / contexte (appelé depuis les contrôles ML) ────────────

    def set_algo(self, algo: str) -> None:
        """algo = "linear" ou "mlp"."""
        self._active_algo = algo

    def set_context(self, context: str) -> None:
        """context = "10pct", "50pct" ou "100pct". Ignoré en mode "real"."""
        self._active_context = context

    def _load_model(self):
        if self._mode == "real":
            return self._models.get(self._active_algo)

        name = f"synth_{self._active_algo}_{self._active_context}.pkl"
        path = self._models_dir / name
        if self._active_algo == "linear":
            return LinearStepModel.load(path)
        return MLPStepModel.load(path)

    # ── Simulation ────────────────────────────────────────────────────────────

    def _compute(self) -> None:
        p     = self._params
        phys  = self._cfg.get("synth", {}).get("physics", {})
        n_steps = phys.get("n_steps", 200)
        init  = np.array([p["r0"], p["theta0"], p["vr0"], p["vtheta0"]])
        model = self._load_model()
        if model is None:
            self._traj = np.zeros((1, 4))
            self._n_frames = 1
            return
        self._traj     = predict_trajectory(model, init, n_steps, r_max=self.R_MAX)
        self._n_frames = len(self._traj)

    def _draw_initial(self) -> None:
        if self._traj is None:
            return
        r, theta = self._traj[:, 0], self._traj[:, 1]
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        self._traj_curve.setData(x, y)
        self._draw(0)

    def _draw(self, frame: int) -> None:
        if self._traj is None:
            return
        r, theta = self._traj[frame, 0], self._traj[frame, 1]
        self._particle_item.setData([r * np.cos(theta)], [r * np.sin(theta)])

    # ── Marqueurs ─────────────────────────────────────────────────────────────

    def _add_marker(self, r: float, theta: float) -> None:
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        item = self._pw.plot(
            [x], [y], pen=None, symbol="x", symbolSize=12,
            symbolBrush=pg.mkBrush(*[int(c * 255) for c in RGB_MARKER[:3]], 255),
        )
        self._markers_items.append(item)
