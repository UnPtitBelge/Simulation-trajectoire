from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
import math

class LiveInfoWidget(QWidget):
    """Semi-transparent floating widget to show live ball data."""

    def __init__(self, parent=None, is_3d=False):
        super().__init__(parent)
        self.is_3d = is_3d
        
        self.setObjectName("liveInfo")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            #liveInfo {
                background-color: rgba(20, 20, 20, 180);
                color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 60);
                margin-top: 20px;
                margin-right: 20px;
            }
            QLabel {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(6)
        
        title_font = QFont("Inter", 15)
        title_font.setBold(True)
        title_label = QLabel("Données en direct")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        content_font = QFont("Inter", 11)
        
        self.pos_label = QLabel("Position: (0.00, 0.00)")
        self.pos_label.setFont(content_font)
        layout.addWidget(self.pos_label)

        self.vel_label = QLabel("Vitesse: 0.00 m/s")
        self.vel_label.setFont(content_font)
        layout.addWidget(self.vel_label)

        self.time_label = QLabel("Temps: 0.00 s")
        self.time_label.setFont(content_font)
        layout.addWidget(self.time_label)

    def update_info(self, index: int, dt: float, x: float, y: float, vx: float, vy: float, z: float = 0.0):
        t = index * dt
        v = math.hypot(vx, vy)
        
        if self.is_3d:
            self.pos_label.setText(f"Position: X={x:.2f}  Y={y:.2f}  Z={z:.2f}")
        else:
            self.pos_label.setText(f"Position: X={x:.1f}  Y={y:.1f}")
            
        self.vel_label.setText(f"Vitesse: |v|={v:.2f} m/s")
        self.time_label.setText(f"Temps: {t:.2f} s")
