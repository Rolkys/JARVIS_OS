"""
Modulo de reconocimiento de venta activa para JARVIS
"""

import logging
import threading
import time
from typing import Optional, Dict, Any

logger = logging.getLogger("JARVIS.WindowTracker")

class WindowTracker:
    """Detecta la ventana activa y proporciona contexto"""

    def __init__(self):
        self.current_window = ""
        self.current_app = ""
        self.previous_window = ""
        self.running = True

        # Iniciar monitorea en segundo plano
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

        logger.info("Monitor de ventanas inicializado")

    def _monitor(self):
        """Monitorea la ventana activa cada segundo"""
        import pygetwindow as gw

        while self.running:
            try:
                active = gw.getActiveWindow()
                if active and active.title:
                    new_title = active.title
                    if new_title != self.current_window:
                        self.previous_window = self.current_window
                        self.current_window = new_title
                        self.current_app = self._detect_app(new_title)
            except:
                pass
            time.sleep(1)

    def _detect_app(self, window_title: str) -> str:
        """Detecta la aplicacion por el titulo de ventana"""
        title_lower = window_title.lower()

        if "chrome" in title_lower or "google chrome" in title_lower:
            return "Chrome"
        elif "firefox" in title_lower:
            return "Firefox"
        elif "edge" in title_lower:
            return "Edge"
        elif "discord" in title_lower:
            return "Discord"
        elif "spotify" in title_lower:
            return "Spotify"
        elif "visual studio code" in title_lower:
            return "VS Code"
        elif "notepad" in title_lower or "bloc de notas" in title_lower:
            return "Bloc de notas"
        elif "word" in title_lower and "microsoft" not in title_lower:
            return "Word"
        elif "excel" in title_lower:
            return "Excel"
        elif "powershell" in title_lower:
            return "PowerShell"
        elif "cmd" in title_lower or "simbolo del sistema" in title_lower:
            return "Terminal"
        elif "explorador" in title_lower or "file explorer" in title_lower:
            return "Explorador"
        elif "youtube" in title_lower:
            return "Youtube"
        elif "github" in title_lower:
            return "GitHub"
        elif "whatsapp" in title_lower:
            return "WhatsApp"
        elif "telegram" in title_lower:
            return "Telegram"
        elif "Configuracion" in title_lower or "settings" in title_lower:
            return "Configuracio"
        elif "escritorio" in title_lower or "desktop" in title_lower:
            return "Escritorio"
        else:
            return"Desconocido"

    def get_current_app(self)->str:
        """Obtiene la aplicacion activa actual"""
        return self.current_app

    def get_current_window(self) -> str:
        """Obtiene el titulo de la ventana activa"""
        return self.current_window

    def get_context(self)->str:
        """Obtiene el contexto util para JARVIS"""
        if not self.current_app or self.current_app == "Desconocido":
            return ""

        context = {
            "Chrome"        : "Estas en el navefador Chromo",
            "FireFox"       : "Estas en Firefox",
            "Discord"       : "Estas en Discord",
            "Spotify"       : "Estas escuchando musica en Spotify",
            "VS Code"       : "Estas programando en VS Code",
            "Bloc de notas" : "Estas en el bloc de notas",
            "Word"          : "Estas en Word",
            "Excel"         : "Estas en Excel",
            "PowerShell"    : "Estas en PoweShell",
            "Terminal"      : "Estas en la terminal",
            "Explorador"    : "Estas viendo archivos",
            "YouTube"       : "Estas viendo Youtube",
            "GitHub"        : "Estas en GitHub",
            "WhatsApp"      : "Estas en WhatsApp",
            "Escritorio"    : "Estas en el escritorio",
        }
        return context.get(self.current_app, "")

    def is_coding(self) -> bool:
        """Verifica si estas programando"""
        coding_apps = ["VS Code", "Terminal", "PowerShell"]
        return self.current_app in coding_apps

    def is_browsing(self) -> bool:
        """Verifica si esta navegando"""
        return self.current_app in ["Chrome", "Firefox", "Edge"]

    def is_listening_music(self) -> bool:
        """Verifica si estas escuchando musica"""
        return self.current_app == "Spotify"

    def shutdown(self):
        """Detiene el monitoreo"""
        self.running = False