"""
Modulo de temporizadores y alarmas para JARVIS
"""
import threading
import time
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("JARVIS.Timers")

class TimerManager:
    """Gestiona temporizadores y alarmas"""

    def __init__(self, speaker=None, sounds=None):
        self.timers = []
        self.alarms = []
        self.speaker = speaker
        self.sounds = sounds
        self.running = True

        self.check_thread = threading.Thread(target=self._check_alarms, daemon=True)
        self.check_thread.start()

    def set_timer(self, seconds: int, label: str = "") -> str:
        end_time = datetime.now() + timedelta(seconds=seconds)

        timer = {
            'end_time': end_time,
            'seconds': seconds,
            'label': label or f"Temporizador de {self._format_time(seconds)}",
            'done': False
        }

        self.timers.append(timer)

        thread = threading.Thread(target=self._timer_thread, args=(timer,), daemon=True)
        thread.start()

        response = f"Temporizador de {self._format_time(seconds)}"
        if label:
            response += f" para {label}"
        response += " iniciado"

        return response

    def set_alarm(self, hour: int, minute: int, label: str = "") -> str:
        now = datetime.now()
        alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if alarm_time <= now:
            alarm_time += timedelta(days=1)

        alarm = {
            'time': alarm_time,
            'hour': hour,
            'minute': minute,
            'label': label or f"Alarma de las {hour:02d}:{minute:02d}",
            'done': False
        }

        self.alarms.append(alarm)

        response = f"Alarma programada para las {hour:02d}:{minute:02d}"
        if label:
            response += f" ({label})"

        return response

    def cancel_timer(self) -> str:
        """Cancela el temporizador mas reciente"""
        for timer in reversed(self.timers):
            if not timer['done']:
                timer['done'] = True
                return f"Temporizador '{timer['label']}' cancelado"
        return "No hay temporizadores activos"

    def cancel_alarm(self) -> str:
        """Cancela la alarma mas reciente"""
        for alarm in reversed(self.alarms):
            if not alarm['done']:
                alarm['done'] = True
                return f"Alarma de las {alarm['hour']:02d}:{alarm['minute']:02d} cancelada"
        return "No hay alarmas programadas"

    def list_timers(self) -> str:
        active = [t for t in self.timers if not t['done']]

        if not active:
            return "No hay temporizadores activos"

        response = "Temporizadores activos: "
        for i, timer in enumerate(active):
            remaining = timer['end_time'] - datetime.now()
            if remaining.total_seconds() > 0:
                response += f"{i+1}. {timer['label']} (faltan {self._format_timedelta(remaining)}), "

        return response.strip(', ')

    def list_alarms(self) -> str:
        active = [a for a in self.alarms if not a['done']]

        if not active:
            return "No hay alarmas programadas"

        response = "Alarmas programadas: "
        for i, alarm in enumerate(active):
            response += f"{i+1}. {alarm['label']}, "

        return response.strip(', ')

    def _timer_thread(self, timer):
        while not timer['done']:
            remaining = (timer['end_time'] - datetime.now()).total_seconds()
            if remaining <= 0:
                timer['done'] = True
                self._trigger_timer(timer)
                break
            time.sleep(0.5)

    def _check_alarms(self):
        while self.running:
            now = datetime.now()
            for alarm in self.alarms:
                if not alarm['done'] and now >= alarm['time']:
                    alarm['done'] = True
                    self._trigger_alarm(alarm)
            time.sleep(1)

    def _trigger_timer(self, timer):
        logger.info(f"Temporizador completado: {timer['label']}")
        if self.sounds:
            self.sounds.play_async(self.sounds.notification)
        if self.speaker:
            self.speaker.speak(f"Atencion. {timer['label']} completado")

    def _trigger_alarm(self, alarm):
        logger.info(f"Alarma: {alarm['label']}")
        if self.sounds:
            for _ in range(3):
                self.sounds.notification()
                time.sleep(0.5)
        if self.speaker:
            self.speaker.speak(f"Alarma. Son las {alarm['hour']:02d}:{alarm['minute']:02d}. {alarm['label']}")

    def parse_time(self, command: str) -> Optional[int]:
        total_seconds = 0

        match = re.search(r'(\d+)\s*horas?', command.lower())
        if match:
            total_seconds += int(match.group(1)) * 3600

        match = re.search(r'(\d+)\s*minutos?', command.lower())
        if match:
            total_seconds += int(match.group(1)) * 60

        match = re.search(r'(\d+)\s*segundos?', command.lower())
        if match:
            total_seconds += int(match.group(1))

        return total_seconds if total_seconds > 0 else None

    def parse_alarm_time(self, command: str) -> Optional[tuple]:
        # Formato HH:MM
        match = re.search(r'(\d{1,2}):(\d{2})', command)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return (hour, minute)

        # Formato "a las X"
        match = re.search(r'a las?\s*(\d{1,2})', command.lower())
        if match:
            hour = int(match.group(1))
            if 'tarde' in command.lower() and hour < 12:
                hour += 12
            elif 'noche' in command.lower() and hour < 12:
                hour += 12
            if 0 <= hour <= 23:
                return (hour, 0)

        return None

    def _format_time(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds} segundos"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            if secs > 0:
                return f"{minutes} minutos y {secs} segundos"
            return f"{minutes} minutos"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours} horas y {minutes} minutos"
            return f"{hours} horas"

    def _format_timedelta(self, td) -> str:
        seconds = int(td.total_seconds())
        return self._format_time(seconds)

    def shutdown(self):
        self.running = False