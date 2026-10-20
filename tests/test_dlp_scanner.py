import os
import pytest
from pathlib import Path
from src.models.schemas import RiskLevel, DLPAuditReport
from src.services.dlp_scanner import DLPScannerService

def test_dlp_scanner_identifies_gdpr_risk_levels():
    """Verify that DLPScanner flags public file with German IBAN and Steuer-ID as CRITICAL."""
    scanner = DLPScannerService()
    
    contract_path = Path("fixtures/sample_docs/contract_with_iban.txt")
    content = contract_path.read_text(encoding="utf-8")
    
    report = scanner.scan_document(
        file_id="doc_contract_de_01",
        file_name="contract_with_iban.txt",
        content=content,
        sharing_risk="PUBLIC_LINK"
    )
    
    assert isinstance(report, DLPAuditReport)
    assert report.file_id == "doc_contract_de_01"
    assert report.risk_level == RiskLevel.CRITICAL
    assert "IBAN" in report.pii_types_detected
    assert "STEUER_ID" in report.pii_types_detected
    assert "SALARY" in report.pii_types_detected
    
    # Assert zero raw PII in redacted preview
    assert "DE89370400440532013000" not in report.redacted_preview
    assert "41234567890" not in report.redacted_preview
    assert "110.000 EUR" not in report.redacted_preview
    assert "[REDACTED_IBAN_1]" in report.redacted_preview
    
    # Assert remediation recommendation and GDPR articles
    assert "revoke" in report.recommended_remediation.lower() or "restrict" in report.recommended_remediation.lower()
    assert any("Art." in article for article in report.gdpr_articles_impacted)
    assert len(report.content_hash_sha256) == 64

def test_dlp_scanner_clean_doc():
    """Verify that a document without PII is evaluated as LOW risk."""
    scanner = DLPScannerService()
    clean_path = Path("fixtures/sample_docs/clean_notes.txt")
    content = clean_path.read_text(encoding="utf-8")
    
    report = scanner.scan_document(
        file_id="doc_clean_02",
        file_name="clean_notes.txt",
        content=content,
        sharing_risk="DOMAIN_INTERNAL"
    )
    
    assert report.risk_level == RiskLevel.LOW
    assert len(report.pii_types_detected) == 0

def test_dlp_scanner_persists_to_audit_store(tmp_path):
    """Verify scan event is stored in AuditStore with SHA-256 hash and zero raw PII."""
    from src.adapters.audit_store import AuditStore
    
    db_file = str(tmp_path / "audit_test.db")
    audit_store = AuditStore(db_path=db_file)
    scanner = DLPScannerService(audit_store=audit_store)
    
    contract_path = Path("fixtures/sample_docs/contract_with_iban.txt")
    content = contract_path.read_text(encoding="utf-8")
    
    scanner.scan_document(
        file_id="audit_check_doc",
        file_name="contract_with_iban.txt",
        content=content,
        sharing_risk="PUBLIC_LINK"
    )
    
    records = audit_store.get_recent_audits()
    assert len(records) == 1
    assert records[0]["target_id"] == "audit_check_doc"
    assert records[0]["risk_level"] == "CRITICAL"
    assert len(records[0]["content_hash_sha256"]) == 64

def test_dlp_scanner_scan_all_drive_files():
    """Verify scanning all files retrieved through WorkspaceDrivePort."""
    from src.adapters.google_live_adapter import GoogleLiveAdapter
    
    drive_adapter = GoogleLiveAdapter(credentials_path="nonexistent.json", token_path="nonexistent.json")
    scanner = DLPScannerService(drive_port=drive_adapter)
    
    reports = scanner.scan_all_drive_files()
    assert len(reports) > 0
    assert any(r.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH] for r in reports)

def test_dlp_scanner_external_share_and_internal_medium_risk():
    """Verify risk classification based on content sensitivity and sharing permissions."""
    scanner = DLPScannerService()
    
    # 1. External share with contractor rate -> HIGH
    contractor_content = "Carlos Mendez, Contractor SOW. Rate: 850 EUR per day. Zero-trust remote access."
    high_rep = scanner.scan_document(
        file_id="doc_ext_01",
        file_name="external_contractor_agreement.txt",
        content=contractor_content,
        sharing_risk="EXTERNAL_SHARE"
    )
    assert high_rep.risk_level == RiskLevel.HIGH
    assert "sharing permissions" in high_rep.recommended_remediation.lower()
    
    # 2. Domain internal with contractor rate only -> MEDIUM
    med_rep = scanner.scan_document(
        file_id="doc_int_01",
        file_name="04_MEDIUM_External_Contractor_Agreement.txt",
        content=contractor_content,
        sharing_risk="DOMAIN_INTERNAL"
    )
    assert med_rep.risk_level == RiskLevel.MEDIUM
    assert "encrypted folder" in med_rep.recommended_remediation.lower()

    # 3. Domain internal with executive payroll (Salaries + IBANs + Steuer-IDs) -> CRITICAL
    payroll_content = (
        "Mitarbeiter_ID,Vollstaendiger_Name,Steuer_ID,IBAN,Monatsgehalt_EUR\n"
        "EMP-101,Hannah Weber,11987654321,DE21500500001234567890,16.500 EUR\n"
    )
    crit_rep = scanner.scan_document(
        file_id="doc_crit_01",
        file_name="01_CRITICAL_Executive_Payroll_Q4_2026.csv",
        content=payroll_content,
        sharing_risk="DOMAIN_INTERNAL"
    )
    assert crit_rep.risk_level == RiskLevel.CRITICAL
    assert "quarantine" in crit_rep.recommended_remediation.lower()

    # 4. Domain internal with employment contract (Passport + IBAN + Steuer-ID) -> HIGH
    contract_content = (
        "ARBEITSVERTRAG: Lukas Schmidt. Pass: C01X00T4K, IBAN: DE89370400440532013000, Steuer-ID: 41234567890"
    )
    contract_rep = scanner.scan_document(
        file_id="doc_contract_02",
        file_name="02_HIGH_Arbeitsvertrag_Senior_Ingenieur.txt",
        content=contract_content,
        sharing_risk="DOMAIN_INTERNAL"
    )
    assert contract_rep.risk_level == RiskLevel.HIGH

def test_dlp_scanner_generic_audit_store_log_event():
    """Verify fallback to log_event when audit store lacks log_dlp_scan."""
    class GenericAuditStore:
        def __init__(self):
            self.events = []
        def log_event(self, event_type, target_id, risk_level, content_hash):
            self.events.append((event_type, target_id, risk_level, content_hash))
            
    generic_store = GenericAuditStore()
    scanner = DLPScannerService(audit_store=generic_store)
    scanner.scan_document(
        file_id="gen_doc_1",
        file_name="notes.txt",
        content="Clean content without PII"
    )
    assert len(generic_store.events) == 1
    assert generic_store.events[0][0] == "DLP_SCAN"
    assert generic_store.events[0][1] == "gen_doc_1"


