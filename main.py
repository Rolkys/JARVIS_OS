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
from core.sounds import SoundEffects
from core.speaker import Speaker
from core.timers import TimerManager
from core.skills import SkillManager
from core.brain import Brain
from core.listener import Listener
from core.waker import Waker
from core.database import Database
from core.quotes import get_quote_manager
from core.window_tracker import WindowTracker
from core.dashboard import Dashboard
from ui.hud import StarkHUD
from PySide6.QtWidgets import QApplication

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

        # Orden correcto de inicializacion
        self.mqtt = MQTTHandler(config_path)
        self.mqtt.connect()

        self.sounds = SoundEffects()
        self.speaker = Speaker(mqtt_handler=self.mqtt, config_path=config_path)
        self.timer_manager = TimerManager(speaker=self.speaker, sounds=self.sounds)
        self.db = Database()
        self.quotes = get_quote_manager()
        self.window_tracker = WindowTracker()
        self.dashboard = Dashboard(jarvis_instance=self)
        self.dashboard.start()

        self.skill_manager = SkillManager(
            mqtt_handler=self.mqtt,
            timer_manager=self.timer_manager,
            config_path=config_path
        )
        self.brain = Brain(mqtt_handler=self.mqtt, config_path=config_path)
        self.listener = Listener(config_path=config_path)

        # El HUD se inicia en el hilo principal de Qt
        self.hud = None
        self.waker = None

        logger.info("Todos los modulos cargados")
        self.speaker.speak("Sistemas iniciados. Hola señor.")

    def start_hud(self):
        """Inicia la interfaz visual"""
        self.hud = StarkHUD()
        self.hud.show_hud()

    def process_command(self, text: str):
        """Procesa un comando de voz completo"""
        logger.info(f"Comando recibido: {text}")

        if not text:
            return

        # Guardar entrada del usuario
        self.db.save_conversation("user", text)

        # Contexto de ventana
        context = self.window_tracker.get_context()

        # Intentar skills
        skill_result = self.skill_manager.execute(text)

        # Obtener respuesta
        if skill_result.get('success'):
            response = skill_result.get('response', 'Accion completada')
            self.sounds.play_async(self.sounds.command_success)
            quote = self.quotes.get_success_quote()
            response = f"{quote}. {response}"
        else:
            prompt_with_context = text
            if context:
                prompt_with_context = f"[{context}] {text}"

            response = self.brain.generate_response(prompt_with_context)
            if response:
                self.sounds.play_async(self.sounds.notification)
            else:
                self.sounds.play_async(self.sounds.command_error)
                response = self.quotes.get_error_quote()

        # Hablar respuesta
        if response:
            logger.info(f"JARVIS: {response}")
            self.db.save_conversation("assistant", response)
            self.db.log_command(
                text,
                action=skill_result.get('action'),
                success=skill_result.get('success'),
                response=response
            )
            self.speaker.speak(response)

    def on_wake(self):
        """Callback cuando se detecta la palabra clave"""
        logger.info("Palabra clave detectada")
        self.sounds.play_async(self.sounds.activation_sound)
        self.speaker.stop()

        wake_quote = self.quotes.get_wake_quote()
        self.speaker.speak(wake_quote)

        text = self.listener.listen_and_transcribe()

        if text:
            self.process_command(text)

    def run(self):
        """Ejecuta el asistente"""
        logger.info(f"Asistente {self.config['jarvis']['name']} iniciado")
        logger.info(f"Di '{self.config['jarvis']['wake_word']}' para activar")

        # El waker corre en un hilo secundario
        self.waker = Waker(config_path="config.yaml")
        waker_thread = threading.Thread(target=self._run_waker, daemon=True)
        waker_thread.start()

        # Qt corre en el hilo principal
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        self.start_hud()
        app.exec()

    def _run_waker(self):
        """Ejecuta el waker en un hilo separado"""
        self.waker.start_listening(callback=self.on_wake)
        self.waker.wait()

    def shutdown(self):
        """Apaga el asistente correctamente"""
        logger.info("Apagando JARVIS...")
        farewell = self.quotes.get_farewell()
        self.speaker.speak(farewell)
        self.speaker.wait_until_done()
        if self.waker:
            self.waker.stop_listening()
        self.window_tracker.shutdown()
        self.db.close()
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