"""
NIVEL 1 - El Despertar
Detección de palabra clave con openWakeWord
Escucha constantemente esperando "JARVIS"
"""
import openwakeword
import sounddevice as sd
import numpy as np
import yaml
import logging
import time
from core.mqtt_handler import MQTTHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS.Waker")

class Waker:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.wake_word = self.config['jarvis']['wake_word']
        self.sample_rate = self.config['audio']['sample_rate']
        
        # Inicializar detector de palabra clave
        self.oww = openwakeword.Model(
            wakeword_models=[f"{self.wake_word}.tflite"]  # Modelo pre-entrenado
        )
        
        # MQTT
        self.mqtt = MQTTHandler(config_path)
        self.mqtt.connect()
        
        self.is_running = False
        logger.info(f"Nivel 1 - El Despertar inicializado (palabra: '{self.wake_word}')")
    
    def start_listening(self, callback=None):
        """
        Inicia la escucha continua de la palabra clave
        callback: función a llamar cuando se detecta la palabra
        """
        self.is_running = True
        logger.info(f"👂 Escuchando palabra clave '{self.wake_word}'...")
        
        def audio_callback(indata, frames, time_info, status):
            if not self.is_running:
                return
            
            # Procesar audio
            audio = indata[:, 0]  # Mono
            prediction = self.oww.predict(audio)
            
            # Verificar detección
            for model_name, score in prediction.items():
                if score > 0.5:  # Umbral de confianza
                    logger.info(f"Palabra clave detectada: {self.wake_word} ({score:.2f})")
                    self.mqtt.publish('wake', {
                        'word': self.wake_word,
                        'confidence': float(score)
                    })
                    
                    if callback:
                        callback()
        
        # Iniciar stream de audio
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=audio_callback,
            blocksize=self.sample_rate // 10  # 100ms
        )
        self.stream.start()
    
    def stop_listening(self):
        """Detener la escucha"""
        self.is_running = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        logger.info("Escucha detenida")

    def wait(self):
        """Mantener el proceso vivo"""
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_listening()

# Prueba de Nivel 1

if __name__ == "__main__":
    print("=" * 50)
    print("JARVIS OS - NIVEL 1: El Despertar")
    print ("=" * 50)

    waker = Waker()

    def on_wake():
        print("\n JARVIS ACTIVADO. Esperando un comando")
    
    waker.start_listening(callback=on_wake)
    waker.wait()