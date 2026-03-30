import sqlite3
import os
from datetime import datetime

class AuditService:
    def __init__(self, db_path="data/compliance_audit.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                action_description TEXT,
                category TEXT,
                risk_score TEXT,
                rationale TEXT,
                citations TEXT,
                corrective_actions TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_assessment(self, action_description, category, risk_score, rationale, citations, corrective_actions):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (timestamp, action_description, category, risk_score, rationale, citations, corrective_actions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            action_description,
            category,
            risk_score,
            rationale,
            str(citations),
            str(corrective_actions)
        ))
        conn.commit()
        conn.close()

    def get_logs(self, limit=50):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?', (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs
