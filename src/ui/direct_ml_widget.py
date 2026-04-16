"""Vue ML directe — affichage 2D (vue du dessus) de trajectoires prédites
en une seule inférence CI → trajectoire complète.

Contrairement à MLWidget (step-by-step), le modèle prédit la trajectoire
entière depuis les conditions initiales en un seul appel `model.predict(ic)`.

Couches affichées (de bas en haut) :
  1. Trajectoires d'entraînement en fond (gris semi-transparent)
  2. Trajectoire de référence physique (vert)
  3. Trajectoire prédite par le modèle direct (bleu)
  4. Bille animée suivant la prédiction (rouge)
"""

from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt

from config.theme import (
    CLR_ML_BALL, CLR_ML_PRED, CLR_ML_TRUE,
    RGBA_ML_TRAIN_TRAJ, RGB_MARKER,
)
from ml.direct_models import DirectLinearModel, DirectMLPModel
from physics.cone import compute_cone
from ui.base_sim_widget import BaseSimWidget
from utils.angle import v0_dir_to_vr_vtheta


class DirectMLWidget(BaseSimWidget):
    R_MAX = 0.4

    def __init__(self, cfg: dict, parent=None):
        super().__init__(cfg, parent)
        self.R_MAX = cfg["physics"]["R"]
        self._n_train = cfg.get("display", {}).get("n_train_trajs", 20)
        _src = Path(__file__).resolve().parent.parent
        self._models_dir = _src / cfg["paths"]["models_dir"]

        self._mode           = "direct"
        self._active_algo    = "linear"
        self._active_context = "100pct"

        self._traj:               np.ndarray | None  = None
        self._true_traj:          np.ndarray | None  = None
        self._bg_trajs:           list[np.ndarray]   = []
        self._cached_synth_trajs: list[np.ndarray] | None = None

        # ── pyqtgraph 2D ──
        self._pw: pg.PlotWidget = pg.PlotWidget()
        self._pw.setAspectLocked(True)
        self._pw.setBackground("#1F2937")
        lim = self.R_MAX * 1.1
        self._pw.setXRange(-lim, lim)
        self._pw.setYRange(-lim, lim)
        self._pw.showGrid(x=True, y=True, alpha=0.15)

        angles = np.linspace(0, 2 * np.pi, 200)
        self._pw.plot(
            self.R_MAX * np.cos(angles), self.R_MAX * np.sin(angles),
            pen=pg.mkPen(color="#555555", width=1, style=Qt.PenStyle.DashLine),
        )

        bg_pen = pg.mkPen(color=RGBA_ML_TRAIN_TRAJ, width=1)
        self._bg_curves = [self._pw.plot(pen=bg_pen) for _ in range(self._n_train)]

        self._true_curve = self._pw.plot(pen=pg.mkPen(color=CLR_ML_TRUE, width=2))
        self._traj_curve = self._pw.plot(pen=pg.mkPen(color=CLR_ML_PRED, width=2))
        self._particle_item = self._pw.plot(
            pen=None, symbol="o", symbolSize=10,
            symbolBrush=CLR_ML_BALL, symbolPen="w",
        )

        self._markers_items: list[pg.PlotDataItem] = []
        self._init_plot(self._pw)

    # ── Sélection algo / contexte ─────────────────────────────────────────────

    def set_algo(self, algo: str) -> None:
        self._active_algo = algo

    def set_context(self, context: str) -> None:
        self._active_context = context

    # ── Chargement du modèle ──────────────────────────────────────────────────

    def _load_model(self):
        name = f"direct_{self._active_algo}_{self._active_context}.pkl"
        path = self._models_dir / name
        if not path.exists():
            return None
        if self._active_algo == "linear":
            return DirectLinearModel.load(path)
        return DirectMLPModel.load(path)

    # ── Trajectoires d'entraînement en arrière-plan ───────────────────────────

    def _load_synth_train_trajs(self, n: int) -> list[np.ndarray]:
        if self._cached_synth_trajs is not None:
            return self._cached_synth_trajs[:n]

        synth_dir = self._models_dir.parent / "synthetic"
        chunks = sorted(synth_dir.glob("chunk_*.npz"))
        if not chunks:
            return []
        rng = np.random.default_rng(42)
        chunk_path = chunks[int(rng.integers(0, min(5, len(chunks))))]
        try:
            data = np.load(chunk_path)
            X = data["X"].astype(np.float32)
            y = data["y"].astype(np.float32)
        except Exception:
            return []

        breaks = np.where(np.any(y[:-1] != X[1:], axis=1))[0] + 1
        boundaries = [0] + breaks.tolist() + [len(X)]
        trajs = [
            np.vstack([X[s:e], y[e - 1:e]])
            for s, e in zip(boundaries[:-1], boundaries[1:])
            if e > s
        ]
        if not trajs:
            return []
        idxs = rng.choice(len(trajs), min(n, len(trajs)), replace=False)
        result = [trajs[int(i)] for i in idxs]
        self._cached_synth_trajs = result
        return result

    # ── Simulation ────────────────────────────────────────────────────────────

    def _compute(self) -> None:
        p    = self._params
        phys = {**self._cfg["physics"], **self._cfg.get("synth", {}).get("physics", {})}

        vr0, vtheta0 = v0_dir_to_vr_vtheta(p["v0"], p["direction_deg"])
        init = np.array([p["r0"], p["theta0"], vr0, vtheta0])

        cone_kw = dict(
            R=phys.get("R", self.R_MAX),
            depth=phys.get("depth", 0.09),
            friction=phys.get("friction", 0.02),
            g=phys.get("g", 9.81),
            dt=phys.get("dt", 0.01),
            n_steps=self._cfg.get("display", {}).get("n_steps_pred", 10_000),
            center_radius=phys.get("center_radius", 0.03),
        )

        self._true_traj = compute_cone(
            r0=p["r0"], theta0=p["theta0"], vr0=vr0, vtheta0=vtheta0,
            **cone_kw,
        )
        self._bg_trajs = self._load_synth_train_trajs(self._n_train)

        model = self._load_model()
        if model is None:
            self._traj     = np.zeros((1, 4))
            self._n_frames = 1
            return

        self._traj     = model.predict(init)   # (target_len, 4)
        self._n_frames = len(self._traj)

    # ── Dessin ────────────────────────────────────────────────────────────────

    def _draw_initial(self) -> None:
        if self._traj is None:
            return

        for i, curve in enumerate(self._bg_curves):
            if i < len(self._bg_trajs):
                t = self._bg_trajs[i]
                curve.setData(t[:, 0] * np.cos(t[:, 1]), t[:, 0] * np.sin(t[:, 1]))
            else:
                curve.setData([], [])

        if self._true_traj is not None:
            t = self._true_traj
            self._true_curve.setData(t[:, 0] * np.cos(t[:, 1]), t[:, 0] * np.sin(t[:, 1]))
        else:
            self._true_curve.setData([], [])

        self._traj_curve.setData([], [])
        self._draw(0)

    def _draw(self, frame: int) -> None:
        if self._traj is None:
            return
        t = self._traj[:frame + 1]
        self._traj_curve.setData(t[:, 0] * np.cos(t[:, 1]), t[:, 0] * np.sin(t[:, 1]))
        r, theta = self._traj[frame, 0], self._traj[frame, 1]
        self._particle_item.setData([r * np.cos(theta)], [r * np.sin(theta)])

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> str:
        if self._traj is None:
            return "Aucune trajectoire calculée."
        n    = len(self._traj)
        algo = {"linear": "Linéaire", "mlp": "MLP"}.get(self._active_algo, self._active_algo)
        return f"Direct — {algo} [{self._active_context}]\n{n} pas prédits"

    # ── Marqueurs ─────────────────────────────────────────────────────────────

    def _add_marker(self, r: float, theta: float) -> None:
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        item = self._pw.plot(
            [x], [y], pen=None, symbol="x", symbolSize=12,
            symbolBrush=pg.mkBrush(*[int(c * 255) for c in RGB_MARKER[:3]], 255),
        )
        self._markers_items.append(item)
