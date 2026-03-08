"""Video player widget.

Provides a styled video player with play/pause, stop, load, a time
slider, and a current-time label. Uses QMediaPlayer + QGraphicsVideoItem
for playback, avoiding the native-window transparency bug that
QVideoWidget suffers from on X11/Wayland when alt-tabbing.
"""

import logging

from PySide6.QtCore import QRectF, Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from utils.stylesheet import VIDEO_PLAYER_STYLE, VIDEO_SEP_STYLE

log = logging.getLogger(__name__)


def _fmt_ms(ms: int) -> str:
    """Format milliseconds as M:SS."""
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


class VideoPlayerWidget(QWidget):
    """A styled video player backed by QGraphicsVideoItem.

    Uses QGraphicsView + QGraphicsVideoItem instead of QVideoWidget so
    that video frames are composited through Qt's own paint engine,
    preventing the transparent artefact on X11/Wayland after alt-tab.

    Attributes:
        media_player: The QMediaPlayer driving playback.
        audio_output: The QAudioOutput attached to ``media_player``.
        video_item:   The QGraphicsVideoItem receiving decoded frames.
        scene:        The QGraphicsScene that owns ``video_item``.
        graphics_view: The QGraphicsView that renders ``scene``.
        play_button:  Toggles between play and pause.
        stop_button:  Stops playback and resets position to 0.
        load_button:  Opens a native file-picker dialog.
        time_slider:  Horizontal slider reflecting playback position.
        time_label:   Current / total time readout.
        update_timer: 1-second QTimer that periodically syncs the slider.
    """

    def __init__(self) -> None:
        log.debug("VideoPlayerWidget — initialising")
        super().__init__()

        self.setObjectName("videoPlayerOuter")
        self.setStyleSheet(VIDEO_PLAYER_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Video display ──────────────────────────────────────────────
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.GlobalColor.black)

        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)

        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setObjectName("videoView")
        self.graphics_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.graphics_view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.graphics_view.setFrameShape(QFrame.Shape.NoFrame)
        self.graphics_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        root.addWidget(self.graphics_view, stretch=1)

        # ── Placeholder shown when no video is loaded ──────────────────
        self._placeholder = QLabel("No video loaded — click  Load Video  to begin")
        self._placeholder.setObjectName("videoPlaceholder")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Overlay the placeholder on top of the graphics view
        self._placeholder.setParent(self.graphics_view)
        self._placeholder.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._placeholder.show()

        # ── Media engine ──────────────────────────────────────────────
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_item)
        self.video_item.nativeSizeChanged.connect(self._fit_video)

        # ── Controls strip ─────────────────────────────────────────────
        controls = QWidget()
        controls.setObjectName("videoControls")
        controls.setFixedHeight(54)

        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(12, 0, 12, 0)
        ctrl_layout.setSpacing(8)

        self.play_button = QPushButton("▶  Play")
        self.play_button.setObjectName("videoBtnPlay")
        self.play_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.play_button.clicked.connect(self.toggle_play)
        ctrl_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("■  Stop")
        self.stop_button.setObjectName("videoBtn")
        self.stop_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.stop_button.clicked.connect(self.media_player.stop)
        ctrl_layout.addWidget(self.stop_button)

        self.load_button = QPushButton("⏏  Load Video")
        self.load_button.setObjectName("videoBtnLoad")
        self.load_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.load_button.clicked.connect(self.load_video)
        ctrl_layout.addWidget(self.load_button)

        # Thin separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setFixedWidth(1)
        sep.setStyleSheet(VIDEO_SEP_STYLE)
        ctrl_layout.addWidget(sep)

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setObjectName("videoSlider")
        self.time_slider.setRange(0, 0)
        self.time_slider.sliderMoved.connect(self.set_position)
        ctrl_layout.addWidget(self.time_slider, stretch=1)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("videoTimeLabel")
        self.time_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        ctrl_layout.addWidget(self.time_label)

        root.addWidget(controls)

        # ── Media player signals ───────────────────────────────────────
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.media_player.errorOccurred.connect(self._on_media_error)

        log.debug("VideoPlayerWidget — ready")

    # ── Video sizing ───────────────────────────────────────────────────

    def _fit_video(self, native_size) -> None:
        if native_size.isEmpty():
            return
        self.scene.setSceneRect(QRectF(self.graphics_view.rect()))
        self.video_item.setSize(QRectF(self.graphics_view.rect()).size())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.scene.setSceneRect(QRectF(self.graphics_view.rect()))
        self.video_item.setSize(QRectF(self.graphics_view.rect()).size())
        # Keep placeholder centred over the view
        self._placeholder.setGeometry(self.graphics_view.rect())

    # ── Playback controls ──────────────────────────────────────────────

    def toggle_play(self) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            log.info("Video paused — position=%d ms", self.media_player.position())
            self.media_player.pause()
        else:
            log.info("Video playing — position=%d ms", self.media_player.position())
            self.media_player.play()

    def load_video(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            log.info("Loading video — path: %s", file_path)
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.play()
            self._placeholder.hide()
        else:
            log.debug("Load video cancelled — no file selected")

    def duration_changed(self, duration: int) -> None:
        log.info("Video duration known — %d ms (%.1f s)", duration, duration / 1000)
        self.time_slider.setRange(0, duration)
        self._update_time_label(self.media_player.position(), duration)

    def position_changed(self, position: int) -> None:
        self.time_slider.setValue(position)
        self._update_time_label(position, self.media_player.duration())

    def set_position(self, position: int) -> None:
        log.debug("User seeked — position=%d ms", position)
        self.media_player.setPosition(position)

    def update_slider(self) -> None:
        if self.media_player.duration() > 0:
            pos = self.media_player.position()
            self.time_slider.setValue(pos)
            self._update_time_label(pos, self.media_player.duration())

    def _update_time_label(self, position: int, duration: int) -> None:
        self.time_label.setText(f"{_fmt_ms(position)} / {_fmt_ms(duration)}")

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("⏸  Pause")
        else:
            self.play_button.setText("▶  Play")

    def _on_media_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        """Re-show the placeholder and log the error when media fails to load."""
        log.error(
            "Media player error — code=%s message=%r",
            error.name,
            error_string,
        )
        self._placeholder.setText(f"Error: {error_string}")
        self._placeholder.show()
