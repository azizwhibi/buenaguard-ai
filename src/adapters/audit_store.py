import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.config import settings
from src.models.schemas import DLPAuditReport
from src.ports.workspace_port import AuditStorePort

class AuditStore(AuditStorePort):
    """SQLite-backed, GDPR-compliant audit logger storing SHA-256 hashes and zero raw PII."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.AUDIT_DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        content_hash_sha256 TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        summary TEXT
                    )
                """)
        finally:
            conn.close()

    def log_dlp_scan(self, report: DLPAuditReport) -> None:
        """Store DLP audit event ensuring zero raw PII is written to disk."""
        now = datetime.now(timezone.utc).isoformat()
        risk_val = report.risk_level.value if hasattr(report.risk_level, "value") else str(report.risk_level)
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_logs (timestamp, event_type, target_id, content_hash_sha256, risk_level, summary)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    now,
                    "DLP_SCAN",
                    report.file_id,
                    report.content_hash_sha256,
                    risk_val,
                    report.file_name
                ))
        finally:
            conn.close()

    def log_event(self, event_type: str, target_id: str, risk_level: str, content_hash: str) -> None:
        """Record an audit trail event with SHA-256 hash and zero raw PII."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_logs (timestamp, event_type, target_id, content_hash_sha256, risk_level, summary)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (now, event_type, target_id, content_hash, risk_level, ""))
        finally:
            conn.close()

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent audit events for compliance reporting."""
        return self.get_recent_audits(limit=limit)

    def get_recent_audits(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent audit records formatted as dictionaries."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, event_type, target_id, content_hash_sha256, risk_level, summary
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

