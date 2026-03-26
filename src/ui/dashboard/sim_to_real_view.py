"""SimToRealView — génération de données synthétiques et entraînement ML.

Structure :
  ┌─[topbar : titre + bouton retour]──────────────────────────────────────┐
  │ ┌─[gauche 280px]────────────────┬─[droite flexible]──────────────────┐│
  │ │ Nb simulations [slider]       │  Plot 2D vue de dessus (x vs y)    ││
  │ │                               │  gris  = trajectoires d'entraîn.   ││
  │ │ [Générer et entraîner]        │  vert  = vérité terrain (holdout)  ││
  │ │ [████████░░░░] 75 %           │  bleu  = prédiction ML             ││
  │ │ Génération…                   │  ●     = point IC                  ││
  │ │                               ├────────────────────────────────────┤│
  │ │ ── Résultats ──               │  R²x | R²y | RMSEx | RMSEy        ││
  │ │ n_train : 48                  │                                    ││
  │ │ R²x : 0.987  R²y : 0.991     │                                    ││
  │ └───────────────────────────────┴────────────────────────────────────┘│
  └────────────────────────────────────────────────────────────────────────┘
"""

import logging

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.core.params.integrators import MLModel
from src.simulations.sim_to_real import _SYNTHETIC_NPZ, load_pool, train_and_evaluate
from src.utils.theme import (
    CLR_BORDER,
    CLR_DANGER,
    CLR_ML_BG,
    CLR_PRIMARY,
    CLR_PRIMARY_DARK,
    CLR_PRIMARY_LIGHT,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_TEXT_SECONDARY,
    FS_LG,
    FS_MD,
    FS_SM,
    FS_XS,
)

log = logging.getLogger(__name__)

_PEN_TRAIN = pg.mkPen((150, 150, 150, 50), width=1)
_PEN_TRUTH = pg.mkPen(CLR_SUCCESS, width=2)
_PEN_PRED  = pg.mkPen(CLR_PRIMARY, width=2)


# ── Worker ────────────────────────────────────────────────────────────────────

class _GenerateWorker(QObject):
    """Charge load_pool() + train_and_evaluate() dans un QThread.

    La génération des trajectoires se fait une seule fois au démarrage de
    l'application (voir app.py). Ce worker se contente de charger le pool
    pré-généré et d'entraîner les modèles sur n_sims trajectoires.

    Signaux :
      progress(current, total) — avancement (émis une seule fois à la fin)
      finished(result)         — dict retourné par train_and_evaluate
      failed(message)          — message d'erreur
    """

    progress = Signal(int, int)
    finished = Signal(object)
    failed   = Signal(str)

    def __init__(self, n_sims: int, model_type: MLModel = MLModel.LINEAR):
        super().__init__()
        self._n_sims = n_sims
        self._model_type = model_type

    @Slot()
    def run(self) -> None:
        try:
            data = load_pool(n_sims=self._n_sims)
            if data is None:
                self.failed.emit(
                    "Pool synthétique introuvable. "
                    "Relancez l'application pour le générer."
                )
                return
            self.progress.emit(self._n_sims, self._n_sims)
            result = train_and_evaluate(data["trajectories"])
            self.finished.emit(result)
        except Exception as e:
            log.exception("_GenerateWorker.run a échoué")
            self.failed.emit(str(e))


# ── Vue principale ────────────────────────────────────────────────────────────

class SimToRealView(QWidget):
    """Vue sim-to-real : génère un dataset cône synthétique et entraîne le ML."""

    def __init__(self, on_back=None, parent=None):
        super().__init__(parent)
        self._on_back = on_back
        self._thread: QThread | None = None
        self._worker: _GenerateWorker | None = None
        self._train_curves: list = []

        self._build_ui()

    # ── Construction de l'UI ─────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Barre supérieure ─────────────────────────────────────────────────
        topbar = QWidget()
        topbar.setStyleSheet(
            f"background:{CLR_SURFACE}; border-bottom:1px solid {CLR_BORDER};"
        )
        top_lay = QHBoxLayout(topbar)
        top_lay.setContentsMargins(16, 10, 16, 10)

        if self._on_back:
            back_btn = QPushButton("← Retour au menu")
            back_btn.setProperty("flat", True)
            back_btn.clicked.connect(self._on_back)
            top_lay.addWidget(back_btn)

        title = QLabel("Sim-to-Real — Entraînement par simulation cône")
        title.setStyleSheet(f"font-size:{FS_LG}; font-weight:500;")
        top_lay.addWidget(title)
        top_lay.addStretch()

        csv_hint = QLabel(f"Pool → {_SYNTHETIC_NPZ}")
        csv_hint.setStyleSheet(f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};")
        top_lay.addWidget(csv_hint)

        root.addWidget(topbar)

        # ── Corps : gauche + droite ───────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, stretch=1)

        body.addWidget(self._build_left_panel(), stretch=0)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{CLR_BORDER};")
        body.addWidget(sep)

        body.addLayout(self._build_right_panel(), stretch=1)

    def _build_left_panel(self) -> QWidget:
        """Panneau gauche : configuration, bouton, progression, résultats."""
        panel = QWidget()
        panel.setFixedWidth(280)
        panel.setStyleSheet(f"background:{CLR_SURFACE};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(panel)
        scroll.setFixedWidth(280)

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # ── Paramètre : nb simulations ────────────────────────────────────────
        lay.addWidget(self._section("Configuration"))

        lay.addWidget(QLabel("Nombre de simulations"))
        self._n_sims_lbl = QLabel("150")
        self._n_sims_lbl.setStyleSheet(
            f"font-size:{FS_MD}; font-weight:500; color:{CLR_PRIMARY};"
        )
        # Slider logarithmique : 200 steps mappés sur [50, 90000]
        # Note : 90k correspond au nombre réel de trajectoires disponibles après filtrage.
        import math as _m
        self._log_min, self._log_max = _m.log(50), _m.log(90_000)
        self._n_sims_slider = QSlider(Qt.Orientation.Horizontal)
        self._n_sims_slider.setMinimum(0)
        self._n_sims_slider.setMaximum(200)
        self._n_sims_slider.setValue(self._log_to_pos(150))
        self._n_sims_slider.valueChanged.connect(self._on_nsims_slider)
        lay.addWidget(self._n_sims_slider)
        lbl_min = QLabel("50")
        lbl_min.setStyleSheet(f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};")
        lbl_max = QLabel("100 000")
        lbl_max.setStyleSheet(f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};")
        row = QHBoxLayout()
        row.addWidget(lbl_min)
        row.addStretch()
        row.addWidget(self._n_sims_lbl)
        row.addStretch()
        row.addWidget(lbl_max)
        lay.addLayout(row)

        hint = QLabel(
            "CI tirées aléatoirement :\n"
            "r₀ ∈ [0.08, 0.35] m\n"
            "v₀ ∈ [0.3, 2.5] m/s\n"
            "φ₀ ∈ [0°, 360°]"
        )
        hint.setStyleSheet(f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};")
        lay.addWidget(hint)

        # ── Toggle modèle ML ────────────────────────────────────────────────
        lay.addWidget(QLabel("Modèle"))
        model_row = QHBoxLayout()
        self._model_group = QButtonGroup(self)
        self._model_group.setExclusive(True)
        for idx, (model, label) in enumerate([
            (MLModel.LINEAR, "Régr. linéaire"),
            (MLModel.MLP, "MLP"),
        ]):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            self._model_group.addButton(btn, idx)
            model_row.addWidget(btn)
        lay.addLayout(model_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{CLR_BORDER};")
        lay.addWidget(sep)

        # ── Bouton + progression ──────────────────────────────────────────────
        self._generate_btn = QPushButton("Générer et entraîner")
        self._generate_btn.setFixedHeight(40)
        self._generate_btn.clicked.connect(self._on_generate)
        lay.addWidget(self._generate_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(16)
        self._progress.setTextVisible(False)
        self._progress.hide()
        lay.addWidget(self._progress)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};")
        self._status_lbl.setWordWrap(True)
        lay.addWidget(self._status_lbl)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{CLR_BORDER};")
        lay.addWidget(sep2)

        # ── Résultats ─────────────────────────────────────────────────────────
        lay.addWidget(self._section("Résultats"))

        self._results_frame = QFrame()
        self._results_frame.setStyleSheet(
            f"background:{CLR_PRIMARY_LIGHT}; border:1px solid {CLR_PRIMARY};"
            f" border-radius:8px;"
        )
        res_lay = QVBoxLayout(self._results_frame)
        res_lay.setContentsMargins(12, 10, 12, 10)
        res_lay.setSpacing(4)

        self._r2x_lbl    = self._metric_row("R² x", "—")
        self._r2y_lbl    = self._metric_row("R² y", "—")
        self._rmsex_lbl  = self._metric_row("RMSE x", "—")
        self._rmsey_lbl  = self._metric_row("RMSE y", "—")
        self._ntrain_lbl = self._metric_row("n_train", "—")
        for lbl in (self._r2x_lbl, self._r2y_lbl,
                    self._rmsex_lbl, self._rmsey_lbl, self._ntrain_lbl):
            res_lay.addWidget(lbl)

        self._results_frame.hide()
        lay.addWidget(self._results_frame)

        lay.addStretch()
        return scroll

    def _build_right_panel(self) -> QVBoxLayout:
        """Panneau droit : plot 2D pyqtgraph."""
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Plot pyqtgraph ────────────────────────────────────────────────────
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground(CLR_ML_BG)
        self._plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._plot_widget.showGrid(x=False, y=False)
        self._plot_widget.hideAxis("bottom")
        self._plot_widget.hideAxis("left")
        self._plot_widget.setAspectLocked(True)
        self._plot_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        legend = self._plot_widget.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(31, 41, 55, 200))

        self._truth_curve = self._plot_widget.plot([], [], pen=_PEN_TRUTH, name="Vrai (holdout)")
        self._pred_curve  = self._plot_widget.plot([], [], pen=_PEN_PRED,  name="Prédit (ML)")
        self._ic_scatter  = self._plot_widget.plot(
            [], [],
            pen=None, symbol="o", symbolSize=8,
            symbolBrush=pg.mkBrush("w"), symbolPen=pg.mkPen("w", width=1),
        )

        lay.addWidget(self._plot_widget, stretch=1)

        # ── Barre de métriques basse ──────────────────────────────────────────
        self._metric_bar = QWidget()
        self._metric_bar.setStyleSheet(
            f"background:{CLR_SURFACE}; border-top:1px solid {CLR_BORDER};"
        )
        bar_lay = QHBoxLayout(self._metric_bar)
        bar_lay.setContentsMargins(20, 8, 20, 8)
        bar_lay.setSpacing(32)

        self._bar_labels: dict[str, QLabel] = {}
        for key, label, color in [
            ("r2_x",   "R² x",    CLR_SUCCESS),
            ("r2_y",   "R² y",    CLR_SUCCESS),
            ("rmse_x", "RMSE x",  CLR_DANGER),
            ("rmse_y", "RMSE y",  CLR_DANGER),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            k_lbl = QLabel(label)
            k_lbl.setStyleSheet(f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};")
            v_lbl = QLabel("—")
            v_lbl.setStyleSheet(f"color:{color}; font-size:{FS_MD}; font-weight:500;")
            col.addWidget(k_lbl)
            col.addWidget(v_lbl)
            bar_lay.addLayout(col)
            self._bar_labels[key] = v_lbl

        bar_lay.addStretch()

        unit_note = QLabel("(unités : mètres)")
        unit_note.setStyleSheet(f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS};")
        bar_lay.addWidget(unit_note)

        self._metric_bar.hide()
        lay.addWidget(self._metric_bar, stretch=0)

        return lay

    # ── Helpers UI ────────────────────────────────────────────────────────────

    @staticmethod
    def _section(title: str) -> QLabel:
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size:{FS_MD}; font-weight:500; color:{CLR_PRIMARY_DARK};")
        return lbl

    @staticmethod
    def _metric_row(label: str, value: str) -> QLabel:
        lbl = QLabel(f"<b>{label} :</b> {value}")
        lbl.setStyleSheet(f"color:{CLR_PRIMARY_DARK}; font-size:{FS_SM};")
        return lbl

    # ── Slider logarithmique n_sims ────────────────────────────────────────────

    def _log_to_pos(self, val: int) -> int:
        import math as _m
        return round(((_m.log(max(val, 50)) - self._log_min)
                      / (self._log_max - self._log_min)) * 200)

    def _pos_to_nsims(self, pos: int) -> int:
        import math as _m
        raw = _m.exp(self._log_min + pos / 200 * (self._log_max - self._log_min))
        # Arrondir à un "beau" nombre : 50 si <75, sinon arrondir à 10/100/1000
        if raw < 75:
            return 50
        if raw < 500:
            return round(raw / 10) * 10
        if raw < 5000:
            return round(raw / 100) * 100
        return round(raw / 1000) * 1000

    def _on_nsims_slider(self, pos: int) -> None:
        n = self._pos_to_nsims(pos)
        self._n_sims_lbl.setText(f"{n:,}".replace(",", " "))

    # ── Génération ────────────────────────────────────────────────────────────

    def _on_generate(self) -> None:
        if self._thread and self._thread.isRunning():
            return

        n_sims = self._pos_to_nsims(self._n_sims_slider.value())
        self._generate_btn.setEnabled(False)
        self._progress.setValue(0)
        self._progress.show()
        self._status_lbl.setText(f"Chargement de {n_sims} trajectoires depuis le pool…")
        self._results_frame.hide()
        self._metric_bar.hide()
        self._clear_plot()

        model_idx = self._model_group.checkedId()
        model_type = list(MLModel)[model_idx] if model_idx >= 0 else MLModel.LINEAR
        self._worker = _GenerateWorker(n_sims, model_type)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    @Slot(int, int)
    def _on_progress(self, current: int, total: int) -> None:
        pct = int(current / max(total, 1) * 100)
        self._progress.setValue(pct)
        self._status_lbl.setText(f"Simulation {current} / {total}…")

    @Slot(object)
    def _on_done(self, result: dict) -> None:
        self._progress.setValue(100)
        self._status_lbl.setText("Entraînement terminé.")
        self._generate_btn.setEnabled(True)
        self._draw_result(result)

    @Slot(str)
    def _on_failed(self, msg: str) -> None:
        self._progress.hide()
        self._status_lbl.setText(f"Erreur : {msg}")
        self._generate_btn.setEnabled(True)

    @Slot()
    def _cleanup_thread(self) -> None:
        self._thread = None
        self._worker = None

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def _clear_plot(self) -> None:
        for c in self._train_curves:
            self._plot_widget.removeItem(c)
        self._train_curves.clear()
        self._truth_curve.setData([], [])
        self._pred_curve.setData([], [])
        self._ic_scatter.setData([], [])

    def _draw_result(self, result: dict) -> None:
        self._clear_plot()

        # Trajectoires d'entraînement complètes (fond gris — x_full peut être None)
        for traj in result["train_trajs"]:
            if traj.get("x_full") is None:
                continue
            c = self._plot_widget.plot(
                traj["x_full"].tolist(), traj["y_full"].tolist(), pen=_PEN_TRAIN
            )
            self._train_curves.append(c)

        # Vérité terrain et prédiction
        truth = np.array(result["truth_positions"])
        pred  = np.array(result["pred_positions"])

        self._truth_curve.setData(truth[:, 0], truth[:, 1])
        self._pred_curve.setData(pred[:, 0], pred[:, 1])
        self._ic_scatter.setData([pred[0, 0]], [pred[0, 1]])

        # Métriques (utilise RL ou MLP selon le toggle)
        model_idx = self._model_group.checkedId()
        m_key = "metrics_mlp" if model_idx == 1 else "metrics_lr"
        m = result.get(m_key, result.get("metrics_lr", {}))
        self._update_metrics(m)

    def _update_metrics(self, m: dict) -> None:
        self._r2x_lbl.setText(   f"<b>R² x :</b> {m['r2_x']:.3f}")
        self._r2y_lbl.setText(   f"<b>R² y :</b> {m['r2_y']:.3f}")
        self._rmsex_lbl.setText( f"<b>RMSE x :</b> {m['rmse_x']:.4f} m")
        self._rmsey_lbl.setText( f"<b>RMSE y :</b> {m['rmse_y']:.4f} m")
        self._ntrain_lbl.setText(f"<b>n_train :</b> {m['n_train']}")
        self._results_frame.show()

        self._bar_labels["r2_x"].setText(  f"{m['r2_x']:.3f}")
        self._bar_labels["r2_y"].setText(  f"{m['r2_y']:.3f}")
        self._bar_labels["rmse_x"].setText(f"{m['rmse_x']:.4f} m")
        self._bar_labels["rmse_y"].setText(f"{m['rmse_y']:.4f} m")
        self._metric_bar.show()
