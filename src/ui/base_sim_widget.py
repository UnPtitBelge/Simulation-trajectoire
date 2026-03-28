"""Widget de simulation abstrait : thread de calcul, timer d'animation, marqueurs.

Toutes les vues de simulation héritent de BaseSimWidget.

Cycle de vie :
  setup(params) → lance _compute() dans un QThread
                → quand terminé : _draw_initial() puis démarre le timer
  timer.timeout → _draw(frame)
  touche P      → MarkerPopup → _add_marker(r, theta)
"""

import logging

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.marker_popup import MarkerPopup

log = logging.getLogger(__name__)


class _Worker(QObject):
    finished = Signal()
    failed   = Signal(str)

    def __init__(self, widget: "BaseSimWidget"):
        super().__init__()
        self._widget = widget

    @Slot()
    def run(self) -> None:
        try:
            self._widget._compute()
            self.finished.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class BaseSimWidget(QWidget):
    compute_done  = Signal()
    frame_updated = Signal(int)
    error_occurred = Signal(str)

    # Sous-classes doivent définir R_MAX pour le popup marqueur
    R_MAX: float = 1.0

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._cfg      = cfg
        self._params   = {}
        self._markers: list[tuple[float, float]] = []  # (r, theta)
        self._frame    = 0
        self._n_frames = 0
        self._ready    = False

        self._timer = QTimer()
        self._timer.setInterval(cfg.get("physics", {}).get("frame_ms", 16))
        self._timer.timeout.connect(self._tick)

        self._thread: QThread | None = None
        self._worker: _Worker | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self._layout = main_layout

    def _init_plot(self, plot_widget: QWidget) -> None:
        """Appelé par la sous-classe pour enregistrer et insérer le widget de rendu."""
        self._layout.addWidget(plot_widget)

    # ── Interface abstraite ───────────────────────────────────────────────────

    def _compute(self) -> None:
        """Calcul de la trajectoire dans le thread worker. PAS d'appels Qt."""
        raise NotImplementedError

    def _draw_initial(self) -> None:
        """Affichage de la frame 0 dans le thread principal."""

    def _draw(self, frame: int) -> None:
        """Mise à jour de l'affichage pour la frame donnée (thread principal)."""
        raise NotImplementedError

    def _add_marker(self, r: float, theta: float) -> None:
        """Rendu d'un marqueur dans la scène. Appelé après stockage."""

    # ── API publique ──────────────────────────────────────────────────────────

    def setup(self, params: dict) -> None:
        """Lance la simulation avec les paramètres donnés."""
        self._stop()
        self._params = params
        self._frame  = 0
        self._ready  = False

        self._thread = QThread()
        self._worker = _Worker(self)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def start(self) -> None:
        if self._ready:
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def reset(self) -> None:
        self._timer.stop()
        self._frame = 0
        if self._ready:
            self._draw_initial()

    # ── Événements clavier ────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.text().lower() == "p":
            popup = MarkerPopup(r_max=self.R_MAX, parent=self)
            popup.marker_added.connect(self._on_marker_added)
            popup.exec()
        else:
            super().keyPressEvent(event)

    # ── Slots internes ────────────────────────────────────────────────────────

    @Slot()
    def _on_done(self) -> None:
        self._ready = True
        self._frame = 0
        self._draw_initial()
        self.compute_done.emit()
        self._timer.start()

    @Slot(str)
    def _on_failed(self, msg: str) -> None:
        log.error("%s._compute() : %s", type(self).__name__, msg)
        self.error_occurred.emit(msg)

    @Slot()
    def _cleanup_thread(self) -> None:
        self._thread = None
        self._worker = None

    @Slot(float, float)
    def _on_marker_added(self, r: float, theta: float) -> None:
        self._markers.append((r, theta))
        self._add_marker(r, theta)

    def _tick(self) -> None:
        if not self._ready:
            return
        if self._frame < self._n_frames:
            self._draw(self._frame)
            self.frame_updated.emit(self._frame)
            self._frame += 1
        else:
            self._timer.stop()

    def _stop(self) -> None:
        self._timer.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
