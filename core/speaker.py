"""
NIVEL 4 - La Voz
Sintesis de voz local con Piper TTS
"""
import os
import io
import wave
import logging
import threading
import queue
import yaml
import sounddevice as sd
import numpy as np
from typing import Optional
from core.mqtt_handler import MQTTHandler

logger = logging.getLogger("JARVIS.Speaker")

class Speaker:
    """
    Nivel 4: La Voz
    Convierte texto a voz usando Piper TTS de forma local.
    """
    
    def __init__(self, mqtt_handler: Optional[MQTTHandler] = None, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.tts_config = self.config.get('tts', {})
        self.voice = self.tts_config.get('voice', 'es_ES-carlfm-medium')
        self.speed = self.tts_config.get('speed', 1.0)
        self.models_dir = self.tts_config.get('models_dir', './models')
        
        self.mqtt = mqtt_handler if mqtt_handler else MQTTHandler(config_path)
        if not mqtt_handler:
            self.mqtt.connect()
        
        self.queue = queue.Queue()
        self.is_speaking = False
        self.voice_available = False
        
        self._init_piper()
        
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        
        logger.info(f"Nivel 4 - Voz inicializada")
    
    def _init_piper(self):
        """Inicializa Piper TTS"""
        try:
            from piper import PiperVoice
            from piper.download import ensure_voice_exists
            
            os.makedirs(self.models_dir, exist_ok=True)
            
            model_path = ensure_voice_exists(
                self.voice,
                data_dirs=[self.models_dir, os.path.expanduser('~/.local/share/piper-tts')],
                download_dir=self.models_dir
            )
            
            self.piper_voice = PiperVoice.load(model_path)
            self.voice_available = True
            logger.info(f"Voz cargada: {self.voice}")
            
        except ImportError:
            logger.warning("Piper TTS no instalado. Ejecuta: pip install piper-tts")
            self.voice_available = False
        except Exception as e:
            logger.error(f"Error cargando Piper: {e}")
            self.voice_available = False
    
    def speak(self, text: str, wait: bool = False):
        """Reproduce texto como voz"""
        if not text or not text.strip() or not self.voice_available:
            return
        
        text = self._clean_text(text)
        
        if wait:
            self._speak_direct(text)
        else:
            self.queue.put(text)
    
    def _clean_text(self, text: str) -> str:
        """Limpia texto para mejor pronunciacion"""
        if len(text) > 500:
            text = text[:497] + "..."
        text = text.replace('*', '').replace('_', '').replace('`', '')
        text = text.replace('|', ',').replace('  ', ' ')
        return text.strip()
    
    def _speak_direct(self, text: str):
        """Genera y reproduce audio"""
        try:
            self.is_speaking = True
            self.mqtt.publish('speak', {'status': 'speaking', 'text': text[:100]})
            
            audio_buffer = io.BytesIO()
            wav_file = wave.open(audio_buffer, 'wb')
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            
            self.piper_voice.synthesize(text, wav_file)
            wav_file.close()
            
            audio_buffer.seek(0)
            audio_data = np.frombuffer(audio_buffer.read(), dtype=np.int16)
            
            sd.play(audio_data, samplerate=22050)
            sd.wait()
            
            self.mqtt.publish('speak', {'status': 'done'})
            
        except Exception as e:
            logger.error(f"Error reproduciendo voz: {e}")
        finally:
            self.is_speaking = False
    
    def _process_queue(self):
        """Procesa cola de mensajes en segundo plano"""
        while True:
            try:
                text = self.queue.get(timeout=0.5)
                if text:
                    self._speak_direct(text)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error en cola de voz: {e}")
    
    def is_busy(self) -> bool:
        """Verifica si esta hablando"""
        return self.is_speaking or not self.queue.empty()
    
    def wait_until_done(self):
        """Espera hasta que termine de hablar"""
        self.queue.join()
        while self.is_speaking:
            pass
    
    def stop(self):
        """Detiene la reproduccion actual"""
        sd.stop()
        self.is_speaking = False
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except:
                pass