"""
Modo desarrollador para JARVIS
Ejecuta scripts, abre proyectos y controla el entorno de desarrollo
"""
import subprocess
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("JARVIS.Developer")

class DeveloperMode:
    """Comandos para desarrolladores"""

    def __init__(self):
        self.projects_dir = os.path.expanduser("~/Documents/Projects")
        self.default_editor = "code"  # VS Code

        # Asegurar que existe la carpeta de proyectos
        os.makedirs(self.projects_dir, exist_ok=True)

        logger.info("Modo desarrollador inicializado")

    def open_project(self, project_name: str) -> Dict[str, Any]:
        """Abre un proyecto en VS Code"""
        project_path = os.path.join(self.projects_dir, project_name)

        if os.path.exists(project_path):
            subprocess.Popen(f"{self.default_editor} {project_path}", shell=True)
            return {
                'success': True,
                'response': f"Abriendo proyecto {project_name}",
                'action': 'open_project'
            }

        # Buscar en subcarpetas
        for folder in os.listdir(self.projects_dir):
            folder_path = os.path.join(self.projects_dir, folder)
            if os.path.isdir(folder_path) and project_name.lower() in folder.lower():
                subprocess.Popen(f"{self.default_editor} {folder_path}", shell=True)
                return {
                    'success': True,
                    'response': f"Abriendo proyecto {folder}",
                    'action': 'open_project'
                }

        return {
            'success': False,
            'response': f"No encontre el proyecto {project_name} en {self.projects_dir}",
            'action': 'open_project'
        }

    def new_project(self, project_name: str, project_type: str = "python") -> Dict[str, Any]:
        """Crea un nuevo proyecto con estructura basica"""
        project_path = os.path.join(self.projects_dir, project_name)

        if os.path.exists(project_path):
            return {
                'success': False,
                'response': f"El proyecto {project_name} ya existe",
                'action': 'new_project'
            }

        try:
            os.makedirs(project_path, exist_ok=True)

            if project_type in ["python", "py"]:
                # Crear estructura Python
                os.makedirs(os.path.join(project_path, "src"), exist_ok=True)
                with open(os.path.join(project_path, "main.py"), "w") as f:
                    f.write(f'"""\n{project_name}\n"""\n\n\ndef main():\n    print("Hola desde {project_name}")\n\n\nif __name__ == "__main__":\n    main()\n')
                with open(os.path.join(project_path, "README.md"), "w") as f:
                    f.write(f"# {project_name}\n\nProyecto creado por JARVIS\n")

            elif project_type in ["web", "html"]:
                with open(os.path.join(project_path, "index.html"), "w") as f:
                    f.write(f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>{project_name}</h1>
    <p>Proyecto creado por JARVIS</p>
    <script src="script.js"></script>
</body>
</html>""")
                with open(os.path.join(project_path, "style.css"), "w") as f:
                    f.write("* { margin: 0; padding: 0; box-sizing: border-box; }\nbody { font-family: sans-serif; padding: 20px; }\n")
                with open(os.path.join(project_path, "script.js"), "w") as f:
                    f.write("console.log('Proyecto creado por JARVIS');\n")

            elif project_type in ["react", "next"]:
                subprocess.Popen(f"npx create-react-app {project_path}", shell=True)
                return {
                    'success': True,
                    'response': f"Creando proyecto React {project_name}. Esto puede tardar unos minutos.",
                    'action': 'new_project'
                }

            # Abrir en VS Code
            subprocess.Popen(f"{self.default_editor} {project_path}", shell=True)

            return {
                'success': True,
                'response': f"Proyecto {project_name} creado y abierto en VS Code",
                'action': 'new_project'
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Error al crear proyecto: {e}",
                'action': 'new_project'
            }

    def list_projects(self) -> Dict[str, Any]:
        """Lista proyectos disponibles"""
        if not os.path.exists(self.projects_dir):
            return {
                'success': True,
                'response': "No hay proyectos. Crea uno con: nuevo proyecto nombre",
                'action': 'list_projects'
            }

        projects = os.listdir(self.projects_dir)

        if not projects:
            return {
                'success': True,
                'response': "No hay proyectos en la carpeta de proyectos",
                'action': 'list_projects'
            }

        response = "Proyectos disponibles: "
        for i, proj in enumerate(projects[:10], 1):
            response += f"{i}. {proj}, "

        return {
            'success': True,
            'response': response.strip(', '),
            'action': 'list_projects'
        }

    def run_script(self, script_name: str) -> Dict[str, Any]:
        """Ejecuta un script de Python"""
        # Buscar en la carpeta actual y proyectos
        script_path = script_name

        if not os.path.exists(script_path):
            # Buscar en proyectos
            for folder in os.listdir(self.projects_dir):
                potential_path = os.path.join(self.projects_dir, folder, script_name)
                if os.path.exists(potential_path):
                    script_path = potential_path
                    break

        if not os.path.exists(script_path):
            return {
                'success': False,
                'response': f"No encontre el script {script_name}",
                'action': 'run_script'
            }

        try:
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                output = result.stdout[:200] if result.stdout else "Ejecutado correctamente"
                return {
                    'success': True,
                    'response': f"Script ejecutado: {output}",
                    'action': 'run_script'
                }
            else:
                return {
                    'success': False,
                    'response': f"Error: {result.stderr[:200]}",
                    'action': 'run_script'
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'response': "El script tardo demasiado. Lo he detenido.",
                'action': 'run_script'
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Error al ejecutar: {e}",
                'action': 'run_script'
            }

    def git_command(self, command: str) -> Dict[str, Any]:
        """Ejecuta comandos de Git"""
        git_commands = {
            "git status": "git status",
            "estado": "git status",
            "git add": "git add .",
            "agregar": "git add .",
            "git commit": 'git commit -m "Commit desde JARVIS"',
            "commit": 'git commit -m "Commit desde JARVIS"',
            "git push": "git push",
            "subir": "git push",
            "git pull": "git pull",
            "actualizar": "git pull",
            "git log": "git log --oneline -5",
            "historial": "git log --oneline -5",
        }

        command_lower = command.lower()

        for key, git_cmd in git_commands.items():
            if key in command_lower:
                try:
                    result = subprocess.run(
                        git_cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=15,
                        shell=True
                    )

                    output = (result.stdout or result.stderr)[:300]
                    return {
                        'success': True,
                        'response': f"Git: {output}",
                        'action': 'git'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'response': f"Error en Git: {e}",
                        'action': 'git'
                    }

        return {
            'success': False,
            'response': "Comando Git no reconocido",
            'action': 'git'
        }

    def open_terminal(self) -> Dict[str, Any]:
        """Abre una terminal en la carpeta de proyectos"""
        subprocess.Popen(f"wt -d {self.projects_dir}", shell=True)
        return {
            'success': True,
            'response': "Abriendo terminal en proyectos",
            'action': 'open_terminal'
        }

    def create_shortcut(self, name: str, command_str: str) -> Dict[str, Any]:
        """Crea un acceso directo personalizado"""
        shortcut_path = os.path.join(self.projects_dir, f"{name}.bat")

        try:
            with open(shortcut_path, "w") as f:
                f.write(f"@echo off\n{command_str}\npause\n")

            return {
                'success': True,
                'response': f"Acceso directo {name} creado en proyectos",
                'action': 'create_shortcut'
            }
        except Exception as e:
            return {
                'success': False,
                'response': f"Error: {e}",
                'action': 'create_shortcut'
            }