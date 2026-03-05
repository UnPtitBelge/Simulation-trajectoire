"""Video player widget.

Provides a simple video player with play/pause, stop, load and a time slider.
The widget uses QMediaPlayer + QGraphicsVideoItem (via QVideoSink) for playback,
which renders entirely through Qt's paint system — avoiding the native-window
transparency bug that QVideoWidget suffers from on X11/Wayland when alt-tabbing.
"""

from PySide6.QtCore import QRectF, Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class VideoPlayerWidget(QWidget):
    """A compact video player UI widget.

    Uses QGraphicsView + QGraphicsVideoItem instead of QVideoWidget so that
    video frames are composited through Qt's own paint engine. This prevents
    the transparent/see-through artefact caused by QVideoWidget's native child
    window on X11/Wayland after an alt-tab.
    """

    def __init__(self):
        """Create the video player UI and wire signal handlers."""
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- Graphics-based video display (no native sub-window) ---
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(Qt.black)

        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)

        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setStyleSheet("background-color: black; border: none;")
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setFrameShape(QGraphicsView.NoFrame)
        # Let the view expand to fill all available space
        self.graphics_view.setSizePolicy(
            self.graphics_view.sizePolicy().horizontalPolicy(),
            self.graphics_view.sizePolicy().verticalPolicy(),
        )
        self.main_layout.addWidget(self.graphics_view, stretch=1)

        # --- Media player ---
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_item)

        # Resize the video item whenever the video native size is known
        self.video_item.nativeSizeChanged.connect(self._fit_video)

        # --- Controls layout (horizontal) ---
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(4, 4, 4, 4)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.media_player.stop)
        controls_layout.addWidget(self.stop_button)

        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        controls_layout.addWidget(self.load_button)

        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 0)
        self.time_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.time_slider)

        self.main_layout.addLayout(controls_layout)

        # --- Periodic slider update ---
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_slider)
        self.update_timer.start(1000)

        # --- Media player signals ---
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.positionChanged.connect(self.position_changed)

    # ------------------------------------------------------------------
    # Video sizing
    # ------------------------------------------------------------------

    def _fit_video(self, native_size):
        """Scale the QGraphicsVideoItem to fill the view while keeping aspect ratio."""
        if native_size.isEmpty():
            return
        view_rect = self.graphics_view.rect()
        self.scene.setSceneRect(QRectF(self.graphics_view.rect()))
        self.video_item.setSize(QRectF(self.graphics_view.rect()).size())

    def resizeEvent(self, event):
        """Keep the video item filling the view when the widget is resized."""
        super().resizeEvent(event)
        self.scene.setSceneRect(QRectF(self.graphics_view.rect()))
        self.video_item.setSize(QRectF(self.graphics_view.rect()).size())

    # ------------------------------------------------------------------
    # Playback controls
    # ------------------------------------------------------------------

    def toggle_play(self):
        """Toggle between play and pause states."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("Play")
        else:
            self.media_player.play()
            self.play_button.setText("Pause")

    def load_video(self):
        """Open a file dialog to select a video and start playback."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.play()
            self.play_button.setText("Pause")

    def duration_changed(self, duration):
        """Update slider range when the media duration becomes available."""
        self.time_slider.setRange(0, duration)

    def position_changed(self, position):
        """Update slider position when playback position changes."""
        self.time_slider.setValue(position)

    def set_position(self, position):
        """Seek the media player to the specified position (in ms)."""
        self.media_player.setPosition(position)

    def update_slider(self):
        """Periodic update to sync the slider with the current playback position."""
        if self.media_player.duration() > 0:
            self.time_slider.setValue(self.media_player.position())
