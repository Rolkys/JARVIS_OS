"""
Modulo de base de datos SQLite para JARVIS
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger("JARVIS.Database")

class Database:
    """Gestiona la base de datos local de JARVIS"""

    def __init__(self, db_path: str = "jarvis.db"):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
        logger.info("Base de datos inicializada")

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                done INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commands_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                action TEXT,
                success INTEGER,
                response TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.conn.commit()

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # NOTAS
    def add_note(self, text: str) -> int:
        now = self._now()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO notes (text, created_at, updated_at) VALUES (?, ?, ?)",
            (text, now, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_notes(self, limit: int = 10) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def search_notes(self, query: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM notes WHERE text LIKE ? ORDER BY updated_at DESC",
            (f"%{query}%",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_note(self, note_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # RECORDATORIOS
    def add_reminder(self, text: str) -> int:
        now = self._now()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (text, created_at) VALUES (?, ?)",
            (text, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_reminders(self, show_done: bool = False) -> List[Dict]:
        cursor = self.conn.cursor()
        if show_done:
            cursor.execute("SELECT * FROM reminders ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM reminders WHERE done = 0 ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def mark_reminder_done(self, reminder_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE reminders SET done = 1 WHERE id = ?", (reminder_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_reminder(self, reminder_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # CONVERSACION
    def save_conversation(self, role: str, text: str):
        now = self._now()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO conversation (role, text, timestamp) VALUES (?, ?, ?)",
            (role, text, now)
        )
        self.conn.commit()

    def get_conversation(self, limit: int = 20) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM conversation ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in reversed(rows)]

    def clear_conversation(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM conversation")
        self.conn.commit()

    # LOG DE COMANDOS
    def log_command(self, command: str, action: str = None, success: bool = None, response: str = None):
        now = self._now()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO commands_log (command, action, success, response, timestamp) VALUES (?, ?, ?, ?, ?)",
            (command, action, 1 if success else 0, response, now)
        )
        self.conn.commit()

    def get_command_history(self, limit: int = 50) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM commands_log ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM commands_log")
        total_commands = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM commands_log WHERE success = 1")
        success_commands = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM notes")
        total_notes = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM reminders WHERE done = 0")
        pending_reminders = cursor.fetchone()["count"]

        return {
            "total_commands": total_commands,
            "success_commands": success_commands,
            "total_notes": total_notes,
            "pending_reminders": pending_reminders,
        }

    # CONFIGURACION
    def set_config(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_config(self, key: str, default: str = None) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

    def close(self):
        if self.conn:
            self.conn.close()