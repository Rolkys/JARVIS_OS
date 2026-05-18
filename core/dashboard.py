"""
Dashboard web para JARVIS
Panel de control accesible desde el movil en red local
"""
import logging
import socket
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

logger = logging.getLogger("JARVIS.Dashboard")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS OS - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Consolas', 'Courier New', monospace;
            background: #0a0f19;
            color: #00ccff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #00ccff33;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; letter-spacing: 5px; }
        .header .subtitle { color: #0088aa; font-size: 0.9em; margin-top: 10px; }
        .status-bar {
            display: flex;
            justify-content: space-around;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: #0d1525;
            border: 1px solid #00ccff33;
            border-radius: 10px;
            padding: 15px 20px;
            text-align: center;
            flex: 1;
            min-width: 120px;
        }
        .stat-card .number {
            font-size: 2em;
            color: #00ccff;
        }
        .stat-card .label {
            font-size: 0.8em;
            color: #0088aa;
            margin-top: 5px;
        }
        .command-section {
            background: #0d1525;
            border: 1px solid #00ccff33;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .command-section h2 {
            font-size: 1.1em;
            margin-bottom: 15px;
            color: #00ccff;
        }
        .quick-commands {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }
        .quick-btn {
            background: #00ccff22;
            border: 1px solid #00ccff44;
            color: #00ccff;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.9em;
            transition: all 0.2s;
        }
        .quick-btn:hover {
            background: #00ccff44;
            border-color: #00ccff88;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        .input-group input {
            flex: 1;
            background: #060b14;
            border: 1px solid #00ccff33;
            color: #00ccff;
            padding: 12px;
            border-radius: 5px;
            font-family: inherit;
            font-size: 1em;
        }
        .input-group input:focus {
            outline: none;
            border-color: #00ccff88;
        }
        .input-group button {
            background: #00ccff;
            border: none;
            color: #0a0f19;
            padding: 12px 25px;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            font-weight: bold;
            font-size: 1em;
        }
        .input-group button:hover { background: #00ddff; }
        .log-section {
            background: #0d1525;
            border: 1px solid #00ccff33;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            max-height: 300px;
            overflow-y: auto;
        }
        .log-entry {
            padding: 8px 0;
            border-bottom: 1px solid #00ccff11;
            font-size: 0.85em;
        }
        .log-entry .time { color: #005570; }
        .log-entry .cmd { color: #00ccff; }
        .log-entry .response { color: #00aa88; }
        .footer {
            text-align: center;
            padding: 20px;
            color: #005570;
            font-size: 0.8em;
        }
        .pulse {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>J.A.R.V.I.S.</h1>
            <div class="subtitle">
                <span class="pulse"></span> Sistemas operativos | {{ status }}
            </div>
        </div>

        <div class="status-bar">
            <div class="stat-card">
                <div class="number">{{ stats.total_commands }}</div>
                <div class="label">Comandos totales</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ stats.success_commands }}</div>
                <div class="label">Exitosos</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ stats.total_notes }}</div>
                <div class="label">Notas</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ stats.pending_reminders }}</div>
                <div class="label">Pendientes</div>
            </div>
        </div>

        <div class="command-section">
            <h2>Comandos rapidos</h2>
            <div class="quick-commands">
                <button class="quick-btn" onclick="sendCommand('que hora es')">Hora</button>
                <button class="quick-btn" onclick="sendCommand('estado del sistema')">Sistema</button>
                <button class="quick-btn" onclick="sendCommand('abre discord')">Abrir Discord</button>
                <button class="quick-btn" onclick="sendCommand('abre spotify')">Abrir Spotify</button>
                <button class="quick-btn" onclick="sendCommand('noticias')">Noticias</button>
                <button class="quick-btn" onclick="sendCommand('dato curioso')">Dato curioso</button>
                <button class="quick-btn" onclick="sendCommand('captura')">Captura</button>
                <button class="quick-btn" onclick="sendCommand('estadisticas')">Estadisticas</button>
            </div>
            
            <h2>Comando personalizado</h2>
            <div class="input-group">
                <input type="text" id="commandInput" placeholder="Escribe un comando..." 
                       onkeypress="if(event.key==='Enter') sendCommand(document.getElementById('commandInput').value)">
                <button onclick="sendCommand(document.getElementById('commandInput').value)">Enviar</button>
            </div>
        </div>

        <div class="log-section" id="logContainer">
            <h2>Historial reciente</h2>
            <div id="logEntries"></div>
        </div>

        <div class="footer">
            JARVIS OS v1.0 | Stark Industries | {{ ip }}
        </div>
    </div>

    <script>
        function sendCommand(command) {
            if (!command.trim()) return;
            
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: command})
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('commandInput').value = '';
                setTimeout(() => location.reload(), 500);
            });
        }
        
        function refreshLogs() {
            fetch('/api/logs')
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('logEntries');
                    container.innerHTML = data.logs.map(log => `
                        <div class="log-entry">
                            <span class="time">${log.timestamp}</span>
                            <span class="cmd">> ${log.command}</span>
                            ${log.response ? `<br><span class="response">  ${log.response.substring(0, 100)}</span>` : ''}
                        </div>
                    `).join('');
                });
        }
        
        setInterval(refreshLogs, 3000);
        refreshLogs();
    </script>
</body>
</html>
"""

class Dashboard:
    """Servidor web para controlar JARVIS remotamente"""

    def __init__(self, jarvis_instance=None, host: str = "0.0.0.0", port: int = 5050):
        self.jarvis = jarvis_instance
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()
        logger.info(f"Dashboard iniciado en http://{self._get_local_ip()}:{port}")

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _setup_routes(self):

        @self.app.route('/')
        def index():
            stats = {"total_commands": 0, "success_commands": 0, "total_notes": 0, "pending_reminders": 0}
            if self.jarvis and hasattr(self.jarvis, 'db'):
                try:
                    stats = self.jarvis.db.get_stats()
                except:
                    pass

            return render_template_string(
                HTML_TEMPLATE,
                status="En linea",
                stats=stats,
                ip=self._get_local_ip()
            )

        @self.app.route('/api/command', methods=['POST'])
        def api_command():
            data = request.get_json()
            command = data.get('command', '')

            if self.jarvis and command:
                self.jarvis.process_command(command)
                return jsonify({'status': 'ok', 'command': command})

            return jsonify({'status': 'error', 'message': 'Sin comando'})

        @self.app.route('/api/logs')
        def api_logs():
            logs = []
            if self.jarvis and hasattr(self.jarvis, 'db'):
                try:
                    db_logs = self.jarvis.db.get_command_history(20)
                    logs = [dict(log) for log in db_logs]
                except:
                    pass
            return jsonify({'logs': logs})

        @self.app.route('/api/stats')
        def api_stats():
            stats = {"total_commands": 0, "success_commands": 0, "total_notes": 0, "pending_reminders": 0}
            if self.jarvis and hasattr(self.jarvis, 'db'):
                try:
                    stats = self.jarvis.db.get_stats()
                except:
                    pass
            return jsonify(stats)

    def start(self):
        """Inicia el servidor en un hilo"""
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        """Ejecuta el servidor Flask"""
        from flask_cors import CORS
        CORS(self.app)
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)