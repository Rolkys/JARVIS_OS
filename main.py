"""
JARVIS OS - Main
Punto de entrada principal del asistente
"""

import sys
import os
import logging
import threading
import yaml
from core.mqtt_handler import MQTTHandler
from core.listener import Listener
from core.waker import Waker
from core.skills import SkillManager
from core.brain import Brain
from core.speaker import Speaker
from core.sounds import SoundEffects
from core.timers import TimerManager
from core.quotes import get_quote_manager
from ui.hud import StarkHUD
from PySide6.QtWidgets import QApplocation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger("JARVIS.Main")

class JarvisOS:
    """Clase principal que integra todos los modulos de JARVIS"""

    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        logger.info("=" * 50)
        logger.info(f"Iniciando {self.config['jarvis']['name']}...")
        logger.info("=" * 50)

        # Inicializar MQTT (primero, para que todos los usen)
        self.mqtt = MQTTHandler(config_path)
        self.mqtt.connect()

        self.sounds = SoundEffects()
        self.timer_maganer = TimerManager(speaker=self.speaker, sounds=self.sounds)
        self.quotes = get_quote_manager()
        # Inicializar modulos en orden
        logger.info("Cargando modulos...")

        self.speaker        = Speaker(mqtt_handler=self.mqtt, config_path=config_path)
        self.skill_manager  = SkillManager(mqtt_handler=self.mqtt, config_path=config_path)
        self.brain          = Brain(mqtt_handler=self.mqtt, config_path=config_path)
        self.listener       = Listener(config_path=config_path)
        self.waker          = Waker(config_path=config_path)

        # El HUD se inicia en el hilo principal de Qt
        self.hud = None

        logger.info("Todos los modulos cargados")
        self.speaker.speak("Sistemas iniciados, Hola señor.")

    def start_hud(self):
        """Inicia la interfaz visual"""
        self.hud = StarkHUD()
        self.hud.show_hud()
    
    def process_command(self, text: str):
        logger.info(f"Comando recibido: {text}")
        
        if not text:
            return
        
        skill_result = self.skill_manager.execute(text)
        
        if skill_result.get('success'):
            response = skill_result.get('response', 'Accion completada')
            self.sounds.play_async(self.sounds.command_success)
            quote = self.quotes.get_success_quote()
            response = f"{quote}. {response}"
        else:
            response = self.brain.generate_response(text)
            if response:
                self.sounds.play_async(self.sounds.notification)
            else:
                self.sounds.play_async(self.sounds.command_error)
                response = self.quotes.get_error_quote()
        
        if response:
            logger.info(f"JARVIS: {response}")
            self.speaker.speak(response)
        
    def on_wake(self):
        logger.info("Palabra clave detectada")
        self.sounds.play_async(self.sounds.activation_sound)
        self.speaker.stop()
        
        wake_quote = self.quotes.get_wake_quote()
        self.speaker.speak(wake_quote)
        
        text = self.listener.listen_and_transcribe()
        
        if text:
            self.process_command(text)
    
    def run(self):
        """Ejecuta el asistente en modo escucha continua"""
        logger.info(f"Asistente {self.config['jarvis']['name']} iniciado")
        logger.info(f"Di '{self.config['jarvis']['wake_word']}' para activar")
        logger.info("Presiona Ctrl+C para salir")

        # Iniciar HUD en un hilo aparte si Qt no esta corriendo
        hud_thread = threading.Thread(target=self._run_hud, daemon=True)
        hud_thread.start()

        # Iniciar escucha de palabra clave (bloqueante)
        self.waker.start_listening(callback=self.on_wake)
        self.waker.wait()
    
    def _run_hud(self):
        """Ejecuta el HUD de un hilo separado"""
        app = QApplocation.instance()
        if not app:
            app = QApplocation(sys.argv)

        self.start_hud()
        app.exec()
    
    def shutdown(self):
        logger.info("Apagando JARVIS...")
        farewell = self.quotes.get_farewell()
        self.speaker.speak(farewell)
        self.speaker.wait_until_done()
        self.waker.stop_listening()
        self.mqtt.disconnect()

    
    
if __name__ == "__main__":
    jarvis = JarvisOS()
    try:
        jarvis.run()
    except KeyboardInterrupt:
        jarvis.shutdown()
    except Exception as e:
        logger.error(f"Error: {e}")
        jarvis.shutdown()