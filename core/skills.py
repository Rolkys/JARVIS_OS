"""
NIVEL 2 - Las Manos
Sistema de Skills para control de Windows
"""
import subprocess
import os
import re
import logging
import webbrowser
import psutil
import socket
from datetime import datetime
from typing import Dict, Any, Optional
from core.mqtt_handler import MQTTHandler
from core.database import Database
from core.quotes import get_quote_manager

logger = logging.getLogger("JARVIS.Skills")

class SkillManager:
    """
    Nivel 2: Las Manos
    Ejecuta acciones en Windows.
    """

    def __init__(self, mqtt_handler=None, timer_manager=None, config_path="config.yaml"):
        import yaml

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.mqtt = mqtt_handler or MQTTHandler(config_path)
        if not mqtt_handler:
            self.mqtt.connect()

        self.timer_manager = timer_manager
        self.db = Database()
        self.quotes = get_quote_manager()

        self.skills = {
            # ---- APLICACIONES ----
            "abrir": self.open_application,
            "abre": self.open_application,
            "iniciar": self.open_application,
            "cerrar": self.close_application,
            "cierra": self.close_application,
            "discord": self.open_discord,

            # ---- SISTEMA ----
            "reiniciar": self.restart_system,
            "reinicia": self.restart_system,
            "apagar": self.shutdown_system,
            "apaga": self.shutdown_system,
            "cancelar apagado": self.cancel_shutdown,
            "cancelar reinicio": self.cancel_shutdown,

            # ---- INFORMACION ----
            "hora": self.tell_time,
            "que hora": self.tell_time,
            "dime la hora": self.tell_time,
            "fecha": self.tell_date,
            "que dia": self.tell_date,
            "dime la fecha": self.tell_date,
            "sistema": self.system_info,
            "estado del sistema": self.system_info,
            "ip": self.get_ip,
            "direccion ip": self.get_ip,
            "mi ip": self.get_ip,
            "procesos": self.list_processes,
            "que esta consumiendo": self.list_processes,

            # ---- WEB ----
            "buscar": self.search_web,
            "busca": self.search_web,
            "google": self.search_web,
            "navegar": self.open_website,
            "abrir web": self.open_website,
            "ir a": self.open_website,
            "youtube": self.open_youtube,
            "github": self.open_github,

            # ---- ARCHIVOS ----
            "crear carpeta": self.create_folder,
            "nueva carpeta": self.create_folder,
            "nota": self.create_note,
            "apunta": self.create_note,
            "anota": self.create_note,
            "recordatorio": self.set_reminder,
            "recordarme": self.set_reminder,
            "listar archivos": self.list_files,
            "archivos del escritorio": self.list_files,
            "buscar notas": self.search_notes_skill,
            "leer notas": self.read_notes_skill,
            "eliminar nota": self.delete_note_skill,
            "recordatorios pendientes": self.pending_reminders_skill,
            "completar recordatorio": self.complete_reminder_skill,
            "estadisticas": self.stats_skill,

            # ---- VOLUMEN ----
            "volumen": self.set_volume,
            "pon volumen": self.set_volume,
            "cambiar volumen": self.set_volume,
            "sube volumen": self.volume_up,
            "subir volumen": self.volume_up,
            "mas volumen": self.volume_up,
            "baja volumen": self.volume_down,
            "bajar volumen": self.volume_down,
            "menos volumen": self.volume_down,
            "silencio": self.mute_volume,
            "silenciar": self.mute_volume,
            "mutear": self.mute_volume,
            "quitar silencio": self.mute_volume,

            # ---- MULTIMEDIA ----
            "musica": self.play_music,
            "spotify": self.play_music,
            "siguiente": self.next_track,
            "siguiente cancion": self.next_track,
            "pausa": self.pause_media,
            "pausar": self.pause_media,
            "reanudar": self.resume_media,
            "play": self.resume_media,

            # ---- CAPTURA ----
            "captura": self.screenshot,
            "capturar pantalla": self.screenshot,
            "pantallazo": self.screenshot,

            # ---- TEMPORIZADORES ----
            "temporizador": self.set_timer_skill,
            "alarma": self.set_alarm_skill,
            "avisame en": self.set_timer_skill,
            "despertador": self.set_alarm_skill,
            "cancelar temporizador": self.cancel_timer_skill,
            "cancelar alarma": self.cancel_alarm_skill,
            "temporizadores activos": self.list_timers_skill,
            "alarmas programadas": self.list_alarms_skill,

            # ---- CONFIGURACION ----
            "auto inicio": self.toggle_startup,
            "iniciar con windows": self.toggle_startup,
            "auto arranque": self.toggle_startup,

            # ---- FRASES ----
            "dato curioso": self.random_quote,
            "dime algo": self.random_quote,
            "cuentame algo": self.random_quote,
            "frase del dia": self.random_quote,

            # ---- CALCULADORA ----
            "calcula": self.calculate_skill,
            "calculame": self.calculate_skill,
            "cuanto es": self.calculate_skill,
            "resuelve": self.calculate_skill,

            # ---- CONVERSOR ----
            "convierte": self.convert_skill,
            "convertir": self.convert_skill,
            "conversion": self.convert_skill,
            "pasa": self.convert_skill,
            "cuantos son": self.convert_skill,

            # ---- NOTICIAS ----
            "noticias": self.read_news_skill,
            "noticias de": self.read_news_skill,
            "lee las noticias": self.read_news_skill,
            "categorias noticias": self.news_categories_skill,

            # ---- VENTANA ACTIVA ----
            "donde estoy": self.where_am_i_skill,
            "que aplicacion": self.where_am_i_skill,
            "ventana activa": self.where_am_i_skill,
            "estoy programando": self.am_i_coding_skill,
            "estoy escuchando musica": self.am_i_listening_skill,

            # ---- DESARROLLADOR ----
            "abrir proyecto": self.open_project_skill,
            "nuevo proyecto": self.new_project_skill,
            "crear proyecto": self.new_project_skill,
            "lista proyectos": self.list_projects_skill,
            "listar proyectos": self.list_projects_skill,
            "ejecutar script": self.run_script_skill,
            "correr script": self.run_script_skill,
            "git": self.git_skill,
            "terminal desarrollador": self.dev_terminal_skill,
        }

        logger.info(f"Nivel 2 - Skills inicializado ({len(self.skills)} comandos)")

    def execute(self, command_text: str) -> Dict[str, Any]:
        if not command_text:
            return {'success': False, 'response': 'No entendi el comando', 'action': 'unknown'}

        command_lower = command_text.lower().strip()
        sorted_skills = sorted(self.skills.items(), key=lambda x: len(x[0]), reverse=True)

        for keyword, skill_func in sorted_skills:
            if command_lower.startswith(keyword) or f" {keyword} " in f" {command_lower} ":
                try:
                    result = skill_func(command_text)
                    self.mqtt.publish('command', {
                        'command': command_text,
                        'action': result.get('action', keyword),
                        'success': result.get('success', False),
                        'response': result.get('response', '')
                    })
                    return result
                except Exception as e:
                    logger.error(f"Error en '{keyword}': {e}")
                    return {'success': False, 'response': f"Error: {e}", 'action': keyword}

        return {'success': False, 'response': None, 'action': 'unknown'}

    def add_skill(self, keyword: str, func):
        self.skills[keyword.lower()] = func

    # ==========================================
    # APLICACIONES
    # ==========================================

    def open_application(self, command: str) -> Dict[str, Any]:
        apps = {
            "navegador": "start chrome", "chrome": "start chrome",
            "firefox": "start firefox", "edge": "start msedge",
            "calculadora": "calc", "bloc de notas": "notepad",
            "notepad": "notepad", "terminal": "wt", "cmd": "start cmd",
            "powershell": "start powershell", "explorador": "explorer",
            "configuracion": "start ms-settings:", "administrador de tareas": "taskmgr",
            "word": "start winword", "excel": "start excel",
            "powerpoint": "start powerpnt", "vscode": "code",
            "discord": "start discord", "whatsapp": "start whatsapp",
            "spotify": "start spotify", "tienda": "start ms-windows-store:",
            "paint": "mspaint", "correo": "start outlookmail:",
        }

        command_lower = command.lower()

        for app_name, app_cmd in apps.items():
            if app_name in command_lower:
                try:
                    subprocess.Popen(app_cmd, shell=True)
                    return {'success': True, 'response': f"Abriendo {app_name}", 'action': 'open_app'}
                except:
                    return {'success': False, 'response': f"No pude abrir {app_name}", 'action': 'open_app'}

        return {'success': False, 'response': "No encontre esa aplicacion", 'action': 'open_app'}

    def open_discord(self, command: str = "") -> Dict[str, Any]:
        subprocess.Popen("start discord", shell=True)
        return {'success': True, 'response': "Abriendo Discord, señor", 'action': 'open_discord'}

    def close_application(self, command: str) -> Dict[str, Any]:
        app_processes = {
            "chrome": "chrome.exe", "navegador": "chrome.exe",
            "firefox": "firefox.exe", "edge": "msedge.exe",
            "notepad": "notepad.exe", "bloc de notas": "notepad.exe",
            "spotify": "spotify.exe", "discord": "discord.exe",
            "calculadora": "calculator.exe", "terminal": "WindowsTerminal.exe",
            "word": "winword.exe", "excel": "excel.exe",
            "powerpoint": "powerpnt.exe", "explorador": "explorer.exe",
            "whatsapp": "whatsapp.exe",
        }

        command_lower = command.lower()

        for app_name, process_name in app_processes.items():
            if app_name in command_lower:
                result = os.system(f"taskkill /f /im {process_name} 2>nul")
                if result == 0:
                    return {'success': True, 'response': f"{app_name} cerrado", 'action': 'close_app'}
                return {'success': True, 'response': f"{app_name} no estaba abierto", 'action': 'close_app'}

        return {'success': False, 'response': "No pude identificar que cerrar", 'action': 'close_app'}

    # ==========================================
    # SISTEMA
    # ==========================================

    def shutdown_system(self, command: str) -> Dict[str, Any]:
        os.system("shutdown /s /t 30")
        return {'success': True, 'response': "Apagando en 30 segundos. Di 'cancelar apagado' para detener.", 'action': 'shutdown'}

    def restart_system(self, command: str) -> Dict[str, Any]:
        os.system("shutdown /r /t 30")
        return {'success': True, 'response': "Reiniciando en 30 segundos. Di 'cancelar reinicio' para detener.", 'action': 'restart'}

    def cancel_shutdown(self, command: str) -> Dict[str, Any]:
        os.system("shutdown /a")
        return {'success': True, 'response': "Apagado/reinicio cancelado", 'action': 'cancel_shutdown'}

    # ==========================================
    # INFORMACION
    # ==========================================

    def tell_time(self, command: str) -> Dict[str, Any]:
        now = datetime.now()
        return {'success': True, 'response': f"Son las {now.strftime('%H:%M')}", 'action': 'time'}

    def tell_date(self, command: str) -> Dict[str, Any]:
        now = datetime.now()
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return {'success': True, 'response': f"Hoy es {dias[now.weekday()]} {now.day} de {meses[now.month-1]} de {now.year}", 'action': 'date'}

    def system_info(self, command: str) -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:')
        info = f"CPU: {cpu}% | RAM: {ram.percent}% | Disco: {disk.percent}%"
        return {'success': True, 'response': info, 'action': 'sysinfo'}

    def get_ip(self, command: str) -> Dict[str, Any]:
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return {'success': True, 'response': f"Mi IP local es {ip}", 'action': 'ip'}
        except:
            return {'success': False, 'response': "No pude obtener la IP", 'action': 'ip'}

    def list_processes(self, command: str) -> Dict[str, Any]:
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        processes.sort(key=lambda x: x['cpu_percent'] if x['cpu_percent'] else 0, reverse=True)
        top_5 = processes[:5]
        info = "Top 5: " + ", ".join([f"{p['name']} ({p['cpu_percent']:.1f}%)" for p in top_5])
        return {'success': True, 'response': info, 'action': 'processes'}

    # ==========================================
    # WEB
    # ==========================================

    def open_website(self, command: str) -> Dict[str, Any]:
        url = command
        for prefix in ["navegar", "abrir web", "ir a"]:
            url = url.replace(prefix, "")
        url = url.strip()
        if not url.startswith("http"):
            url = f"https://{url}"
        webbrowser.open(url)
        return {'success': True, 'response': f"Abriendo {url}", 'action': 'web'}

    def search_web(self, command: str) -> Dict[str, Any]:
        query = command.replace("buscar", "").replace("busca", "").replace("google", "").strip()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return {'success': True, 'response': f"Buscando '{query}'", 'action': 'search'}
        return {'success': False, 'response': "Que quieres que busque?", 'action': 'search'}

    def open_youtube(self, command: str) -> Dict[str, Any]:
        query = command.replace("youtube", "").strip()
        if query:
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return {'success': True, 'response': f"Buscando en YouTube", 'action': 'youtube'}
        webbrowser.open("https://www.youtube.com")
        return {'success': True, 'response': "Abriendo YouTube", 'action': 'youtube'}

    def open_github(self, command: str) -> Dict[str, Any]:
        query = command.replace("github", "").strip()
        if query:
            webbrowser.open(f"https://github.com/search?q={query}")
            return {'success': True, 'response': f"Buscando en GitHub", 'action': 'github'}
        webbrowser.open("https://github.com")
        return {'success': True, 'response': "Abriendo GitHub", 'action': 'github'}

    # ==========================================
    # ARCHIVOS
    # ==========================================

    def create_folder(self, command: str) -> Dict[str, Any]:
        folder_name = command.replace("crear carpeta", "").replace("nueva carpeta", "").strip()
        if not folder_name:
            return {'success': False, 'response': "Necesito un nombre", 'action': 'create_folder'}
        desktop = os.path.expanduser("~/Desktop")
        folder_path = os.path.join(desktop, folder_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
            return {'success': True, 'response': f"Carpeta creada: {folder_name}", 'action': 'create_folder'}
        except Exception as e:
            return {'success': False, 'response': f"Error: {e}", 'action': 'create_folder'}

    def create_note(self, command: str) -> Dict[str, Any]:
        note_text = command.replace("nota", "").replace("apunta", "").replace("anota", "").strip()
        if not note_text:
            return {'success': False, 'response': "Que quieres que apunte?", 'action': 'note'}
        note_id = self.db.add_note(note_text)
        return {'success': True, 'response': f"Nota {note_id} guardada", 'action': 'note'}

    def set_reminder(self, command: str) -> Dict[str, Any]:
        reminder_text = command.replace("recordatorio", "").replace("recordarme", "").strip()
        if not reminder_text:
            return {'success': False, 'response': "Que quieres que te recuerde?", 'action': 'reminder'}
        reminder_id = self.db.add_reminder(reminder_text)
        return {'success': True, 'response': f"Recordatorio {reminder_id} guardado", 'action': 'reminder'}

    def list_files(self, command: str) -> Dict[str, Any]:
        target = os.path.expanduser("~/Desktop")
        if "documentos" in command.lower():
            target = os.path.expanduser("~/Documents")
        elif "descargas" in command.lower():
            target = os.path.expanduser("~/Downloads")
        try:
            files = os.listdir(target)
            return {'success': True, 'response': f"Hay {len(files)} archivos en la carpeta", 'action': 'list_files'}
        except:
            return {'success': False, 'response': "No pude listar los archivos", 'action': 'list_files'}

    def search_notes_skill(self, command: str) -> Dict[str, Any]:
        query = command.replace("buscar notas", "").strip()
        notes = self.db.search_notes(query)
        if not notes:
            return {'success': True, 'response': "No encontre notas", 'action': 'search_notes'}
        response = "Notas: " + ", ".join([f"{n['id']}: {n['text'][:50]}" for n in notes[:5]])
        return {'success': True, 'response': response, 'action': 'search_notes'}

    def read_notes_skill(self, command: str) -> Dict[str, Any]:
        notes = self.db.get_notes(5)
        if not notes:
            return {'success': True, 'response': "No hay notas", 'action': 'read_notes'}
        response = "Notas: " + ", ".join([f"{n['id']}: {n['text'][:60]}" for n in notes])
        return {'success': True, 'response': response, 'action': 'read_notes'}

    def delete_note_skill(self, command: str) -> Dict[str, Any]:
        numbers = re.findall(r'\d+', command)
        if not numbers:
            return {'success': False, 'response': "Di el numero de nota", 'action': 'delete_note'}
        note_id = int(numbers[0])
        if self.db.delete_note(note_id):
            return {'success': True, 'response': f"Nota {note_id} eliminada", 'action': 'delete_note'}
        return {'success': False, 'response': f"No encontre la nota {note_id}", 'action': 'delete_note'}

    def pending_reminders_skill(self, command: str) -> Dict[str, Any]:
        reminders = self.db.get_reminders()
        if not reminders:
            return {'success': True, 'response': "No hay recordatorios pendientes", 'action': 'reminders'}
        response = "Pendientes: " + ", ".join([f"{r['id']}: {r['text'][:50]}" for r in reminders])
        return {'success': True, 'response': response, 'action': 'reminders'}

    def complete_reminder_skill(self, command: str) -> Dict[str, Any]:
        numbers = re.findall(r'\d+', command)
        if not numbers:
            return {'success': False, 'response': "Di el numero de recordatorio", 'action': 'complete_reminder'}
        reminder_id = int(numbers[0])
        if self.db.mark_reminder_done(reminder_id):
            return {'success': True, 'response': f"Recordatorio {reminder_id} completado", 'action': 'complete_reminder'}
        return {'success': False, 'response': f"No encontre el recordatorio {reminder_id}", 'action': 'complete_reminder'}

    def stats_skill(self, command: str) -> Dict[str, Any]:
        stats = self.db.get_stats()
        response = f"Comandos: {stats['total_commands']}. Exitosos: {stats['success_commands']}. Notas: {stats['total_notes']}. Pendientes: {stats['pending_reminders']}."
        return {'success': True, 'response': response, 'action': 'stats'}

    # ==========================================
    # VOLUMEN
    # ==========================================

    def set_volume(self, command: str) -> Dict[str, Any]:
        numbers = re.findall(r'\d+', command)
        if numbers:
            level = max(0, min(100, int(numbers[0])))
            ps_script = f"""
            Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {{
                int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
            }}
            [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDevice {{
                int Activate(ref Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
            }}
            [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IMMDeviceEnumerator {{
                int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
            }}
            [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject {{ }}
            public class Audio {{
                public static void SetVolume(float level) {{
                    var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
                    IMMDevice dev = null;
                    enumerator.GetDefaultAudioEndpoint(0, 1, out dev);
                    IAudioEndpointVolume epv = null;
                    var epvid = typeof(IAudioEndpointVolume).GUID;
                    dev.Activate(ref epvid, 23, 0, out epv);
                    epv.SetMasterVolumeLevelScalar(level / 100.0f, Guid.Empty);
                }}
            }}
"@
            [Audio]::SetVolume({level})
            """
            with open("_temp_volume.ps1", "w") as f:
                f.write(ps_script)
            os.system("powershell -ExecutionPolicy Bypass -File _temp_volume.ps1")
            os.remove("_temp_volume.ps1")
            return {'success': True, 'response': f"Volumen: {level}%", 'action': 'volume'}
        return {'success': False, 'response': "Di un nivel del 0 al 100", 'action': 'volume'}

    def volume_up(self, command: str) -> Dict[str, Any]:
        for _ in range(2):
            os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"')
        return {'success': True, 'response': "Volumen arriba", 'action': 'volume_up'}

    def volume_down(self, command: str) -> Dict[str, Any]:
        for _ in range(2):
            os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"')
        return {'success': True, 'response': "Volumen abajo", 'action': 'volume_down'}

    def mute_volume(self, command: str) -> Dict[str, Any]:
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"')
        return {'success': True, 'response': "Sonido activado/desactivado", 'action': 'mute'}

    # ==========================================
    # MULTIMEDIA
    # ==========================================

    def play_music(self, command: str) -> Dict[str, Any]:
        try:
            subprocess.Popen("start spotify", shell=True)
            return {'success': True, 'response': "Abriendo Spotify", 'action': 'music'}
        except:
            return {'success': True, 'response': "No pude abrir Spotify", 'action': 'music'}

    def next_track(self, command: str) -> Dict[str, Any]:
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"')
        return {'success': True, 'response': "Siguiente", 'action': 'next_track'}

    def pause_media(self, command: str) -> Dict[str, Any]:
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"')
        return {'success': True, 'response': "Pausado", 'action': 'pause'}

    def resume_media(self, command: str) -> Dict[str, Any]:
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"')
        return {'success': True, 'response': "Reproduciendo", 'action': 'resume'}

    # ==========================================
    # CAPTURA
    # ==========================================

    def screenshot(self, command: str) -> Dict[str, Any]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.expanduser("~/Desktop")
        filepath = os.path.join(desktop, f"screenshot_{timestamp}.png")
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen(0, 0, 0, 0, $bitmap.Size)
        $bitmap.Save('{filepath}')
        $graphics.Dispose()
        $bitmap.Dispose()
        """
        with open("_temp_screenshot.ps1", "w") as f:
            f.write(ps_script)
        os.system("powershell -ExecutionPolicy Bypass -File _temp_screenshot.ps1")
        os.remove("_temp_screenshot.ps1")
        return {'success': True, 'response': "Captura guardada", 'action': 'screenshot'}

    # ==========================================
    # TEMPORIZADORES (usa self.timer_manager inyectado)
    # ==========================================

    def set_timer_skill(self, command: str) -> Dict[str, Any]:
        if not self.timer_manager:
            from core.timers import TimerManager
            self.timer_manager = TimerManager()
        seconds = self.timer_manager.parse_time(command)
        if not seconds:
            return {'success': False, 'response': "No entendi el tiempo", 'action': 'timer'}
        response = self.timer_manager.set_timer(seconds)
        return {'success': True, 'response': response, 'action': 'timer'}

    def set_alarm_skill(self, command: str) -> Dict[str, Any]:
        if not self.timer_manager:
            from core.timers import TimerManager
            self.timer_manager = TimerManager()
        time_tuple = self.timer_manager.parse_alarm_time(command)
        if not time_tuple:
            return {'success': False, 'response': "No entendi la hora", 'action': 'alarm'}
        hour, minute = time_tuple
        response = self.timer_manager.set_alarm(hour, minute)
        return {'success': True, 'response': response, 'action': 'alarm'}

    def cancel_timer_skill(self, command: str) -> Dict[str, Any]:
        if not self.timer_manager:
            return {'success': False, 'response': "No hay temporizadores activos", 'action': 'cancel_timer'}
        response = self.timer_manager.cancel_timer()
        return {'success': True, 'response': response, 'action': 'cancel_timer'}

    def cancel_alarm_skill(self, command: str) -> Dict[str, Any]:
        if not self.timer_manager:
            return {'success': False, 'response': "No hay alarmas programadas", 'action': 'cancel_alarm'}
        response = self.timer_manager.cancel_alarm()
        return {'success': True, 'response': response, 'action': 'cancel_alarm'}

    def list_timers_skill(self, command: str) -> Dict[str, Any]:
        if not self.timer_manager:
            return {'success': True, 'response': "No hay temporizadores activos", 'action': 'list_timers'}
        response = self.timer_manager.list_timers()
        return {'success': True, 'response': response, 'action': 'list_timers'}

    def list_alarms_skill(self, command: str) -> Dict[str, Any]:
        if not self.timer_manager:
            return {'success': True, 'response': "No hay alarmas programadas", 'action': 'list_alarms'}
        response = self.timer_manager.list_alarms()
        return {'success': True, 'response': response, 'action': 'list_alarms'}

    # ==========================================
    # CONFIGURACION
    # ==========================================

    def toggle_startup(self, command: str) -> Dict[str, Any]:
        from core.startup import StartupManager
        startup = StartupManager()
        response = startup.toggle()
        return {'success': True, 'response': response, 'action': 'startup'}

    # ==========================================
    # FRASES
    # ==========================================

    def random_quote(self, command: str) -> Dict[str, Any]:
        response = self.quotes.get_random_fact()
        return {'success': True, 'response': response, 'action': 'quote'}

    # ==========================================
    # CALCULADORA
    # ==========================================

    def calculate_skill(self, command: str) -> Dict[str, Any]:
        from core.calculator import Calculator
        calc = Calculator()
        response = calc.parse_and_calculate(command)
        return {'success': True, 'response': response, 'action': 'calculate'}

    # ==========================================
    # CONVERSOR
    # ==========================================

    def convert_skill(self, command: str) -> Dict[str, Any]:
        from core.converter import UnitConverter
        conv = UnitConverter()
        response = conv.parse_and_convert(command)
        return {'success': True, 'response': response, 'action': 'convert'}

    # ==========================================
    # NOTICIAS
    # ==========================================

    def read_news_skill(self, command: str) -> Dict[str, Any]:
        from core.news import NewsReader
        news = NewsReader()
        command_lower = command.lower()
        for category in news.feeds.keys():
            if category in command_lower:
                response = news.format_for_speech(category)
                return {'success': True, 'response': response, 'action': 'news'}
        response = news.format_for_speech("nacional")
        return {'success': True, 'response': response, 'action': 'news'}

    def news_categories_skill(self, command: str) -> Dict[str, Any]:
        from core.news import NewsReader
        news = NewsReader()
        response = news.list_categories()
        return {'success': True, 'response': response, 'action': 'news_categories'}

    # ==========================================
    # VENTANA ACTIVA
    # ==========================================

    def where_am_i_skill(self, command: str) -> Dict[str, Any]:
        from core.window_tracker import WindowTracker
        tracker = WindowTracker()
        app = tracker.get_current_app()
        if app and app != "Desconocido":
            return {'success': True, 'response': f"Estas en {app}. {tracker.get_context()}", 'action': 'window_info'}
        return {'success': True, 'response': "No puedo identificar la aplicacion actual", 'action': 'window_info'}

    def am_i_coding_skill(self, command: str) -> Dict[str, Any]:
        from core.window_tracker import WindowTracker
        tracker = WindowTracker()
        if tracker.is_coding():
            return {'success': True, 'response': "Si, estas programando. Sigue asi, señor.", 'action': 'coding_check'}
        return {'success': True, 'response': "No, no parece que estes programando ahora.", 'action': 'coding_check'}

    def am_i_listening_skill(self, command: str) -> Dict[str, Any]:
        from core.window_tracker import WindowTracker
        tracker = WindowTracker()
        if tracker.is_listening_music():
            return {'success': True, 'response': "Si, estas en Spotify. Disfruta de la musica, señor.", 'action': 'music_check'}
        return {'success': True, 'response': "No estas escuchando musica ahora.", 'action': 'music_check'}

    # ==========================================
    # DESARROLLADOR
    # ==========================================

    def open_project_skill(self, command: str) -> Dict[str, Any]:
        """Abre un proyecto en VS Code"""
        from core.developer import DeveloperMode
        dev = DeveloperMode()
        project_name = command.replace("abrir proyecto", "").strip()
        if not project_name:
            return {'success': False, 'response': "Di el nombre del proyecto", 'action': 'open_project'}
        result = dev.open_project(project_name)
        return result

    def new_project_skill(self, command: str) -> Dict[str, Any]:
        """Crea un nuevo proyecto"""
        from core.developer import DeveloperMode
        dev = DeveloperMode()

        project_name = command.replace("nuevo proyecto", "").replace("crear proyecto", "").strip()

        if not project_name:
            return {'success': False, 'response': "Di el nombre del proyecto", 'action': 'new_project'}

        project_type = "python"
        if "web" in command.lower() or "html" in command.lower():
            project_type = "web"
        elif "react" in command.lower():
            project_type = "react"

        result = dev.new_project(project_name, project_type)
        return result

    def list_projects_skill(self, command: str) -> Dict[str, Any]:
        """Lista proyectos disponibles"""
        from core.developer import DeveloperMode
        dev = DeveloperMode()
        result = dev.list_projects()
        return result

    def run_script_skill(self, command: str) -> Dict[str, Any]:
        """Ejecuta un script de Python"""
        from core.developer import DeveloperMode
        dev = DeveloperMode()
        script_name = command.replace("ejecutar script", "").replace("correr script", "").strip()
        if not script_name:
            return {'success': False, 'response': "Di el nombre del script", 'action': 'run_script'}
        result = dev.run_script(script_name)
        return result

    def git_skill(self, command: str) -> Dict[str, Any]:
        """Ejecuta comandos de Git"""
        from core.developer import DeveloperMode
        dev = DeveloperMode()
        result = dev.git_command(command)
        return result

    def dev_terminal_skill(self, command: str) -> Dict[str, Any]:
        """Abre terminal de desarrollador"""
        from core.developer import DeveloperMode
        dev = DeveloperMode()
        result = dev.open_terminal()
        return result