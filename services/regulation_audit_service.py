import sqlite3
import os
from datetime import datetime

class RegulationAuditService:
    def __init__(self, db_path="data/regulation_audit.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regulation_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                category TEXT,
                previous_file TEXT,
                new_file TEXT,
                summary TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_change(self, category, previous_file, new_file, summary):
        """Logs a regulatory change summary automatically."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO regulation_audits (timestamp, category, previous_file, new_file, summary)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            category,
            os.path.basename(previous_file) if previous_file else "N/A",
            os.path.basename(new_file) if new_file else "N/A",
            summary
        ))
        conn.commit()
        conn.close()

    def get_logs(self, limit=50):
        """Retrieves all saved change detection summaries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM regulation_audits ORDER BY timestamp DESC LIMIT ?', (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs
