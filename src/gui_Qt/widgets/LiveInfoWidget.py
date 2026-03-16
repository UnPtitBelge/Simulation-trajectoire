from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser, QFrame
import math

class LiveInfoWidget(QWidget):
    """Semi-transparent floating widget to show live ball data."""

    def __init__(self, parent=None, sim_type="2d"):
        super().__init__(parent)
        self.sim_type = sim_type
        
        self.setObjectName("liveInfo")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False) # allow scroll in text browser
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(450)
        self.setStyleSheet("""
            #liveInfo {
                background-color: rgba(20, 20, 20, 180);
                color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 60);
                margin-top: 20px;
                margin-right: 20px;
                margin-bottom: 20px;
            }
            QLabel {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
            }
            QTextBrowser {
                background-color: transparent;
                border: none;
                color: #DDDDDD;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 40, 40, 40) # Add padding to account for margins
        layout.setSpacing(12)
        
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
        
        # Add a nice little separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 40); border: none; min-height: 1px; max-height: 1px; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(line)
        
        # Markdown explanation section
        self.explanation_label = QLabel("Explications")
        self.explanation_label.setFont(title_font)
        self.explanation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.explanation_label)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setFont(QFont("Inter", 10))
        self.text_browser.setOpenExternalLinks(True)
        
        if self.sim_type == "3d":
            self.text_browser.setMarkdown(
"""
**Simulation 3D : Bille sur un cône**

Cette simulation représente la trajectoire d'une masse glissant avec frottement à l'intérieur d'un entonnoir (ou cône) gravitationnel.

- **Modèle de gravité** : L'accélération subie est influencée par la pente du cône vers son centre.
- **Frottement** : Plus le coefficient de frottement cinétique *&mu;<sub>c</sub>* est imposant, plus la bille perd en vitesse et se rabat rapidement vers le centre.
- **Intégration** : Modèle basé sur la méthode **Euler**, calculant ainsi chaque position suivante *x, y, z* en direct.
"""
            )
        elif self.sim_type == "ml":
            self.text_browser.setMarkdown(
"""
**Simulation Machine Learning : Régression Linéaire**

Cette approche "boîte noire" estime la trajectoire de la bille grâce à un entraînement préalable sur des données expérimentales.

- **Dataset** : Ensemble de données commençant par une position initiale *(x, y)* et un vecteur vitesse *(v<sub>x</sub>, v<sub>y</sub>)* aboutissant sur une trajectoire de points *(x, y)*.
- **Apprentissage** : Un modèle de **Régression Linéaire** apprend à prédire l'intégralité d'une trajectoire à partir des 4 conditions initiales.
- **Prédiction et validation** : Le modèle prédit la trajectoire pour de nouvelles entrées. La *MSE (Mean Squared Error)* permet d'évaluer la précision entre la trajectoire réelle et celle prédite.
"""
            )
        else:
            self.text_browser.setMarkdown(
"""
**Simulation 2D : Orbite et Force Centrale**

Nous observons une bille en orbite soumise à l'influence gravitationnelle d'un corps super-massif au centre.

- **Vitesse initiale** : Détermine l'excentricité de la trajectoire (circulaire ou elliptique).
- **Force de traînée** : Simulation d'un éventuel frottement fluide (ex. orbite très basse en frottement atmosphérique) agissant contre le vecteur vitesse.
- **Moteur physique** : Intégration de **Verlet des vitesses** (*Velocity-Verlet*), qui offre une stabilité exceptionnelle pour la conservation de l'énergie (orbites stables).
"""
            )
            
        layout.addWidget(self.text_browser, stretch=1) # Allow text browser to fill the rest of the vertical space

    def update_info(self, index: int, dt: float, x: float, y: float, vx: float, vy: float, z: float = 0.0):
        t = index * dt
        v = math.hypot(vx, vy)
        
        if self.sim_type == "3d":
            self.pos_label.setText(f"Position: X={x:.2f}  Y={y:.2f}  Z={z:.2f}")
            self.vel_label.setText(f"Vitesse: |v|={v:.2f} m/s")
        elif self.sim_type == "ml":
            self.pos_label.setText(f"Position: X={x:.2f}  Y={y:.2f}")
            self.vel_label.setText(f"Vitesse: |v|={v:.1f} px/s")
        else:
            self.pos_label.setText(f"Position: X={x:.2f}  Y={y:.2f}")
            self.vel_label.setText(f"Vitesse: |v|={v:.2f} m/s")
            
        self.time_label.setText(f"Temps: {t:.2f} s")
