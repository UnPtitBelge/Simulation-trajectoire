"""Widget de simulation abstrait : thread de calcul, timer d'animation, marqueurs.

Toutes les vues de simulation héritent de BaseSimWidget.

Cycle de vie :
  setup(params) → incrémente _gen, lance _compute() dans un QThread
                → quand terminé : _on_done(gen) vérifie le gen avant de dessiner
  timer.timeout → _draw(frame)
  touche P      → MarkerPopup → _add_marker(r, theta)

Sécurité thread :
  Chaque appel setup() incrémente un compteur de génération (_gen).
  _Worker.finished/failed portent le gen directement (Signal(int) / Signal(int, str)).
  Connectés aux méthodes de self (QWidget dans le thread principal) → Qt utilise
  automatiquement une Queued Connection → _on_done/_on_failed s'exécutent dans le
  thread principal, pas dans le thread worker.
  thread.finished → thread.deleteLater  (C++ libéré après la fin du thread)
  _stop() protège isRunning() par try/except RuntimeError au cas où deleteLater
  a déjà supprimé l'objet C++ entre-temps.
"""

import logging

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.marker_popup import MarkerPopup

log = logging.getLogger(__name__)


class _Worker(QObject):
    finished = Signal(int)       # porte gen
    failed   = Signal(int, str)  # porte gen + message d'erreur

    def __init__(self, widget: "BaseSimWidget", gen: int):
        super().__init__()
        self._widget   = widget
        self._gen      = gen
        self.cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            self._widget._compute()
            if not self.cancelled:
                self.finished.emit(self._gen)
        except Exception as exc:
            if not self.cancelled:
                self.failed.emit(self._gen, str(exc))


class BaseSimWidget(QWidget):
    compute_done   = Signal()
    frame_updated  = Signal(int)
    error_occurred = Signal(str)

    R_MAX: float = 1.0

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._cfg      = cfg
        self._params   = {}
        self._markers: list[tuple[float, float]] = []
        self._frame    = 0
        self._n_frames = 0
        self._ready    = False
        self._gen      = 0   # compteur de génération anti-stale

        self._timer = QTimer()
        self._timer.setInterval(cfg.get("physics", {}).get("frame_ms", 16))
        self._timer.timeout.connect(self._tick)

        self._thread: QThread | None = None
        self._worker: _Worker | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self._layout = main_layout

    def _init_plot(self, plot_widget: QWidget) -> None:
        self._layout.addWidget(plot_widget)

    # ── Interface abstraite ───────────────────────────────────────────────────

    def _compute(self) -> None:
        raise NotImplementedError

    def _draw_initial(self) -> None:
        pass

    def _draw(self, frame: int) -> None:
        raise NotImplementedError

    def _add_marker(self, r: float, theta: float) -> None:
        pass

    # ── API publique ──────────────────────────────────────────────────────────

    def setup(self, params: dict) -> None:
        """Lance la simulation avec les paramètres donnés."""
        self._stop()
        self._params = params
        self._frame  = 0
        self._ready  = False
        self._gen   += 1
        gen = self._gen

        thread = QThread()
        worker = _Worker(self, gen)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        # Connexion vers self (QWidget dans le thread principal) :
        # Qt choisit automatiquement Queued Connection → callbacks dans le thread Qt.
        worker.finished.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker
        thread.start()

    def start(self) -> None:
        if self._ready:
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def toggle(self) -> None:
        """Pause / reprend l'animation."""
        if self._timer.isActive():
            self._timer.stop()
        elif self._ready:
            self._timer.start()

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

    @Slot(int)
    def _on_done(self, gen: int) -> None:
        if gen != self._gen:
            return  # résultat périmé — un nouveau setup() a déjà été lancé
        self._ready = True
        self._frame = 0
        self._draw_initial()
        self.compute_done.emit()
        # Pas d'auto-start : l'utilisateur démarre l'animation via Espace

    @Slot(int, str)
    def _on_failed(self, gen: int, msg: str) -> None:
        if gen != self._gen:
            return
        log.error("%s._compute() : %s", type(self).__name__, msg)
        self.error_occurred.emit(msg)

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
        if self._worker:
            self._worker.cancelled = True
        if self._thread:
            try:
                if self._thread.isRunning():
                    self._thread.quit()
                    self._thread.wait()
            except RuntimeError:
                pass  # C++ object already deleted via deleteLater
        self._thread = None
        self._worker = None
