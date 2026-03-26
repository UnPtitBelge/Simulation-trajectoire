"""Sim-to-Real visualization and main integration."""

import logging
import math

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg

from src.model.params.integrators import MLModel
from src.model.params.sim_to_real import SimToRealParams as _P, SimToRealParams
from src.model.simulation.base import Plot
from src.util.theme import (
    CLR_ML_BG,
    CLR_ML_PRED,
    CLR_ML_TRUE,
    CLR_PRIMARY,
    CLR_SUCCESS,
    CLR_TEXT_SECONDARY,
    FS_LG,
    FS_MD,
    FS_SM,
    FS_XS,
)

# Re-export des constantes et fonctions depuis les modules dédiés
from .data_utils import (
    _N_IN, _N_OUT, _MIN_TRAJ_LEN, _POOL_SIZE,
    _SYNTHETIC_CSV, _SYNTHETIC_NPZ, _PRESETS_NPZ, _MODELS_PKL,
    _PRESET_LABELS, _PRESET_N_SIMS, _CONTEXT_LABELS,
    generate_and_save_pool, pool_is_ready, load_pool,
    _run_cone, _make_feat,
)
from .model_utils import (
    train_and_evaluate, save_trained_models, load_trained_models, models_are_ready,
    get_cached_models, set_cached_models,
)
from .preset_utils import load_presets, presets_are_ready

log = logging.getLogger(__name__)

# ── Pens pyqtgraph ────────────────────────────────────────────────────────────

_PEN_TRUTH = pg.mkPen(CLR_ML_TRUE,  width=2)
_PEN_PRED  = pg.mkPen(CLR_ML_PRED,  width=2)
_PEN_TRAIN = pg.mkPen("#374151",     width=1, style=pg.QtCore.Qt.PenStyle.SolidLine)

class PlotSimToReal(Plot):
    """Simulation Sim-to-Real : génère un dataset cône synthétique et entraîne le ML.

    Utilisation en mode normal :
      - _compute()       : génère les trajectoires + entraîne le modèle (QThread)
      - _draw_initial()  : bascule sur la vue résultats, affiche les trajectoires
      - _draw(i)         : anime la trajectoire prédite frame par frame

    La vérité terrain (courbe verte) n'est affichée que si les CI courantes
    correspondent exactement à l'un des 3 presets par défaut.
    Les 3 trajectoires de référence sont pré-calculées hors dataset d'entraînement.

    Seules les CI (r0, v0, phi0) sont passées à ConeParams ; tous les autres
    paramètres physiques utilisent les valeurs par défaut de ConeParams.

    Un signal `progress(current, total)` est émis depuis le thread de calcul
    pour mettre à jour la barre de progression visible pendant le chargement.
    """

    SIM_KEY = "sim_to_real"

    # Émis depuis le thread de calcul — connexion automatiquement queued (thread-safe)
    progress: Signal = Signal(int, int)

    def __init__(self, params: SimToRealParams | None = None):
        _p = params or SimToRealParams()
        super().__init__(_p)
        self.params: SimToRealParams = _p

        self._result:       dict       = {}
        self._pred_np:      np.ndarray = np.empty((0, 2))
        self._train_curves: list       = []
        self.metrics:       dict       = {}
        self._lr_x                     = None
        self._lr_y                     = None
        self._mlp_x                    = None
        self._mlp_y                    = None
        self._ref_trajs:    dict       = {}     # preset_key → (N, 2)
        self._last_n_sims:  int        = -1
        self._precomputed:  dict       = {}     # key → {pred_np, metrics, model_type, …}
        self._preset_btns:  dict[str, QPushButton] = {}

        # Registres des sliders CI — peuplés par _build_ci_bar()
        self._ci_sliders:    dict[str, QSlider] = {}
        self._ci_val_labels: dict[str, QLabel]  = {}

        self.widget = self._build_widget()

        # Boucle automatique : quand l'animation se termine, on repart du début
        self.anim_finished.connect(self._reset_animation)

    # ── Construction du widget ────────────────────────────────────────────────

    def _build_widget(self) -> QWidget:
        root = QWidget()
        root.setStyleSheet(f"background:{CLR_ML_BG};")
        root.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_loading_page())   # index 0
        self._stack.addWidget(self._build_results_page())   # index 1
        self._stack.setCurrentIndex(0)

        layout.addWidget(self._stack)
        return root

    def _build_loading_page(self) -> QWidget:
        """Écran de chargement — visible pendant _compute()."""
        page = QWidget()
        page.setStyleSheet(f"background:{CLR_ML_BG};")

        outer = QVBoxLayout(page)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner = QWidget()
        inner.setFixedWidth(480)
        lay = QVBoxLayout(inner)
        lay.setSpacing(18)
        lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Sim-to-Real — Entraînement en cours")
        title.setStyleSheet(
            f"color:white; font-size:{FS_LG}; font-weight:500; background:transparent;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        self._loading_subtitle = QLabel(
            f"Chargement de {self.params.n_sims} trajectoires depuis le pool…"
        )
        self._loading_subtitle.setStyleSheet(
            f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_MD}; background:transparent;"
        )
        self._loading_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._loading_subtitle)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(10)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(
            f"QProgressBar {{ background:#374151; border-radius:5px; border:none; }}"
            f"QProgressBar::chunk {{ background:{CLR_PRIMARY}; border-radius:5px; }}"
        )
        lay.addWidget(self._progress_bar)

        self._loading_status = QLabel("Démarrage…")
        self._loading_status.setStyleSheet(
            f"color:{CLR_TEXT_SECONDARY}; font-size:{FS_XS}; background:transparent;"
        )
        self._loading_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._loading_status)

        outer.addWidget(inner)

        self.progress.connect(self._on_progress)
        return page

    def _build_results_page(self) -> QWidget:
        """Vue résultats — visible après entraînement."""
        page = QWidget()
        page.setStyleSheet(f"background:{CLR_ML_BG};")

        lay = QVBoxLayout(page)
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

        # Vérité terrain — seulement visible quand CI = un preset
        self._truth_curve = self._plot_widget.plot(
            [], [], pen=_PEN_TRUTH, name="Réel (référence preset)"
        )
        self._pred_curve = self._plot_widget.plot(
            [], [], pen=_PEN_PRED, name="Prédit (ML)"
        )
        self._cursor = self._plot_widget.plot(
            [], [],
            pen=None, symbol="o", symbolSize=8,
            symbolBrush=pg.mkBrush("w"), symbolPen=pg.mkPen("w", width=1),
        )

        lay.addWidget(self._plot_widget, stretch=1)

        # ── Barre de métriques ────────────────────────────────────────────────
        self._metrics_bar = QWidget()
        self._metrics_bar.setStyleSheet(
            "background:#111827; border-top:1px solid #374151;"
        )
        bar = QHBoxLayout(self._metrics_bar)
        bar.setContentsMargins(24, 8, 24, 8)
        bar.setSpacing(40)

        self._bar_labels: dict[str, QLabel] = {}
        for key, label, color in [
            ("n_train", "Trajectoires entr.", "#9CA3AF"),
            ("r2_x",    "R² x",              CLR_SUCCESS),
            ("r2_y",    "R² y",              CLR_SUCCESS),
            ("rmse_x",  "RMSE x",            "#F87171"),
            ("rmse_y",  "RMSE y",            "#F87171"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            k_lbl = QLabel(label)
            k_lbl.setStyleSheet(
                f"color:#6B7280; font-size:{FS_XS}; background:transparent;"
            )
            v_lbl = QLabel("—")
            v_lbl.setStyleSheet(
                f"color:{color}; font-size:{FS_SM}; font-weight:500;"
                f" background:transparent;"
            )
            col.addWidget(k_lbl)
            col.addWidget(v_lbl)
            bar.addLayout(col)
            self._bar_labels[key] = v_lbl

        bar.addStretch()
        note = QLabel("données synthétiques (sim cône)")
        note.setStyleSheet(
            f"color:#4B5563; font-size:{FS_XS}; background:transparent;"
        )
        bar.addWidget(note)

        lay.addWidget(self._metrics_bar, stretch=0)
        lay.addWidget(self._build_model_presets_bar(), stretch=0)
        lay.addWidget(self._build_ci_bar(), stretch=0)
        return page

    def _build_model_presets_bar(self) -> QWidget:
        """Barre de 6 boutons preset pré-calculés (RL×3 + MLP×3)."""
        bar = QWidget()
        bar.setStyleSheet("background:#0D1117; border-top:1px solid #1E293B;")
        bar.setFixedHeight(44)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 6, 16, 6)
        lay.setSpacing(6)

        lbl = QLabel("Presets :")
        lbl.setStyleSheet(f"color:#6B7280; font-size:{FS_XS}; background:transparent;")
        lay.addWidget(lbl)

        _INACTIVE = (
            "QPushButton {"
            "  background:#1F2937; color:#9CA3AF;"
            f" font-size:{FS_XS}; border-radius:4px; padding:2px 10px;"
            "}"
            "QPushButton:hover { background:#374151; }"
        )
        _ACTIVE = (
            "QPushButton {"
            "  background:#2563EB; color:#FFFFFF;"
            f" font-size:{FS_XS}; border-radius:4px; padding:2px 10px;"
            "}"
        )

        # Séparateur entre RL et MLP
        for model_tag, model_label, ns_list in [
            ("rl",  "RL",  _PRESET_N_SIMS),
            ("mlp", "MLP", _PRESET_N_SIMS),
        ]:
            sep = QLabel(f"  {model_label}")
            sep.setStyleSheet(
                f"color:#4B5563; font-size:{FS_XS}; background:transparent;"
            )
            lay.addWidget(sep)
            for i, n in enumerate(ns_list):
                key = f"{model_tag}_{n}"
                btn = QPushButton(_PRESET_LABELS[i])
                btn.setFixedHeight(28)
                btn.setStyleSheet(_INACTIVE)
                btn.setProperty("_preset_key", key)
                btn.setProperty("_inactive_style", _INACTIVE)
                btn.setProperty("_active_style",   _ACTIVE)
                btn.clicked.connect(lambda checked=False, k=key: self._apply_model_preset(k))
                lay.addWidget(btn)
                self._preset_btns[key] = btn

        lay.addStretch()
        return bar

    def _apply_model_preset(self, key: str) -> None:
        """Injecte directement un preset pré-calculé sans re-entraîner."""
        if key not in self._precomputed:
            log.warning("Preset '%s' non disponible.", key)
            return

        p = self._precomputed[key]
        self._pred_np = p["pred_np"]
        self.metrics  = p["metrics"]

        # Mise à jour des labels de métriques
        m = p["metrics"]
        self._bar_labels["n_train"].setText(str(m.get("n_train", "—")))
        self._bar_labels["r2_x"].setText(  f"{m.get('r2_x',  0):.3f}")
        self._bar_labels["r2_y"].setText(  f"{m.get('r2_y',  0):.3f}")
        self._bar_labels["rmse_x"].setText(f"{m.get('rmse_x',0):.4f} m")
        self._bar_labels["rmse_y"].setText(f"{m.get('rmse_y',0):.4f} m")

        # Surlignage du bouton actif
        for k, btn in self._preset_btns.items():
            btn.setStyleSheet(
                btn.property("_active_style") if k == key
                else btn.property("_inactive_style")
            )

        # Relance l'animation depuis le début
        self._reset_animation()

    def _build_ci_bar(self) -> QWidget:
        """Barre de contrôle des conditions initiales de test."""
        bar = QWidget()
        bar.setStyleSheet("background:#0F172A; border-top:1px solid #1E293B;")
        bar.setFixedHeight(62)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 8, 24, 8)
        lay.setSpacing(0)

        # r0 va jusqu'à 0.39 pour couvrir LAUNCH_R0=0.36 (hors distribution ML [0.08,0.35])
        _CI = [
            ("r0",   "r₀",  "m",   0.08, 0.39,  0.01, ".2f"),
            ("v0",   "v₀",  "m/s", 0.10, 2.50,  0.05, ".2f"),
            ("phi0", "φ₀",  "°",   0.0,  355.0,  5.0, ".0f"),
        ]

        for i, (attr, lbl_txt, unit, lo, hi, step, fmt) in enumerate(_CI):
            if i:
                sep = QLabel("|")
                sep.setStyleSheet("color:#1E293B; background:transparent; padding:0 16px;")
                lay.addWidget(sep)

            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet(
                f"color:#9CA3AF; font-size:{FS_SM}; font-weight:500;"
                f" background:transparent; min-width:22px;"
            )
            lay.addWidget(lbl)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setFixedWidth(150)
            cur = getattr(self.params, attr, lo)
            slider.setValue(int((cur - lo) / (hi - lo) * 100))
            slider.setStyleSheet(
                "QSlider::groove:horizontal{height:4px;background:#374151;border-radius:2px;}"
                f"QSlider::handle:horizontal{{width:14px;height:14px;margin:-5px 0;"
                f"background:{CLR_PRIMARY};border-radius:7px;}}"
                "QSlider::sub-page:horizontal{background:#3B82F6;border-radius:2px;}"
            )
            lay.addWidget(slider)

            val_lbl = QLabel(f"{cur:{fmt}} {unit}")
            val_lbl.setStyleSheet(
                f"color:white; font-size:{FS_XS}; font-family:monospace;"
                f" background:transparent; min-width:64px; padding-left:8px;"
            )
            lay.addWidget(val_lbl)

            self._ci_sliders[attr]    = slider
            self._ci_val_labels[attr] = val_lbl

            slider.valueChanged.connect(
                lambda pos, a=attr, l=lo, h=hi, s=step, f=fmt, u=unit, vl=val_lbl:
                    self._on_ci_slider(a, l, h, s, f, u, pos, vl)
            )

        lay.addStretch()
        return bar

    # ── Slot de progression (main thread) ────────────────────────────────────

    @Slot(int, int)
    def _on_progress(self, current: int, total: int) -> None:
        pct = int(current / max(total, 1) * 100)
        self._progress_bar.setValue(pct)
        self._loading_status.setText(f"Simulation {current} / {total}")

    # ── CI sliders (main thread) ──────────────────────────────────────────────

    def _on_ci_slider(
        self, attr: str, lo: float, hi: float, step: float,
        fmt: str, unit: str, pos: int, val_lbl: QLabel,
    ) -> None:
        """Mise à jour d'un slider CI : recalcule la prédiction instantanément."""
        raw = lo + pos / 100.0 * (hi - lo)
        val = round(round(raw / step) * step, 10)
        setattr(self.params, attr, val)
        val_lbl.setText(f"{val:{fmt}} {unit}")
        if self._lr_x is not None:
            self._do_predict()
            self._update_truth_visibility()
            self._reset_animation()

    def _sync_ci_sliders(self) -> None:
        """Synchronise les sliders CI avec self.params (après preset ou cache)."""
        _CI = [
            ("r0",   0.08, 0.39,  0.01, ".2f", "m"),
            ("v0",   0.10, 2.50,  0.05, ".2f", "m/s"),
            ("phi0", 0.0,  355.0,  5.0, ".0f", "°"),
        ]
        for attr, lo, hi, _, fmt, unit in _CI:
            if attr not in self._ci_sliders:
                continue
            val = getattr(self.params, attr, lo)
            slider = self._ci_sliders[attr]
            slider.blockSignals(True)
            slider.setValue(int((val - lo) / (hi - lo) * 100))
            slider.blockSignals(False)
            self._ci_val_labels[attr].setText(f"{val:{fmt}} {unit}")

    # ── Vérité terrain conditionnelle ─────────────────────────────────────────

    def _find_matching_preset(self) -> str | None:
        """Retourne la clé du preset dont les CI correspondent aux paramètres courants."""
        for key, preset in SimToRealParams.PRESENTATION_PRESETS.items():
            if (abs(self.params.r0   - preset["r0"])   < 0.006 and
                    abs(self.params.v0   - preset["v0"])   < 0.03  and
                    abs(self.params.phi0 - preset["phi0"]) < 3.0):
                return key
        return None

    def _update_truth_visibility(self) -> None:
        """Affiche la trajectoire réelle si les CI correspondent à un preset."""
        key = self._find_matching_preset()
        if key and key in self._ref_trajs:
            ref = self._ref_trajs[key]
            self._truth_curve.setData(ref[:, 0], ref[:, 1])
        else:
            self._truth_curve.setData([], [])

    # ── Prédiction légère (main thread) ───────────────────────────────────────

    def _do_predict(self) -> None:
        """Prédit la trajectoire depuis les CI courantes — O(_N_IN) simulation + O(1) ML.

        Simule les _N_IN premiers pas (contexte), construit le vecteur de features,
        puis appelle le modèle sélectionné (RL ou MLP). Le résultat est dans self._pred_np.
        """
        use_mlp = self.params.model_type == MLModel.MLP
        model_x = self._mlp_x if use_mlp else self._lr_x
        model_y = self._mlp_y if use_mlp else self._lr_y
        if model_x is None or model_y is None:
            return

        phi_rad = math.radians(self.params.phi0)
        vx0 = self.params.v0 * math.cos(phi_rad)
        vy0 = self.params.v0 * math.sin(phi_rad)

        # Simulation courte pour obtenir les _N_IN points de contexte.
        # On passe n_frames=_N_IN+1 pour ne pas simuler 3000 frames inutilement.
        ctx_raw = _run_cone(self.params.r0, self.params.v0, self.params.phi0,
                            n_frames=_N_IN + 1)
        # Sécurité : répéter le dernier point si simulation trop courte (rare)
        while len(ctx_raw) < _N_IN:
            ctx_raw.append(ctx_raw[-1])

        ctx_x = np.array([pt[0] for pt in ctx_raw[:_N_IN]])
        ctx_y = np.array([pt[1] for pt in ctx_raw[:_N_IN]])

        feat   = _make_feat(ctx_x, ctx_y, vx0, vy0).reshape(1, -1)
        pred_x = model_x.predict(feat)[0]   # (_N_OUT,)
        pred_y = model_y.predict(feat)[0]   # (_N_OUT,)

        # _pred_np = contexte simulé + prédiction ML
        context        = np.column_stack([ctx_x, ctx_y])          # (_N_IN, 2)
        predicted      = np.column_stack([pred_x, pred_y])        # (_N_OUT, 2)
        self._pred_np  = np.vstack([context, predicted])          # (_N_IN+_N_OUT, 2)
        self._n_frames = len(self._pred_np)

    def _reset_animation(self) -> None:
        """Remet l'animation à zéro avec la nouvelle prédiction (main thread)."""
        if not self._ready or not len(self._pred_np):
            return
        self.stop()
        self.frame      = 0
        self._frame_acc = 0.0
        x0, y0 = self._pred_np[0]
        self._pred_curve.setData([], [])
        self._cursor.setData([x0], [y0])
        self.frame_updated.emit(0)
        self.timer.start()

    # ── Override setup() — court-circuit pour les changements de CI ───────────

    def setup(self) -> None:
        """Si seules les CI ont changé (modèles déjà entraînés), prédit sans thread."""
        if self._lr_x is not None and self.params.n_sims == self._last_n_sims:
            self.stop()
            self._do_predict()
            self._sync_ci_sliders()
            self._update_truth_visibility()
            if hasattr(self, "_bar_labels"):
                self._update_metrics_bar()
            self.frame      = 0
            self._frame_acc = 0.0
            if self._ready:
                x0, y0 = self._pred_np[0]
                self._pred_curve.setData([], [])
                self._cursor.setData([x0], [y0])
                self.frame_updated.emit(0)
                self.setup_done.emit()
                if self._start_after_setup:
                    self._start_after_setup = False
                    self.timer.start()
        else:
            # Ré-entraînement complet : rebascule sur l'écran de chargement
            if hasattr(self, "_stack"):
                self._stack.setCurrentIndex(0)
                self._progress_bar.setValue(0)
                self._loading_subtitle.setText(
                    f"Chargement de {self.params.n_sims} trajectoires depuis le pool…"
                )
                self._loading_status.setText("Démarrage…")
            super().setup()

    # ── Cache ─────────────────────────────────────────────────────────────────

    def _get_cache_data(self) -> dict:
        return {
            "_result":      self._result,
            "_n_frames":    self._n_frames,
            "metrics":      self.metrics,
            "_lr_x":        self._lr_x,
            "_lr_y":        self._lr_y,
            "_mlp_x":       self._mlp_x,
            "_mlp_y":       self._mlp_y,
            "_ref_trajs":   self._ref_trajs,
            "_last_n_sims": self._last_n_sims,
        }

    def _set_cache_data(self, data: dict) -> None:
        self._result      = data["_result"]
        self._n_frames    = data["_n_frames"]
        self.metrics      = data["metrics"]
        self._lr_x        = data.get("_lr_x")
        self._lr_y        = data.get("_lr_y")
        self._mlp_x       = data.get("_mlp_x")
        self._mlp_y       = data.get("_mlp_y")
        self._ref_trajs   = data.get("_ref_trajs", {})
        self._last_n_sims = data.get("_last_n_sims", -1)

    # ── Calcul (QThread) ──────────────────────────────────────────────────────

    def _compute(self) -> None:
        data = load_pool(n_sims=self.params.n_sims)
        if data is None:
            raise RuntimeError(
                "Pool synthétique introuvable. "
                "Relancez l'application pour le régénérer."
            )

        result = train_and_evaluate(data["trajectories"])
        self._result      = result
        self.metrics      = result["metrics_lr"]
        self._lr_x        = result["lr_x"]
        self._lr_y        = result["lr_y"]
        self._mlp_x       = result["mlp_x"]
        self._mlp_y       = result["mlp_y"]
        self._ref_trajs   = data["ref_trajs"]
        self._last_n_sims = self.params.n_sims
        self._do_predict()

    # ── Rendu (main thread) ───────────────────────────────────────────────────

    def _draw_initial(self) -> None:
        self._stack.setCurrentIndex(1)

        # Charge les presets pré-calculés une seule fois
        if not self._precomputed:
            loaded = load_presets()
            if loaded:
                self._precomputed = loaded

        for c in self._train_curves:
            self._plot_widget.removeItem(c)
        self._train_curves.clear()

        r = self._result
        if not r:
            return

        # Trajectoires d'entraînement — max _MAX_DISPLAY_TRAJS courbes grises
        # (x_full/y_full sont None pour les trajectoires au-delà de _MAX_DISPLAY_TRAJS)
        trajs_to_show = [t for t in r["train_trajs"] if t.get("x_full") is not None]
        for traj in trajs_to_show:
            c = self._plot_widget.plot(
                traj["x_full"].tolist(), traj["y_full"].tolist(), pen=_PEN_TRAIN
            )
            self._train_curves.append(c)

        # Vérité terrain conditionnelle (preset uniquement)
        self._update_truth_visibility()

        # Prédiction initiale (_do_predict déjà appelé dans _compute)
        x0, y0 = self._pred_np[0]
        self._pred_curve.setData([], [])
        self._cursor.setData([x0], [y0])

        self._sync_ci_sliders()
        self._update_metrics_bar()

        self.frame_updated.emit(0)

    def _update_metrics_bar(self) -> None:
        """Met à jour la barre de métriques selon le modèle actif."""
        use_mlp = self.params.model_type == MLModel.MLP
        m = self._result.get("metrics_mlp" if use_mlp else "metrics_lr", self.metrics)
        self.metrics = m
        self._bar_labels["n_train"].setText(str(m.get("n_train", "—")))
        self._bar_labels["r2_x"].setText(  f"{m.get('r2_x',  0):.3f}")
        self._bar_labels["r2_y"].setText(  f"{m.get('r2_y',  0):.3f}")
        self._bar_labels["rmse_x"].setText(f"{m.get('rmse_x',0):.4f} m")
        self._bar_labels["rmse_y"].setText(f"{m.get('rmse_y',0):.4f} m")

    def _draw(self, i: int) -> None:
        if not (0 <= i < len(self._pred_np)):
            return
        trail = self._pred_np[:i + 1]
        self._pred_curve.setData(trail[:, 0], trail[:, 1])
        self._cursor.setData([self._pred_np[i, 0]], [self._pred_np[i, 1]])

    # ── Métriques ────────────────────────────────────────────────────────

    def format_metrics(self) -> str:
        if not self.metrics:
            return ""
        m = self.metrics
        return (
            f"n_train : {m.get('n_train', '?')}   "
            f"R² x : {m.get('r2_x', 0):.3f}   R² y : {m.get('r2_y', 0):.3f}   "
            f"RMSE x : {m.get('rmse_x', 0):.4f} m   RMSE y : {m.get('rmse_y', 0):.4f} m"
        )

    def get_metrics_schema(self) -> list[dict]:
        from src.util.theme import CLR_DANGER, CLR_PRIMARY, CLR_SUCCESS
        schema = [
            {"key": "prog", "label": "Progression", "unit": "%",  "fmt": ".0f", "color": CLR_PRIMARY},
            {"key": "x",    "label": "x prédit",    "unit": "m",  "fmt": ".4f", "color": "#9CA3AF"},
            {"key": "y",    "label": "y prédit",    "unit": "m",  "fmt": ".4f", "color": "#9CA3AF"},
        ]
        if self.metrics:
            schema += [
                {"key": "r2_x",   "label": "R² x",   "unit": "",  "fmt": ".3f", "color": CLR_SUCCESS},
                {"key": "r2_y",   "label": "R² y",   "unit": "",  "fmt": ".3f", "color": CLR_SUCCESS},
                {"key": "rmse_x", "label": "RMSE x", "unit": "m", "fmt": ".4f", "color": CLR_DANGER},
                {"key": "rmse_y", "label": "RMSE y", "unit": "m", "fmt": ".4f", "color": CLR_DANGER},
            ]
        return schema

    def get_frame_metrics(self, i: int) -> dict:
        if not (0 <= i < len(self._pred_np)):
            return {}
        x, y = float(self._pred_np[i, 0]), float(self._pred_np[i, 1])
        prog = (i + 1) / max(self._n_frames, 1) * 100.0
        d: dict = {"prog": prog, "x": x, "y": y}
        if self.metrics:
            d.update({k: self.metrics.get(k, 0.0) for k in ("r2_x", "r2_y", "rmse_x", "rmse_y")})
        return d

    # ── Cache ─────────────────────────────────────────────────────────────────────

    def _get_params_hash(self) -> int | None:
        """Hash uniquement sur (n_sims, model_type) — r0/v0/phi0 n'affectent pas l'entraînement."""
        if self.params is None:
            return None
        return hash((self.params.n_sims, self.params.model_type))

    # ── Méthodes ────────────────────────────────────────────────────────────

    def _refresh_prediction(self) -> None:
        """Prédit depuis les CI courantes et met à jour métriques + animation."""
        if self._lr_x is None:
            return
        self._do_predict()
        self._update_truth_visibility()
        self._update_metrics_bar()
        self._reset_animation()

    def apply_preset(self, index: int) -> None:
        """Applique un preset CI sans réentraîner — O(_N_IN) simulation + O(1) ML."""
        presets = type(self.params).PRESENTATION_PRESETS
        if not (0 <= index < len(presets)):
            return
        preset = list(presets.values())[index]
        self.params.r0   = preset["r0"]
        self.params.v0   = preset["v0"]
        self.params.phi0 = preset["phi0"]
        self._refresh_prediction()
        if self._lr_x is not None:
            self._sync_ci_sliders()

    def toggle_model(self) -> None:
        """Bascule entre RL et MLP sans réentraîner."""
        self.params.model_type = (
            MLModel.MLP if self.params.model_type == MLModel.LINEAR else MLModel.LINEAR
        )
        self._refresh_prediction()

    def apply_context_preset(self, idx: int) -> None:
        """Change la taille du contexte (n_sims) et déclenche un réentraînement."""
        if not (0 <= idx < len(_PRESET_N_SIMS)):
            return
        self.params.n_sims = _PRESET_N_SIMS[idx]
        self.restart()

    def _update_train_curve_visibility(self, n_sims: int) -> None:
        """Affiche un nombre de courbes grises proportionnel à n_sims (5 à max)."""
        n_curves = len(self._train_curves)
        if not n_curves:
            return
        max_n = _PRESET_N_SIMS[-1]
        n_display = max(5, min(n_curves, int(n_curves * n_sims / max_n)))
        for i, curve in enumerate(self._train_curves):
            visible = i < n_display
            if curve.isVisible() != visible:
                curve.setVisible(visible)
