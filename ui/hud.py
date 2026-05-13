"""
NIVEL 5 - El HUD
Interfaz visual estilo Stark Industries
"""
import sys
import os
import yaml
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, 
    QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, Slot, QRect
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient, QFontDatabase
from core.mqtt_handler import MQTTHandler

logger = logging.getLogger("JARVIS.HUD")

class ArcReactor(QWidget):
    """Widget del Reactor Arc animado"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self.angle = 0
        self.pulse = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(30)
    
    def _update_animation(self):
        self.angle = (self.angle + 2) % 360
        self.pulse = (self.pulse + 0.05) % (2 * 3.14159)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        radius = 50
        pulse_radius = radius + 10 * abs(__import__('math').sin(self.pulse))
        
        # Circulo exterior pulsante
        painter.setPen(Qt.NoPen)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(0, 180, 255, 60))
        gradient.setColorAt(1, QColor(0, 100, 255, 20))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, int(pulse_radius), int(pulse_radius))
        
        # Anillo principal
        painter.setPen(QPen(QColor(0, 200, 255, 200), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius, radius)
        
        # Anillo interior
        painter.setPen(QPen(QColor(0, 220, 255, 150), 2))
        painter.drawEllipse(center, radius - 15, radius - 15)
        
        # Lineas giratorias
        import math
        for i in range(6):
            ang = math.radians(self.angle + i * 60)
            x1 = center.x() + 15 * math.cos(ang)
            y1 = center.y() + 15 * math.sin(ang)
            x2 = center.x() + radius * math.cos(ang)
            y2 = center.y() + radius * math.sin(ang)
            
            painter.setPen(QPen(QColor(0, 200, 255, 100), 1))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Nucleo central
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 250)))
        painter.drawEllipse(center, 10, 10)
        
        # Brillo central
        glow_gradient = QLinearGradient(center.x() - 10, center.y() - 10, 
                                        center.x() + 10, center.y() + 10)
        glow_gradient.setColorAt(0, QColor(255, 255, 255, 200))
        glow_gradient.setColorAt(1, QColor(0, 180, 255, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.drawEllipse(center, 18, 18)


class AudioVisualizer(QWidget):
    """Visualizador de audio animado"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.level = 0
        self.bars = 20
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.start(50)
    
    def set_level(self, level: float):
        """Actualiza el nivel de audio (0.0 - 1.0)"""
        self.level = level
    
    def _update(self):
        import random
        self.level = max(0, min(1, self.level + random.uniform(-0.1, 0.1)))
        self.update()
    
    def paintEvent(self, event):
        import random
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        bar_width = self.width() / self.bars - 2
        
        for i in range(self.bars):
            height = int(self.height() * self.level * random.uniform(0.3, 1.0))
            x = int(i * (bar_width + 2))
            y = (self.height() - height) // 2
            
            color = QColor(0, 200, 255, 150 + int(100 * self.level))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(x, y, int(bar_width), height, 2, 2)


class StatusIndicator(QWidget):
    """Indicador de estado (escuchando, pensando, hablando)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self._color = QColor(0, 255, 0)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(500)
        
        self.pulse_state = False
    
    def set_color(self, color: QColor):
        self._color = color
    
    def paintEvent(self, event):
        self.pulse_state = not self.pulse_state
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        alpha = 255 if self.pulse_state else 100
        color = QColor(self._color.red(), self._color.green(), self._color.blue(), alpha)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(2, 2, 16, 16)


class StarkHUD(QMainWindow):
    """Ventana principal del HUD estilo Stark"""
    
    response_signal = Signal(str)
    status_signal = Signal(str, str)
    
    def __init__(self, config_path: str = "config.yaml"):
        super().__init__()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.mqtt = MQTTHandler(config_path)
        self.mqtt.connect()
        self.mqtt.subscribe('response', self._on_response)
        self.mqtt.subscribe('listening', self._on_listening)
        self.mqtt.subscribe('processing', self._on_processing)
        self.mqtt.subscribe('speak', self._on_speak)
        
        self.response_signal.connect(self._update_response)
        self.status_signal.connect(self._update_status)
        
        self._init_ui()
        self._setup_animations()
        
        logger.info("Nivel 5 - HUD inicializado")
    
    def _init_ui(self):
        """Configura la interfaz de usuario"""
        self.setWindowTitle("JARVIS OS - HUD")
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Tamanio de la ventana
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(
            screen.width() - 420,
            screen.height() - 320,
            400,
            300
        )
        
        # Widget central
        central = QWidget()
        central.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 15, 25, 220);
                border: 1px solid rgba(0, 180, 255, 100);
                border-radius: 15px;
            }
            QLabel {
                color: #00ccff;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        self.setCentralWidget(central)
        
        # Layout principal
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Header con Reactor Arc y titulo
        header = QHBoxLayout()
        
        # Reactor Arc
        self.reactor = ArcReactor()
        header.addWidget(self.reactor)
        
        # Titulo y estado
        title_layout = QVBoxLayout()
        self.title_label = QLabel("J.A.R.V.I.S.")
        self.title_label.setFont(QFont("Consolas", 16, QFont.Bold))
        self.title_label.setStyleSheet("color: #00ccff;")
        title_layout.addWidget(self.title_label)
        
        self.status_layout = QHBoxLayout()
        self.status_indicator = StatusIndicator()
        self.status_label = QLabel("En espera...")
        self.status_label.setFont(QFont("Consolas", 9))
        self.status_label.setStyleSheet("color: #0088aa;")
        self.status_layout.addWidget(self.status_indicator)
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addStretch()
        title_layout.addLayout(self.status_layout)
        
        header.addLayout(title_layout)
        header.addStretch()
        layout.addLayout(header)
        
        # Visualizador de audio
        self.visualizer = AudioVisualizer()
        layout.addWidget(self.visualizer)
        
        # Texto de respuesta
        self.response_label = QLabel("Sistemas listos.")
        self.response_label.setFont(QFont("Consolas", 11))
        self.response_label.setWordWrap(True)
        self.response_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: rgba(0, 50, 80, 150);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.response_label)
        
        # Footer con hora
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Consolas", 9))
        self.time_label.setStyleSheet("color: #005570;")
        self.time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.time_label)
        
        # Timer para actualizar hora
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
    
    def _setup_animations(self):
        """Configura animaciones de la ventana"""
        # Animacion de opacidad al iniciar
        self.opacity_effect = QGraphicsOpacityEffect()
        self.centralWidget().setGraphicsEffect(self.opacity_effect)
        
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(1000)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in.start()
    
    def _update_clock(self):
        """Actualiza el reloj"""
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S  |  %d/%m/%Y"))
    
    @Slot(str)
    def _update_response(self, text: str):
        """Actualiza el texto de respuesta"""
        self.response_label.setText(text)
        self.visualizer.set_level(0.0)
    
    @Slot(str, str)
    def _update_status(self, status: str, message: str):
        """Actualiza el indicador de estado"""
        self.status_label.setText(message)
        
        colors = {
            'listening': QColor(0, 255, 100),
            'processing': QColor(255, 200, 0),
            'speaking': QColor(0, 150, 255),
            'idle': QColor(0, 255, 0),
            'error': QColor(255, 0, 0),
        }
        
        self.status_indicator.set_color(colors.get(status, QColor(0, 255, 0)))
    
    # MQTT Callbacks
    def _on_response(self, data):
        text = data.get('text', '') if isinstance(data, dict) else str(data)
        self.response_signal.emit(text)
        self.status_signal.emit('idle', 'En espera...')
        self.visualizer.set_level(0.0)
    
    def _on_listening(self, data):
        if data.get('status') == 'recording':
            self.status_signal.emit('listening', 'Escuchando...')
            self.visualizer.set_level(0.7)
        elif data.get('status') == 'done':
            self.visualizer.set_level(0.0)
    
    def _on_processing(self, data):
        self.status_signal.emit('processing', 'Procesando...')
        self.visualizer.set_level(0.5)
    
    def _on_speak(self, data):
        if data.get('status') == 'speaking':
            self.status_signal.emit('speaking', 'Hablando...')
            self.visualizer.set_level(0.9)
        elif data.get('status') == 'done':
            self.visualizer.set_level(0.0)
    
    def show_hud(self):
        """Muestra el HUD"""
        self.show()
    
    def hide_hud(self):
        """Oculta el HUD"""
        self.hide()
    
    def closeEvent(self, event):
        """Limpieza al cerrar"""
        self.mqtt.disconnect()
        event.accept()


def run_hud():
    """Funcion para ejecutar el HUD de forma independiente"""
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS OS HUD")
    
    hud = StarkHUD()
    hud.show_hud()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_hud()