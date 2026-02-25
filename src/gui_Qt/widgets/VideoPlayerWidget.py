from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class VideoPlayerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Video widget
        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)

        # Media player and audio output
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Controls
        controls_layout = QHBoxLayout()

        # Play/Pause button
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.media_player.stop)
        controls_layout.addWidget(self.stop_button)

        # Load button
        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        controls_layout.addWidget(self.load_button)

        # Time slider
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 0)
        self.time_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.time_slider)

        # Timer for updating slider
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_slider)
        self.update_timer.start(1000)  # Update every second

        self.layout.addLayout(controls_layout)

        # Connect media player signals
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.positionChanged.connect(self.position_changed)

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("Play")
        else:
            self.media_player.play()
            self.play_button.setText("Pause")

    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", "Video Files (*.mp4 *.avi)"
        )
        if file_path:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.play()
            self.play_button.setText("Pause")

    def duration_changed(self, duration):
        self.time_slider.setRange(0, duration)

    def position_changed(self, position):
        self.time_slider.setValue(position)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_slider(self):
        if self.media_player.duration() > 0:
            self.time_slider.setValue(self.media_player.position())
