from pyqtgraph.Qt.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class SimWidget:
    def __init__(self, plot) -> None:
        self.layout = QVBoxLayout()

        self.plot = plot
        self.layout.addWidget(self.plot.widget)

        # Parameters layout
        params_layout = QHBoxLayout()
        # self.param_y = QDoubleSpinBox()
        # self.param_y.setRange(0, 10)
        # self.param_y.setValue(1)
        # params_layout.addWidget(QLabel("Parameter Y:"))
        # params_layout.addWidget(self.param_y)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Start button
        self.start_button = QPushButton("Start Animation")
        self.start_button.clicked.connect(self.start_animation)
        buttons_layout.addWidget(self.start_button)

        # Pause/Resume button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pause_animation)
        buttons_layout.addWidget(self.pause_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_animation)
        buttons_layout.addWidget(self.reset_button)

        params_layout.addLayout(buttons_layout)
        self.layout.addLayout(params_layout)

        # Initial plot (without animation)
        self.plot.redraw()

    def start_animation(self) -> None:
        """Start the animation."""
        self.plot.stop_animation()
        self.plot.setup_animation()
        self.pause_button.setText("Pause")

    def toggle_pause_animation(self) -> None:
        """Toggle between pausing and resuming the animation."""
        if self.plot.animation_timer.isActive():
            self.plot.animation_timer.stop()
            self.pause_button.setText("Resume")
        else:
            self.plot.animation_timer.start()
            self.pause_button.setText("Pause")

    def reset_animation(self) -> None:
        """Reset the animation to the start."""
        self.plot.reset_animation()
        self.pause_button.setText("Pause")
