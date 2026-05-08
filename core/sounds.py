"""
Modulo de efectos de sonido para JARVIS
Sonidos estilo Stark Industries
"""

import os
import wave
import struct
import math
import logging
import threading
import sounddevice as sd
import numpy as np

logger = logging.getLogger("JARVIS.Sounds")

class SoundEffects:
    """Genera y reproduce efectos de sonido sintetizados"""

    def __init__(self):
        self.sample_rate = 44100
        self.activated = True
        logger.info("Efetos de sonido inicializados")

    def _generate_tone(self, frequency: float, duration: float, volume: float = 0.3) -> np.ndarray:
        """Genera un tono sinusoidal"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        tone = np.sin(2 * np.pi * frequency * t) * volume
        #Envolvente para evitar clicks
        envelope = np.ones_like(tone)
        fade_len= int(0.01 * self.sample_rate)
        envelope[:fade_len] = np.linspace(0, 1, fade_len)
        envelope[-fade_len:] = np.linspace(0, 1, fade_len)
        return (tone * envelope).astype(np.float32)
    
    def _generate_sweep(self, start_freq: float, end_freq: float, duration: float, volume:float=0.3) -> np.ndarray:
        """Genera un barrio de frecuencia"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        freq = np.linspace(start_freq, end_freq, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / self.sample_rate
        sweep = np.sin(phase) * volume
        fade_len = int(0.01 * self.sample_rate)
        envelope = np.ones_like(sweep)
        envelope[:fade_len] = np.linspace(0, 1, fade_len)
        envelope[-fade_len:] = np.linspace(1, 0, fade_len)
        return (sweep * envelope).astype(np.float32)
    
    def activation_sound(self):
        """Sonido cuando JARVIS se activa (estilo Stark)"""
        if not self.activated:
            return
        
        # Barrio ascendente + tono final
        sweep = self._generate_sweep(400, 1200, 0.15, 0.2)
        tone = self._generate_tone(1200, 0.1, 0.15)

        # Silencio entre ellos
        silence = np.zeros(int(0.02 * self.sample_rate), dtype=np.float32)

        sound = np.concatenate([sweep, silence, tone])
        sd.play(sound, self.sample_rate)

    def deactivation_sound(self):
        """Sonido cuando JARVIS se desactiva"""
        if not self.activated:
            return
        
        # Barrio descendente
        sweep = self._generate_sweep(1200, 300, 0.2, 0.15)
        sd.play(sweep, self.sample_rate)

    def command_success(self):
        """Sonido de comando ejecutado correctamente"""
        if not self.activated:
            return
        
        t1 = self._generate_tone(800, 0.05, 0.15)
        t2 = self._generate_tone(1000, 0.05, 0.15)
        silence = np.zeros(int(0.3 * self.sample_rate), dtype=np.float32)
        sound = np.concatenate([t1, silence, t2])
        sd.play(sound, self.sample_rate)
    
    def command_error(self):
        """Sonido de error"""
        if not self.activated:
            return
        
        t1 = self._generate_tone(300, 0.1, 0.15)
        t2 = self._generate_tone(250, 0.1, 0.15)
        silence = np.zeros(int(0.05 * self.sample_rate), dtype=np.float32)
        sound = np.concatenate([t1, silence, t2])
        sd.play(sound, self.sample_rate)

    def notificacion(self):
        """Sonido de notificacion"""
        t1 = self._generate_tone(600, 0.06, 0.1)
        t2 = self._generate_tone(900, 0.06, 0.1)
        t3 = self._generate_tone(1200, 0.08, 0.1)
        silence = np.zeros(int(0.3 * self.sample_rate), dtype=np.float32)
        sound = np.concatenate([t1, silence, t2, silence, t3])
        sd.play(sound, self.sample_rate)
    
    def play_async(self, sound_func):
        """Reproduce un sonido en un hilo aparte"""
        thread = threading.Thread(target=sound_func, daemon=True)
        thread.start()