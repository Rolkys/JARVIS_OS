"""
Modulo de auto-inicio con Windows
"""

import os 
import sys
import logging
import getpass

logger =  logging.getLogger("JARVIS.Startup")

class StartupManager:
    """Gestioa el inico automaticamente de JARVIS con Windows"""

    def __init__(self):
        self.username = getpass.getuser()
        self.startup_folder = os.path.join(
            "C:", os.sep, "Users", self.username,
            "AppData", "Roaming", "Microsoft", "Windows",
            "Start Menu", "Programs", "Startup"
        )
        self.shortcut_name = "JARVIS_OS.lnk"
        self.shortcut_path = os.path.join(self.startup_folder, self.shortcut_name)

    def is_enable(self) -> bool:
        """Verifica si el auto-inicio esta activado"""
        return os.path.exists(self.shortcut_path)
    
    def enable(self) -> bool:
        """Activa el inicio automatico con Windows"""
        try:
            project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            python_path = os.path.join(project_path, "venv", "Scripts", "pythonw.exe")
            main_script = os.path.join(project_path, "main.py")

            # Usar PowerShell para crear el acceso directo
            ps_script = f"""
            $WScriptShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WScriptShell.CreateShortcut("{self.shortcut_path}")
            $Shortcut.TargetPath = "{python_path}"
            $Shortcut.Arguments = '"{main_script}"'
            $Shortcut.WorkingDirectory = "{project_path}"
            $Shortcut.WindowStyle = 7
            $Shortcut.Description = "JARVIS OS - Asistente IA"
            $Shortcut.Save()
            """

            with open("_temp_startup.ps1", "w") as f:
                f.write(ps_script)

            os.system("powershell -ExecutionPolicy Bypass -File _temp_startup.ps1")
            os.remove("_temp_startup.ps1")

            logger.info("Auto-inicio activado")
            return True
        except Exception as e:
            logger.error(f"Error activando auto-inicio: {e}")
            return False
        
    def disable(self) -> bool:
        """Desactiva el inico automatico"""
        try:
            if os.path.exists(self.shortcut_path):
                os.remove(self.shortcut_path)
                logger.info("Auto-inicio desactivado")
            return True
        except Exception as e:
            logger.error(f"Error desactivando auto-inicio: {e}")
            return False
    
    def toggle(self) -> str:
        """Alterna el auto-inicio y devuelve mensaje"""
        if self.is_enable():
            self.disable()
            return "Auto inicio desactivado"
        else:
            self.enable()
            return "Auto-inicio activado. JARVIS se iniciara con Windows"