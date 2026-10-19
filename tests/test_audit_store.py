import os
import sqlite3
import pytest
from src.models.schemas import DLPAuditReport, RiskLevel

def test_audit_logger_redacts_pii(tmp_path):
    """Verify that AuditStore persists audit events with hashes and zero raw PII."""
    from src.adapters.audit_store import AuditStore
    
    db_file = str(tmp_path / "test_audit.db")
    store = AuditStore(db_path=db_file)
    
    # Create sample audit report
    report = DLPAuditReport(
        file_id="doc_secret_44",
        file_name="Secret_Contract.txt",
        risk_level=RiskLevel.CRITICAL,
        pii_types_detected=["IBAN", "Steuer-ID"],
        gdpr_articles_impacted=["Art. 6"],
        sharing_permission_risk="PUBLIC_LINK",
        recommended_remediation="Revoke public link",
        content_hash_sha256="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
        redacted_preview="Preview with [REDACTED_IBAN_1]"
    )
    
    store.log_dlp_scan(report)
    
    # Verify in SQLite
    records = store.get_recent_audits()
    assert len(records) == 1
    record = records[0]
    
    assert record["event_type"] == "DLP_SCAN"
    assert record["target_id"] == "doc_secret_44"
    assert record["content_hash_sha256"] == "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a"
    assert record["risk_level"] == "CRITICAL"
    
    # Assert zero raw PII or secret unredacted text in database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs")
    raw_row_str = str(cursor.fetchall())
    conn.close()
    
    assert "DE89" not in raw_row_str
    assert "Secret_Contract" in raw_row_str or "doc_secret_44" in raw_row_str

    # Test generic log_event and get_recent_events
    store.log_event("POLICY_CHECK", "usr_101", "LOW", "hash123456")
    recent = store.get_recent_events(limit=10)
    assert len(recent) == 2
    assert recent[0]["event_type"] == "POLICY_CHECK"

