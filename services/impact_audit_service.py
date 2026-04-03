import sqlite3
import os
import json
from datetime import datetime

class ImpactAuditService:
    def __init__(self, db_path="data/impact_audit.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impact_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                document_name TEXT,
                affected_count INTEGER,
                critical_alerts INTEGER,
                high_alerts INTEGER,
                full_results_json TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_impact(self, document_name, results):
        """Automatically logs the results of a business impact analysis."""
        affected = [r for r in results if r['impact_type'] != "NO CHANGE"]
        critical_count = len([r for r in results if r['impact_type'] == 'PRODUCT REMOVED'])
        high_count = len([r for r in results if r['priority'] == 'HIGH'])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO impact_audits (timestamp, document_name, affected_count, critical_alerts, high_alerts, full_results_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            document_name,
            len(affected),
            critical_count,
            high_count,
            json.dumps(results)
        ))
        conn.commit()
        conn.close()

    def get_logs(self, limit=50):
        """Retrieves past impact analysis logs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM impact_audits ORDER BY timestamp DESC LIMIT ?', (limit,))
        logs = cursor.fetchall()
        conn.close()
        return logs
