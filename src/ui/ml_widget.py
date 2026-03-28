"""Vue ML — affichage 2D (vue du dessus) de trajectoires prédites.

Utilisée pour les deux modes :
  - mode="real"  : modèles entraînés au lancement (fournis via `models`)
  - mode="synth" : modèles pré-entraînés sur données synthétiques,
                   sélectionnables par contexte (10%/50%/100%) et algo.

Couches affichées (de bas en haut) :
  1. Trajectoires physiques aléatoires en fond (gris semi-transparent)
  2. Trajectoire de référence physique / vérité terrain (vert)
  3. Trajectoire prédite par le modèle ML (bleu)
  4. Bille animée suivant la prédiction (rouge)
"""

from pathlib import Path

import numpy as np
import pyqtgraph as pg

from config.theme import (
    CLR_ML_BALL, CLR_ML_PRED, CLR_ML_TRUE,
    RGBA_ML_TRAIN_TRAJ, RGB_MARKER,
)
from ml.models import LinearStepModel, MLPStepModel
from ml.predict import predict_trajectory
from physics.cone import compute_cone
from ui.base_sim_widget import BaseSimWidget
from utils.angle import v0_dir_to_vr_vtheta

N_BG_TRAJS = 8  # nombre de trajectoires physiques en arrière-plan


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
        self._models = models or {}
        _src = Path(__file__).resolve().parents[1]  # src/ui/../../ → src/
        self._models_dir = _src / cfg["paths"]["models_dir"]

        # Sélection active
        self._active_algo    = "linear"
        self._active_context = "100pct"   # ignoré en mode "real"

        # Données calculées par _compute()
        self._traj:      np.ndarray | None  = None
        self._true_traj: np.ndarray | None  = None
        self._bg_trajs:  list[np.ndarray]   = []

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

        # Couche 1 — trajectoires physiques en fond (gris semi-transparent)
        bg_pen = pg.mkPen(color=RGBA_ML_TRAIN_TRAJ, width=1)
        self._bg_curves = [self._pw.plot(pen=bg_pen) for _ in range(N_BG_TRAJS)]

        # Couche 2 — vérité terrain / trajectoire physique (vert)
        self._true_curve = self._pw.plot(
            pen=pg.mkPen(color=CLR_ML_TRUE, width=2),
        )

        # Couche 3 — trajectoire prédite par le ML (bleu)
        self._traj_curve = self._pw.plot(
            pen=pg.mkPen(color=CLR_ML_PRED, width=2),
        )

        # Couche 4 — bille animée (rouge)
        self._particle_item = self._pw.plot(
            pen=None, symbol="o", symbolSize=10,
            symbolBrush=CLR_ML_BALL, symbolPen="w",
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
        p       = self._params
        n_steps = self._cfg.get("display", {}).get("n_steps_pred", 10_000)

        if self._mode == "real":
            self._compute_real(p, n_steps)
        else:
            self._compute_synth(p, n_steps)

    def _compute_real(self, p: dict, n_steps: int) -> None:
        """Mode réel : modèles entraînés en unités pixels/unité-temps du tracking."""
        tracking = self._cfg["tracking"]
        ppm      = tracking["px_per_meter"]

        # Init depuis les contrôles (mètres) → pixels
        vr0_px, vth0_px = v0_dir_to_vr_vtheta(p["v0"] * ppm, p["direction_deg"])
        init    = np.array([p["r0"] * ppm, p["theta0"], vr0_px, vth0_px])
        r_max_px = tracking["R"] * ppm

        # Pas de vérité terrain physique ni de bg_trajs en mode réel
        self._true_traj = None
        self._bg_trajs  = []

        model = self._load_model()
        if model is None:
            self._traj = np.zeros((1, 4))
            self._n_frames = 1
            return
        self._traj     = predict_trajectory(model, init, n_steps, r_max=r_max_px)
        self._n_frames = len(self._traj)

    def _compute_synth(self, p: dict, n_steps: int) -> None:
        """Mode synthétique : modèles entraînés en mètres, vérité terrain via compute_cone."""
        phys = self._cfg.get("synth", {}).get("physics", {})

        vr0, vtheta0 = v0_dir_to_vr_vtheta(p["v0"], p["direction_deg"])
        init = np.array([p["r0"], p["theta0"], vr0, vtheta0])

        cone_kw = dict(
            R=phys.get("R", self.R_MAX),
            depth=phys.get("depth", 0.09),
            friction=phys.get("friction", 0.02),
            g=phys.get("g", 9.81),
            dt=phys.get("dt", 0.01),
            n_steps=n_steps,
        )

        # Vérité terrain — simulateur physique
        self._true_traj = compute_cone(
            r0=p["r0"], theta0=p["theta0"], vr0=vr0, vtheta0=vtheta0,
            **cone_kw,
        )

        # Trajectoires physiques en arrière-plan — CI aléatoires fixes
        ranges = self._cfg.get("ranges", {})
        r_lo, r_hi = ranges.get("r0", [0.05, self.R_MAX - 0.01])
        v_lo, v_hi = ranges.get("v0", [0.3, 2.0])
        rng = np.random.default_rng(42)
        self._bg_trajs = []
        for _ in range(N_BG_TRAJS):
            r0_bg     = rng.uniform(r_lo, r_hi * 0.95)
            theta0_bg = rng.uniform(0, 2 * np.pi)
            v0_bg     = rng.uniform(v_lo, v_hi)
            dir_bg    = rng.uniform(-180, 180)
            vr0_bg, vth0_bg = v0_dir_to_vr_vtheta(v0_bg, dir_bg)
            self._bg_trajs.append(compute_cone(
                r0=r0_bg, theta0=theta0_bg, vr0=vr0_bg, vtheta0=vth0_bg,
                **cone_kw,
            ))

        # Prédiction ML
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

        # Trajectoires d'entraînement en fond
        for i, curve in enumerate(self._bg_curves):
            if i < len(self._bg_trajs):
                t = self._bg_trajs[i]
                curve.setData(t[:, 0] * np.cos(t[:, 1]), t[:, 0] * np.sin(t[:, 1]))
            else:
                curve.setData([], [])

        # Vérité terrain (vert) — affichée complète dès le départ
        if self._true_traj is not None:
            t = self._true_traj
            self._true_curve.setData(t[:, 0] * np.cos(t[:, 1]), t[:, 0] * np.sin(t[:, 1]))

        # Trajectoire prédite — commence vide, se révèle via _draw()
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
        """Résumé lisible de l'état courant (modèle, résultat, raison d'arrêt)."""
        if self._traj is None:
            return "Aucune trajectoire calculée."

        n     = len(self._traj)
        algo  = {"linear": "Linéaire", "mlp": "MLP"}.get(self._active_algo, self._active_algo)
        r_end = self._traj[-1, 0]

        if self._mode == "real":
            ppm   = self._cfg["tracking"]["px_per_meter"]
            r_max = self._cfg["tracking"]["R"] * ppm
            stop  = "Sortie bord" if r_end >= r_max - 1.0 else "Arrêt (vitesse nulle)"
            return f"Réel — {algo}\n{n} pas prédits — {stop}"
        else:
            r_max  = self._cfg["synth"]["physics"]["R"]
            n_max  = self._cfg["display"]["n_steps_pred"]
            if n >= n_max:
                stop = "Borne atteinte"
            elif r_end >= r_max - 1e-4:
                stop = "Sortie bord"
            else:
                stop = "Arrêt (vitesse nulle)"
            return f"Synth. — {algo} [{self._active_context}]\n{n} pas prédits — {stop}"

    # ── Marqueurs ─────────────────────────────────────────────────────────────

    def _add_marker(self, r: float, theta: float) -> None:
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        item = self._pw.plot(
            [x], [y], pen=None, symbol="x", symbolSize=12,
            symbolBrush=pg.mkBrush(*[int(c * 255) for c in RGB_MARKER[:3]], 255),
        )
        self._markers_items.append(item)
