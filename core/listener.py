"""
NIVEL 0 - El Oído
Reconocimiento de voz con faster-whisper
Graba audio del micrófono, transcribe a texto
"""

import sounddevice as sd
import numpy as np
import wave
import tempfile
import os 
import time
import yaml
import logging
from faster_whisper import WhisperModel
from core.mqtt_handler import MQTTHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS.Listener")

class Listener:
    def __init__(self, config_path:str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.audio_config = self.config['audio']
        self.whisper_config = self.config['whisper']


        # Inicializar Whisper (modelo local)
        logger.info(F"Cargando modelo Whisper: '{self.whisper_config['model_size']}'...")
        self.model= WhisperModel(
            self.whisper_config['model_size'],
            device=self.whisper_config['device'],
            compute_type=self.whisper_config['compute_type']
        )

        logger.info("Modelo Whisper cargado")

        # MQTT para comunicación
        self.mqtt = MQTTHandler(config_path)
        self.mqtt.connect()

        logger.info("Nivel 0 - El Oído inicializado")
    
    def record_audio(self) -> str:
        """
        Graba audio hasta detectar silencio
        Retorna la ruta del archivo temporal
        """
        sample_rate = self.audio_config['sample_rate']
        silence_threshold = self.audio_config['silence_threshold']
        silence_duration = self.audio_config['silence_duration']
        max_duration = self.audio_config['max_duration']

        logger.info("Escuchando...")
        self.mqtt.publish("listening", {"status": "listening"})

        audio_data = []
        silence_start = None
        stream = sd.InputStream(
            samplerate=sample_rate, 
            channels=1,
            dtype=np.int16    
        )
        stream.start()

        try:
            while True:
                chunk, _ = stream.read(sample_rate // 10)  # 100ms chunks
                audio_data.append(chunk)

                # Detectar silencio
                volume = np.abs(chunk).mean()

                if volume < silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= silence_duration:
                        logger.info("Silencio detectado")
                        break
                else:
                    silence_start = None


                # Duración máxima
                if len(audio_data) * 0.1 >= max_duration:
                    logger.info("Duración máxima alcanzada")
                    break
        finally:
            stream.stop()
            stream.close()
        
        # Guardar audio temporal 
        audio_array = np.concatenate(audio_data)
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_array.tobytes())

        logger.info(f"Audio grabado: {len(audio_array) * 0.1}s")
        self.mqtt.publish('listening', {"status": 'done'})

        return temp_file.name
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio a texto usando Whisper
        """
        logger.info("Transcribiendo audio...")
        self.mqtt.publish("transcribing", {"status": "transcribing"})

        segments, info = self.model.trancribe(
            audio_path,
            language=self.config['jarvis']['language'],
            beam_size=self.whisper_config['beam_size'],
        )

        text = " ".join([seg.text for seg in segments])

        # Limpiar archivo temporal
        os.unlink(audio_path)

        logger.info(f"Transcripción completa: {text}...")
        self.mqtt.publish('response', {'text' : text, 'source': 'whisper'})

        return text.strip()

    def listen_and_transcribe(self):
        """
        Proceso completo: grabar y transcribir
        """
        audio_path = self.record_audio()
        return self.transcribe(audio_path)
    
# Prueba independiente del nivel 0
if __name__ == "__main__":
    print("=" * 50)
    print("JARVIS OS - NIVEL 0: El Oído")
    print("=" * 50)
    
    listener = Listener()
    
    while True:
        input("\nPresiona Enter para hablar (o 'q' para salir)...")
        text = listener.listen_and_transcribe()
        
        if text.lower() in ['salir', 'adiós', 'exit', 'q']:
            break
        
        print(f"\nHas dicho: {text}")