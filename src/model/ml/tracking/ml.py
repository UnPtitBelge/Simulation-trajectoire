"""Machine Learning — Régression linéaire IC → trajectoire.

Modèle : (x₀, y₀, vx₀, vy₀) → (x₁, y₁, …, x₃₅₀, y₃₅₀)

Chaque trajectoire du CSV est un échantillon d'entraînement :
  - entrée  : les conditions initiales (4 valeurs)
  - sortie  : les 350 positions suivantes aplaties (700 valeurs)
Le modèle prédit la trajectoire complète en un seul appel — pas de rollout.
Trajectoires 16 et 17 sont toujours retenues comme holdout.
"""

import csv
import logging
import os

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.model.params.integrators import MLModel
from src.model.params.ml_params import MLParams, TEST_ICS
from src.model.simulation.base import Plot
from src.util.theme import (
    CLR_DANGER,
    CLR_ML_BG,
    CLR_ML_PRED,
    CLR_ML_TRUE,
    CLR_PRIMARY,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_TEXT,
    CLR_TEXT_SECONDARY,
    CLR_WARNING,
    FS_LG,
    FS_MD,
    FS_SM,
    FS_XS,
)

log = logging.getLogger(__name__)

_CSV = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "tracking_data.csv")
)

_N_OUT = 350  # nombre de positions prédites par chaque modèle (x et y séparés)
              # Toutes les trajectoires ont ≥ 353 points → rows 1..350 toujours présents

_PEN_TRAIN = pg.mkPen((150, 150, 150, 70), width=1)   # gris — trajectoires d'entraînement
_PEN_TRUTH = pg.mkPen(CLR_ML_TRUE, width=2)            # vert — vérité terrain (holdout)
_PEN_PRED  = pg.mkPen(CLR_ML_PRED, width=2)            # bleu — prédiction du modèle


def _load_all_trajectories() -> list[dict] | None:
    """Charge les 17 trajectoires du CSV (données brutes, sans interpolation).

    Retourne une liste de dicts {exp_id, t, x, y, vx, vy} triés par expID,
    ou None si le fichier est absent ou illisible.
    """
    if not os.path.exists(_CSV):
        return None
    try:
        rows_by_id: dict[int, list] = {}
        with open(_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                clean = {
                    (k.strip() if isinstance(k, str) else k): (
                        v.strip() if isinstance(v, str) else v
                    )
                    for k, v in row.items()
                }
                try:
                    exp_id = int(clean["expID"])
                    t  = float(clean["temps"])
                    x  = float(clean["x"])
                    y  = float(clean["y"])
                    vx = float(clean["speedX"])
                    vy = float(clean["speedY"])
                except (KeyError, ValueError):
                    continue
                rows_by_id.setdefault(exp_id, []).append((t, x, y, vx, vy))

        trajectories = []
        for exp_id in sorted(rows_by_id.keys()):
            pts = sorted(rows_by_id[exp_id], key=lambda p: p[0])
            if len(pts) < _N_OUT + 1:
                continue
            arr = np.array(pts, dtype=float)
            trajectories.append(
                {
                    "exp_id": exp_id,
                    "t":  arr[:, 0],
                    "x":  arr[:, 1],
                    "y":  arr[:, 2],
                    "vx": arr[:, 3],
                    "vy": arr[:, 4],
                }
            )
        return trajectories if trajectories else None
    except Exception as e:
        log.warning("CSV load failed: %s", e)
        return None


def _build_training_data(
    trajectories: list[dict], n_train: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construit les matrices X, Y_x, Y_y pour l'entraînement.

    Chaque trajectoire devient un échantillon :
      X[i]   : (x₀, y₀, vx₀, vy₀) — conditions initiales    (4 valeurs)
      Y_x[i] : (x₁, …, x₃₅₀)      — 350 coordonnées x       (350 valeurs)
      Y_y[i] : (y₁, …, y₃₅₀)      — 350 coordonnées y       (350 valeurs)

    Deux modèles indépendants seront entraînés, un par coordonnée.
    """
    X, Yx, Yy = [], [], []
    for traj in trajectories[:n_train]:
        X.append([traj["x"][0], traj["y"][0], traj["vx"][0], traj["vy"][0]])
        Yx.append(traj["x"][1:_N_OUT + 1])
        Yy.append(traj["y"][1:_N_OUT + 1])
    return (
        np.array(X,  dtype=float),
        np.array(Yx, dtype=float),
        np.array(Yy, dtype=float),
    )


def simulate_ml(p: MLParams) -> dict:
    trajectories = _load_all_trajectories()
    if trajectories is None:
        raise RuntimeError("Fichier CSV introuvable : data/tracking_data.csv")
    if len(trajectories) < p.n_train:
        raise RuntimeError(
            f"Seulement {len(trajectories)} trajectoires disponibles "
            f"(n_train={p.n_train} demandé)."
        )

    # Trajectoires 16 et 17 (indices 15/16) restent toujours en holdout
    n_train = min(int(p.n_train), 15)

    X_train, Yx_train, Yy_train = _build_training_data(trajectories, n_train)

    # ── Régression linéaire ───────────────────────────────────────────────────
    lr_x = LinearRegression().fit(X_train, Yx_train)
    lr_y = LinearRegression().fit(X_train, Yy_train)

    # ── MLP (adam + early_stopping : scalable de 15 à ∞ samples) ─────────────
    # early_stopping désactivé si n_train < 5 (validation_fraction réserverait tous les samples)
    _es = n_train >= 5
    mlp_x = make_pipeline(
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(64, 32), solver="adam",
            max_iter=300, early_stopping=_es, n_iter_no_change=15, random_state=42,
        ),
    ).fit(X_train, Yx_train)
    mlp_y = make_pipeline(
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(64, 32), solver="adam",
            max_iter=300, early_stopping=_es, n_iter_no_change=15, random_state=42,
        ),
    ).fit(X_train, Yy_train)

    def _predict(mx, my) -> np.ndarray:
        ic = TEST_ICS[int(p.test_ic)]
        feat = np.array([[ic["x"], ic["y"], ic["vx"], ic["vy"]]])
        xy = np.column_stack((mx.predict(feat)[0], my.predict(feat)[0]))
        return np.vstack([np.array([[ic["x"], ic["y"]]]), xy])  # (N+1, 2)

    pred_lr  = _predict(lr_x, lr_y)
    pred_mlp = _predict(mlp_x, mlp_y)

    # Vérité terrain (uniquement pour les holdouts ICs 0 et 1)
    truth_x: list | None = None
    truth_y: list | None = None
    truth_target_x: np.ndarray | None = None
    truth_target_y: np.ndarray | None = None
    if p.test_ic in (0, 1):
        traj_idx = 15 + int(p.test_ic)
        if traj_idx < len(trajectories):
            t = trajectories[traj_idx]
            # Affichage : trajectoire brute complète (contexte visuel)
            truth_x = t["x"].tolist()
            truth_y = t["y"].tolist()
            # Cibles pour les métriques : les 40 positions que le modèle devait prédire
            truth_target_x = t["x"][1:_N_OUT + 1]
            truth_target_y = t["y"][1:_N_OUT + 1]

    def _metrics(pred: np.ndarray) -> dict[str, float]:
        if truth_target_x is None or truth_target_y is None:
            return {}
        return {
            "r2_x":   float(r2_score(truth_target_x, pred[1:, 0])),
            "r2_y":   float(r2_score(truth_target_y, pred[1:, 1])),
            "rmse_x": float(np.sqrt(mean_squared_error(truth_target_x, pred[1:, 0]))),
            "rmse_y": float(np.sqrt(mean_squared_error(truth_target_y, pred[1:, 1]))),
        }

    train_trajs = [
        {"x": t["x"].tolist(), "y": t["y"].tolist()}
        for t in trajectories[:n_train]
    ]

    return {
        "train_trajs":  train_trajs,
        "truth_x":      truth_x,
        "truth_y":      truth_y,
        "pred_lr":      pred_lr.tolist(),
        "pred_mlp":     pred_mlp.tolist(),
        "metrics_lr":   _metrics(pred_lr),
        "metrics_mlp":  _metrics(pred_mlp),
        "n_frames":     len(pred_lr),
    }


class PlotML(Plot):
    SIM_KEY = "ml"

    def __init__(self, params: MLParams | None = None):
        _p = params or MLParams()
        super().__init__(_p)
        self.params: MLParams = _p
        self.widget = pg.PlotWidget()
        self.widget.setBackground(CLR_ML_BG)
        self.widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.widget.showGrid(x=False, y=False)
        self.widget.hideAxis("bottom")
        self.widget.hideAxis("left")
        legend = self.widget.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(31, 41, 55, 200))
        self.widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._train_trajs:  list[dict]  = []
        self._truth_x:      list | None = None
        self._truth_y:      list | None = None
        self._pred_lr:      list        = []
        self._pred_mlp:     list        = []
        self._metrics_lr:   dict        = {}
        self._metrics_mlp:  dict        = {}
        self._pred_np:      np.ndarray  = np.empty((0, 2))
        self.metrics:       dict        = {}

        # Courbes nommées (légende)
        self.truth_curve = self.widget.plot([], [], pen=_PEN_TRUTH, name="Vrai")
        self.pred_curve  = self.widget.plot([], [], pen=_PEN_PRED,  name="Prédit")
        self.cursor = self.widget.plot(
            [], [],
            pen=None,
            symbol="o",
            symbolSize=8,
            symbolBrush=pg.mkBrush("w"),
            symbolPen=pg.mkPen("w", width=1),
        )

        # Courbes d'entraînement — recréées à chaque _draw_initial
        self._train_curves: list = []

    # ── cache ──────────────────────────────────────────────────

    def _get_params_hash(self):
        # Exclure model_type : les deux modèles sont toujours entraînés.
        # Toggler RL↔MLP est un cache hit — _draw_initial() sélectionne les données.
        p = self.params
        return hash((p.n_train, p.test_ic, p.frame_ms))

    def _get_cache_data(self) -> dict:
        return {
            "_train_trajs": self._train_trajs,
            "_truth_x":     self._truth_x,
            "_truth_y":     self._truth_y,
            "_pred_lr":     self._pred_lr,
            "_pred_mlp":    self._pred_mlp,
            "_metrics_lr":  self._metrics_lr,
            "_metrics_mlp": self._metrics_mlp,
            "_n_frames":    self._n_frames,
        }

    def _set_cache_data(self, data: dict) -> None:
        self._train_trajs = data["_train_trajs"]
        self._truth_x     = data["_truth_x"]
        self._truth_y     = data["_truth_y"]
        self._pred_lr     = data["_pred_lr"]
        self._pred_mlp    = data["_pred_mlp"]
        self._metrics_lr  = data["_metrics_lr"]
        self._metrics_mlp = data["_metrics_mlp"]
        self._n_frames    = data["_n_frames"]

    # ── calcul ─────────────────────────────────────────────────

    def _compute(self) -> None:
        r = simulate_ml(self.params)
        self._train_trajs = r["train_trajs"]
        self._truth_x     = r["truth_x"]
        self._truth_y     = r["truth_y"]
        self._pred_lr     = r["pred_lr"]
        self._pred_mlp    = r["pred_mlp"]
        self._metrics_lr  = r["metrics_lr"]
        self._metrics_mlp = r["metrics_mlp"]
        self._n_frames    = r["n_frames"]

    # ── rendu ──────────────────────────────────────────────────

    def _draw_initial(self) -> None:
        for c in self._train_curves:
            self.widget.removeItem(c)
        self._train_curves.clear()

        # Fond gris : trajectoires d'entraînement brutes
        for traj in self._train_trajs:
            c = self.widget.plot(traj["x"], traj["y"], pen=_PEN_TRAIN)
            self._train_curves.append(c)

        # Vert : trajectoire réelle du holdout (toutes les mesures brutes)
        if self._truth_x is not None:
            self.truth_curve.setData(self._truth_x, self._truth_y)
        else:
            self.truth_curve.setData([], [])

        # Sélectionner prédictions et métriques selon le modèle actif
        use_mlp  = self.params.model_type == MLModel.MLP
        pred_list = self._pred_mlp if use_mlp else self._pred_lr
        self.metrics = self._metrics_mlp if use_mlp else self._metrics_lr

        if pred_list:
            self._pred_np = np.array(pred_list)
            x0, y0 = self._pred_np[0]
            self.cursor.setData([x0], [y0])
            self.frame_updated.emit(0)
        else:
            self._pred_np = np.empty((0, 2))
            self.cursor.setData([], [])

        self.pred_curve.setData([], [])

    def _draw(self, i: int) -> None:
        if not (0 <= i < len(self._pred_np)):
            return
        trail = self._pred_np[:i + 1]
        self.pred_curve.setData(trail[:, 0], trail[:, 1])
        self.cursor.setData([self._pred_np[i, 0]], [self._pred_np[i, 1]])

    # ── métriques ──────────────────────────────────────────────

    def format_metrics(self) -> str:
        if not self.metrics:
            return ""
        r2x    = self.metrics.get("r2_x",   0.0)
        r2y    = self.metrics.get("r2_y",   0.0)
        rmse_x = self.metrics.get("rmse_x", 0.0)
        rmse_y = self.metrics.get("rmse_y", 0.0)
        return (
            f"R² x : {r2x:.3f}   R² y : {r2y:.3f}"
            f"   RMSE x : {rmse_x:.1f} px   RMSE y : {rmse_y:.1f} px"
        )

    def get_metrics_schema(self) -> list[dict]:
        schema = [
            {"key": "prog", "label": "Progression", "unit": "%",  "fmt": ".0f", "color": CLR_PRIMARY},
            {"key": "x",    "label": "x prédit",    "unit": "px", "fmt": ".1f", "color": CLR_WARNING},
            {"key": "y",    "label": "y prédit",    "unit": "px", "fmt": ".1f", "color": CLR_WARNING},
        ]
        if self.metrics:
            schema += [
                {"key": "r2_x",   "label": "R² x",   "unit": "",   "fmt": ".3f", "color": CLR_SUCCESS},
                {"key": "r2_y",   "label": "R² y",   "unit": "",   "fmt": ".3f", "color": CLR_SUCCESS},
                {"key": "rmse_x", "label": "RMSE x", "unit": "px", "fmt": ".1f", "color": CLR_DANGER},
                {"key": "rmse_y", "label": "RMSE y", "unit": "px", "fmt": ".1f", "color": CLR_DANGER},
            ]
        return schema

    def get_frame_metrics(self, i: int) -> dict:
        if not (0 <= i < len(self._pred_np)):
            return {}
        x, y = float(self._pred_np[i, 0]), float(self._pred_np[i, 1])
        prog = (i + 1) / max(len(self._pred_np), 1) * 100.0
        d: dict = {"prog": prog, "x": x, "y": y}
        if self.metrics:
            d["r2_x"]   = self.metrics.get("r2_x",   0.0)
            d["r2_y"]   = self.metrics.get("r2_y",   0.0)
            d["rmse_x"] = self.metrics.get("rmse_x", 0.0)
            d["rmse_y"] = self.metrics.get("rmse_y", 0.0)
        return d
