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

logger = logging.getLogger("JARVIS.Skills")

class SkillManager:
    """
    Nivel 2: Las Manos
    Ejecuta acciones en Windows.
    """
    
    def __init__(self, mqtt_handler: Optional[MQTTHandler] = None, config_path: str = "config.yaml"):
        import yaml
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.mqtt = mqtt_handler if mqtt_handler else MQTTHandler(config_path)
        if not mqtt_handler:
            self.mqtt.connect()
        
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
            "cancelar temporizador":self.cancel_timer_skill,
            "cancelar alarma":self.cancel_alarm_skill,
            "temporizadores activos":self.list_timer_skill,
            "alarmas programadas":self.list_alarm_skill,

            # ---- CONFIGURACION ----
            "auto inicio": self.toggle_startup,
            "iniciar con windows": self.toggle_startup,
            "auto arranque": self.toggle_startup,
        }
        
        logger.info(f"Nivel 2 - Skills inicializado ({len(self.skills)} comandos disponibles)")
    
    def execute(self, command_text: str) -> Dict[str, Any]:
        """
        Intenta ejecutar un comando.
        Retorna: {'success': bool, 'response': str, 'action': str}
        """
        if not command_text:
            return {
                'success': False,
                'response': 'No entendi el comando',
                'action': 'unknown'
            }
        
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
                    logger.error(f"Error ejecutando '{keyword}': {e}")
                    return {
                        'success': False,
                        'response': f"Error al ejecutar la accion: {str(e)}",
                        'action': keyword
                    }
        
        return {
            'success': False,
            'response': None,
            'action': 'unknown'
        }
    
    def add_skill(self, keyword: str, func):
        """Anade una nueva skill dinamicamente"""
        self.skills[keyword.lower()] = func
        logger.info(f"Nueva skill registrada: {keyword}")
    
    # ==========================================
    # APLICACIONES
    # ==========================================
    
    def open_application(self, command: str) -> Dict[str, Any]:
        """Abre aplicaciones de Windows"""
        apps = {
            "navegador": "start chrome",
            "chrome": "start chrome",
            "firefox": "start firefox",
            "edge": "start msedge",
            "brave": "start brave",
            "calculadora": "calc",
            "bloc de notas": "notepad",
            "notepad": "notepad",
            "terminal": "wt",
            "cmd": "start cmd",
            "powershell": "start powershell",
            "explorador": "explorer",
            "explorador de archivos": "explorer",
            "configuracion": "start ms-settings:",
            "administrador de tareas": "taskmgr",
            "word": "start winword",
            "excel": "start excel",
            "powerpoint": "start powerpnt",
            "visual studio code": "code",
            "vscode": "code",
            "discord": "start discord",
            "whatsapp": "start whatsapp",
            "spotify": "start spotify",
            "tienda": "start ms-windows-store:",
            "paint": "mspaint",
            "correo": "start outlookmail:",
        }
        
        command_lower = command.lower()
        
        for app_name, app_cmd in apps.items():
            if app_name in command_lower:
                try:
                    subprocess.Popen(app_cmd, shell=True)
                    return {
                        'success': True,
                        'response': f"Abriendo {app_name}",
                        'action': 'open_app'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'response': f"No pude abrir {app_name}",
                        'action': 'open_app'
                    }
        
        app_name = command.replace("abrir ", "").replace("abre ", "").replace("iniciar ", "").strip()
        if app_name:
            try:
                subprocess.Popen(f"start {app_name}", shell=True)
                return {
                    'success': True,
                    'response': f"Intentando abrir {app_name}",
                    'action': 'open_app'
                }
            except:
                pass
        
        return {
            'success': False,
            'response': "No encontre esa aplicacion",
            'action': 'open_app'
        }
    
    def open_discord(self, command: str = "") -> Dict[str, Any]:
        """Abre Discord"""
        subprocess.Popen("start discord", shell=True)
        return {
            'success': True,
            'response': "Abriendo Discord, senor",
            'action': 'open_discord'
        }
    
    def close_application(self, command: str) -> Dict[str, Any]:
        """Cierra aplicaciones por nombre"""
        app_processes = {
            "chrome": "chrome.exe",
            "navegador": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "brave": "brave.exe",
            "notepad": "notepad.exe",
            "bloc de notas": "notepad.exe",
            "spotify": "spotify.exe",
            "discord": "discord.exe",
            "calculadora": "calculator.exe",
            "terminal": "WindowsTerminal.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "explorador": "explorer.exe",
            "whatsapp": "whatsapp.exe",
            "teams": "teams.exe",
        }
        
        command_lower = command.lower()
        
        for app_name, process_name in app_processes.items():
            if app_name in command_lower:
                result = os.system(f"taskkill /f /im {process_name} 2>nul")
                if result == 0:
                    return {
                        'success': True,
                        'response': f"{app_name} cerrado",
                        'action': 'close_app'
                    }
                else:
                    return {
                        'success': True,
                        'response': f"{app_name} no estaba abierto",
                        'action': 'close_app'
                    }
        
        return {
            'success': False,
            'response': "No pude identificar que aplicacion cerrar",
            'action': 'close_app'
        }
    
    # ==========================================
    # SISTEMA
    # ==========================================
    
    def shutdown_system(self, command: str) -> Dict[str, Any]:
        """Apaga el sistema con cuenta regresiva de 30 segundos"""
        os.system("shutdown /s /t 30")
        return {
            'success': True,
            'response': "Apagando el sistema en 30 segundos. Di 'cancelar apagado' para detener.",
            'action': 'shutdown'
        }
    
    def restart_system(self, command: str) -> Dict[str, Any]:
        """Reinicia el sistema con cuenta regresiva de 30 segundos"""
        os.system("shutdown /r /t 30")
        return {
            'success': True,
            'response': "Reiniciando en 30 segundos. Di 'cancelar reinicio' para detener.",
            'action': 'restart'
        }
    
    def cancel_shutdown(self, command: str) -> Dict[str, Any]:
        """Cancela apagado o reinicio programado"""
        os.system("shutdown /a")
        return {
            'success': True,
            'response': "Apagado/reinicio cancelado",
            'action': 'cancel_shutdown'
        }
    
    # ==========================================
    # INFORMACION
    # ==========================================
    
    def tell_time(self, command: str) -> Dict[str, Any]:
        """Dice la hora actual"""
        now = datetime.now()
        hora = now.strftime("%H:%M")
        
        return {
            'success': True,
            'response': f"Son las {hora}",
            'action': 'time'
        }
    
    def tell_date(self, command: str) -> Dict[str, Any]:
        """Dice la fecha actual en espanol"""
        now = datetime.now()
        
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        
        dia_semana = dias[now.weekday()]
        dia = now.day
        mes = meses[now.month - 1]
        año = now.year
        
        return {
            'success': True,
            'response': f"Hoy es {dia_semana} {dia} de {mes} de {año}",
            'action': 'date'
        }
    
    def system_info(self, command: str) -> Dict[str, Any]:
        """Informacion del sistema"""
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:')
        
        info_parts = []
        
        if "cpu" in command.lower() or "procesador" in command.lower():
            info_parts.append(f"CPU al {cpu}%")
        elif "ram" in command.lower() or "memoria" in command.lower():
            info_parts.append(f"RAM: {ram.percent}% usada ({ram.used // (1024**3)}GB de {ram.total // (1024**3)}GB)")
        elif "disco" in command.lower() or "almacenamiento" in command.lower():
            info_parts.append(f"Disco C: {disk.percent}% usado ({disk.used // (1024**3)}GB de {disk.total // (1024**3)}GB)")
        else:
            info_parts.append(f"CPU: {cpu}%")
            info_parts.append(f"RAM: {ram.percent}%")
            info_parts.append(f"Disco: {disk.percent}%")
        
        return {
            'success': True,
            'response': " | ".join(info_parts),
            'action': 'sysinfo'
        }
    
    def get_ip(self, command: str) -> Dict[str, Any]:
        """Obtiene la IP local"""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return {
                'success': True,
                'response': f"Mi IP local es {ip}",
                'action': 'ip'
            }
        except:
            return {
                'success': False,
                'response': "No pude obtener la IP",
                'action': 'ip'
            }
    
    def list_processes(self, command: str) -> Dict[str, Any]:
        """Lista los procesos que mas consumen"""
        processes = []
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        
        processes.sort(key=lambda x: x['cpu_percent'] if x['cpu_percent'] else 0, reverse=True)
        top_5 = processes[:5]
        
        info = "Top 5 procesos: "
        for p in top_5:
            info += f"{p['name']} ({p['cpu_percent']:.1f}%), "
        
        return {
            'success': True,
            'response': info.strip(', '),
            'action': 'processes'
        }
    
    # ==========================================
    # WEB
    # ==========================================
    
    def open_website(self, command: str) -> Dict[str, Any]:
        """Abre una pagina web"""
        url = command
        for prefix in ["navegar", "abrir web", "abre", "ir a"]:
            url = url.replace(prefix, "")
        url = url.strip()
        
        if not url.startswith("http"):
            url = f"https://{url}"
        
        webbrowser.open(url)
        return {
            'success': True,
            'response': f"Abriendo {url}",
            'action': 'web'
        }
    
    def search_web(self, command: str) -> Dict[str, Any]:
        """Busca en Google"""
        query = command
        for prefix in ["buscar", "busca", "google", "busca en google"]:
            query = query.replace(prefix, "")
        query = query.strip()
        
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return {
                'success': True,
                'response': f"Buscando '{query}'",
                'action': 'search'
            }
        return {
            'success': False,
            'response': "Que quieres que busque?",
            'action': 'search'
        }
    
    def open_youtube(self, command: str) -> Dict[str, Any]:
        """Busca en YouTube"""
        query = command.replace("youtube", "").strip()
        
        if query:
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return {
                'success': True,
                'response': f"Buscando '{query}' en YouTube",
                'action': 'youtube'
            }
        else:
            webbrowser.open("https://www.youtube.com")
            return {
                'success': True,
                'response': "Abriendo YouTube",
                'action': 'youtube'
            }
    
    def open_github(self, command: str) -> Dict[str, Any]:
        """Abre GitHub"""
        query = command.replace("github", "").strip()
        
        if query:
            webbrowser.open(f"https://github.com/search?q={query}")
            return {
                'success': True,
                'response': f"Buscando '{query}' en GitHub",
                'action': 'github'
            }
        else:
            webbrowser.open("https://github.com")
            return {
                'success': True,
                'response': "Abriendo GitHub",
                'action': 'github'
            }
    
    # ==========================================
    # ARCHIVOS
    # ==========================================
    
    def create_folder(self, command: str) -> Dict[str, Any]:
        """Crea una carpeta en el escritorio"""
        folder_name = command.replace("crear carpeta", "").replace("nueva carpeta", "").strip()
        
        if not folder_name:
            return {
                'success': False,
                'response': "Necesito un nombre para la carpeta",
                'action': 'create_folder'
            }
        
        desktop = os.path.expanduser("~/Desktop")
        folder_path = os.path.join(desktop, folder_name)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            return {
                'success': True,
                'response': f"Carpeta '{folder_name}' creada en el escritorio",
                'action': 'create_folder'
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"No pude crear la carpeta: {e}",
                'action': 'create_folder'
            }
    
    def create_note(self, command: str) -> Dict[str, Any]:
        """Crea una nota rapida en el escritorio"""
        note_text = command.replace("nota", "").replace("apunta", "").replace("anota", "").strip()
        
        if not note_text:
            return {
                'success': False,
                'response': "Que quieres que apunte?",
                'action': 'note'
            }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.expanduser("~/Desktop")
        note_path = os.path.join(desktop, f"nota_jarvis_{timestamp}.txt")
        
        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(f"Nota de JARVIS\n")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write("-" * 40 + "\n")
                f.write(note_text)
            
            os.startfile(note_path)
            
            return {
                'success': True,
                'response': "Nota creada y abierta",
                'action': 'note'
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Error al crear la nota: {e}",
                'action': 'note'
            }
    
    def set_reminder(self, command: str) -> Dict[str, Any]:
        """Guarda un recordatorio"""
        reminder_text = command.replace("recordatorio", "").replace("recordarme", "").strip()
        
        if not reminder_text:
            return {
                'success': False,
                'response': "Que quieres que te recuerde?",
                'action': 'reminder'
            }
        
        desktop = os.path.expanduser("~/Desktop")
        reminder_path = os.path.join(desktop, "recordatorios_jarvis.txt")
        
        try:
            with open(reminder_path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] {reminder_text}\n")
            
            return {
                'success': True,
                'response': f"Recordatorio guardado: {reminder_text}",
                'action': 'reminder'
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Error al guardar: {e}",
                'action': 'reminder'
            }
    
    def list_files(self, command: str) -> Dict[str, Any]:
        """Lista archivos del escritorio"""
        target = os.path.expanduser("~/Desktop")
        
        if "documentos" in command.lower():
            target = os.path.expanduser("~/Documents")
        elif "descargas" in command.lower():
            target = os.path.expanduser("~/Downloads")
        
        try:
            files = os.listdir(target)
            count = len(files)
            
            files_with_dates = []
            for f in files:
                path = os.path.join(target, f)
                if os.path.isfile(path):
                    mtime = os.path.getmtime(path)
                    files_with_dates.append((f, mtime))
            
            files_with_dates.sort(key=lambda x: x[1], reverse=True)
            recent = [f[0] for f in files_with_dates[:5]]
            
            return {
                'success': True,
                'response': f"Hay {count} archivos. Mas recientes: {', '.join(recent)}",
                'action': 'list_files'
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Error al listar: {e}",
                'action': 'list_files'
            }
    
    # ==========================================
    # VOLUMEN
    # ==========================================
    
    def set_volume(self, command: str) -> Dict[str, Any]:
        """Ajusta el volumen del sistema"""
        numbers = re.findall(r'\d+', command)
        
        if numbers:
            level = int(numbers[0])
            level = max(0, min(100, level))
            
            ps_script = f"""
            Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {{
                int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
                int GetMasterVolumeLevelScalar(out float pfLevel);
                int SetMute(bool bMute, Guid pguidEventContext);
                int GetMute(out bool pbMute);
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
            
            return {
                'success': True,
                'response': f"Volumen: {level}%",
                'action': 'volume'
            }
        
        return {
            'success': False,
            'response': "Especifica un nivel de volumen del 0 al 100",
            'action': 'volume'
        }
    
    def volume_up(self, command: str) -> Dict[str, Any]:
        """Sube el volumen"""
        for _ in range(2):
            os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"')
        return {
            'success': True,
            'response': "Volumen arriba",
            'action': 'volume_up'
        }
    
    def volume_down(self, command: str) -> Dict[str, Any]:
        """Baja el volumen"""
        for _ in range(2):
            os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"')
        return {
            'success': True,
            'response': "Volumen abajo",
            'action': 'volume_down'
        }
    
    def mute_volume(self, command: str) -> Dict[str, Any]:
        """Silencia/restaura el volumen"""
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"')
        return {
            'success': True,
            'response': "Sonido activado/desactivado",
            'action': 'mute'
        }
    
    # ==========================================
    # MULTIMEDIA
    # ==========================================
    
    def play_music(self, command: str) -> Dict[str, Any]:
        """Abre Spotify"""
        try:
            subprocess.Popen("start spotify", shell=True)
            return {
                'success': True,
                'response': "Abriendo Spotify",
                'action': 'music'
            }
        except:
            return {
                'success': True,
                'response': "No pude abrir Spotify, abrelo manualmente",
                'action': 'music'
            }
    
    def next_track(self, command: str) -> Dict[str, Any]:
        """Siguiente cancion"""
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"')
        return {
            'success': True,
            'response': "Siguiente",
            'action': 'next_track'
        }
    
    def pause_media(self, command: str) -> Dict[str, Any]:
        """Pausa la reproduccion"""
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"')
        return {
            'success': True,
            'response': "Pausado",
            'action': 'pause'
        }
    
    def resume_media(self, command: str) -> Dict[str, Any]:
        """Reanuda la reproduccion"""
        os.system('powershell -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"')
        return {
            'success': True,
            'response': "Reproduciendo",
            'action': 'resume'
        }
    
    # ==========================================
    # CAPTURA
    # ==========================================
    
    def screenshot(self, command: str) -> Dict[str, Any]:
        """Toma captura de pantalla"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.expanduser("~/Desktop")
        filepath = os.path.join(desktop, f"screenshot_{timestamp}.png")
        
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Bounds.X, $screen.Bounds.Y, 0, 0, $bitmap.Size)
        $bitmap.Save('{filepath}')
        $graphics.Dispose()
        $bitmap.Dispose()
        """
        
        with open("_temp_screenshot.ps1", "w") as f:
            f.write(ps_script)
        
        os.system("powershell -ExecutionPolicy Bypass -File _temp_screenshot.ps1")
        os.remove("_temp_screenshot.ps1")
        
        return {
            'success': True,
            'response': "Captura guardada en el escritorio",
            'action': 'screenshot'
        }

    def set_timer_skill(self, command: str) -> Dict[str, Any]:
        """Configura un temporizador"""
        from core.timers import TimerManager
        timer_mgr = TimerManager()
        seconds = timer_mgr.parse_time(command)
        
        if not seconds:
            return {
                'success': False,
                'response': "No entendi el tiempo. Di: temporizador 5 minutos",
                'action': 'timer'
            }
        
        response = timer_mgr.set_timer(seconds)
        
        return {
            'success': True,
            'response': response,
            'action': 'timer'
        }
    
    def set_alarm_skill(self, command: str) -> Dict[str, Any]:
        """Configura una alarma"""
        from core.timers import TimerManager
        timer_mgr = TimerManager()
        time_tuple = timer_mgr.parse_alarm_time(command)
        
        if not time_tuple:
            return {
                'success': False,
                'response': "No entendi la hora. Di: alarma a las 8:30",
                'action': 'alarm'
            }
        
        hour, minute = time_tuple
        response = timer_mgr.set_alarm(hour, minute)
        
        return {
            'success': True,
            'response': response,
            'action': 'alarm'
        }
    
    def cancel_timer_skill(self, command: str) -> Dict[str, Any]:
        """Cancela un temporizador"""
        from core.timers import TimerManager
        timer_mgr = TimerManager()
        response = timer_mgr.cancel_timer()
        return {
            'success': True,
            'response': response,
            'action': 'cancel_timer'
        }
    
    def cancel_alarm_skill(self, command: str) -> Dict[str, Any]:
        """Cancela una alarma"""
        from core.timers import TimerManager
        timer_mgr = TimerManager()
        response = timer_mgr.cancel_alarm()
        return {
            'success': True,
            'response': response,
            'action': 'cancel_alarm'
        }
    
    def list_timers_skill(self, command: str) -> Dict[str, Any]:
        """Lista temporizadores activos"""
        from core.timers import TimerManager
        timer_mgr = TimerManager()
        response = timer_mgr.list_timers()
        return {
            'success': True,
            'response': response,
            'action': 'list_timers'
        }
    
    def list_alarms_skill(self, command: str) -> Dict[str, Any]:
        """Lista alarmas programadas"""
        from core.timers import TimerManager
        timer_mgr = TimerManager()
        response = timer_mgr.list_alarms()
        return {
            'success': True,
            'response': response,
            'action': 'list_alarms'
        }

    def toggle_startup(self, command: str) -> Dict[str, Any]:
        """Activa o desactiva el inicio con Windows"""
        from core.startup import StartupManager
        startup = StartupManager()
        response = startup.toggle()
        return {
            'success': True,
            'response': response,
            'action': 'startup'
        }