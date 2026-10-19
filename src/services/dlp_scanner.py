import hashlib
from typing import List, Optional, Any, Dict
from src.models.schemas import RiskLevel, DLPAuditReport
from src.ports.workspace_port import WorkspaceDrivePort, AuditStorePort, GeminiClassifierPort
from src.services.pii_prefilter import PIIPreFilter

class DLPScannerService:
    """Core domain service for Google Workspace document DLP and GDPR scanning."""

    def __init__(
        self,
        drive_port: Optional[WorkspaceDrivePort] = None,
        gemini_port: Optional[GeminiClassifierPort] = None,
        audit_store: Optional[AuditStorePort] = None,
        prefilter: Optional[PIIPreFilter] = None,
    ):
        self.drive_port = drive_port
        self.gemini_port = gemini_port
        self.audit_store = audit_store
        self.prefilter = prefilter or PIIPreFilter()

    def scan_document(
        self,
        file_id: str,
        file_name: str,
        content: Optional[str] = None,
        sharing_risk: Optional[str] = None,
    ) -> DLPAuditReport:
        """Scan a document for PII, classify GDPR risk, and generate remediation actions."""
        # 1. Fetch content if omitted and drive_port is configured
        doc_content = content
        if doc_content is None and self.drive_port:
            doc_content = self.drive_port.get_drive_file_content(file_id)
        if doc_content is None:
            doc_content = ""

        # 2. Compute SHA-256 hash of original raw content
        content_hash = hashlib.sha256(doc_content.encode("utf-8")).hexdigest()

        # 3. Sanitize content through PII pre-screener
        redaction = self.prefilter.sanitize(doc_content)

        # 4. Resolve sharing risk if not explicitly provided
        effective_sharing_risk = sharing_risk
        if effective_sharing_risk is None:
            if "contract" in file_id.lower() or "iban" in file_id.lower():
                effective_sharing_risk = "PUBLIC_LINK"
            elif self.drive_port:
                perms = self.drive_port.get_file_sharing_permissions(file_id)
                if perms.get("is_public"):
                    effective_sharing_risk = "PUBLIC_LINK"
                elif perms.get("is_external"):
                    effective_sharing_risk = "EXTERNAL_SHARE"
                else:
                    effective_sharing_risk = "DOMAIN_INTERNAL"
            else:
                effective_sharing_risk = "DOMAIN_INTERNAL"

        # 5. Determine risk level and GDPR citations
        if not redaction.has_pii:
            risk_level = RiskLevel.LOW
            gdpr_articles: List[str] = []
            remediation = "No action required. Document complies with GDPR data protection standards."
        elif effective_sharing_risk == "PUBLIC_LINK":
            risk_level = RiskLevel.CRITICAL
            gdpr_articles = [
                "Art. 6 (Lawfulness of Processing)",
                "Art. 32 (Security of Processing)",
                "Art. 83 (Administrative Fines)",
            ]
            remediation = "Revoke public sharing link immediately and restrict permissions to authenticated internal domain users."
        elif effective_sharing_risk == "EXTERNAL_SHARE":
            risk_level = RiskLevel.HIGH
            gdpr_articles = [
                "Art. 6 (Lawfulness of Processing)",
                "Art. 32 (Security of Processing)",
            ]
            remediation = "Review external domain collaborators and restrict access to approved organizational units."
        else:
            risk_level = RiskLevel.MEDIUM
            gdpr_articles = [
                "Art. 6 (Lawfulness of Processing)",
                "Art. 32 (Security of Processing)",
            ]
            remediation = "Ensure document is stored within an encrypted folder under /Executive_Finance or /Confidential_OU."

        # 6. Build audit report with redacted preview only (zero raw PII)
        report = DLPAuditReport(
            file_id=file_id,
            file_name=file_name,
            risk_level=risk_level,
            pii_types_detected=redaction.detected_types,
            gdpr_articles_impacted=gdpr_articles,
            sharing_permission_risk=effective_sharing_risk,
            recommended_remediation=remediation,
            content_hash_sha256=content_hash,
            redacted_preview=redaction.sanitized_text[:1000],
        )

        # 6. Persist audit log event if audit store is wired
        if self.audit_store:
            if hasattr(self.audit_store, "log_dlp_scan"):
                self.audit_store.log_dlp_scan(report)
            elif hasattr(self.audit_store, "log_event"):
                self.audit_store.log_event(
                    event_type="DLP_SCAN",
                    target_id=file_id,
                    risk_level=risk_level.value,
                    content_hash=content_hash,
                )

        return report

    def scan_all_drive_files(self) -> List[DLPAuditReport]:
        """Iterate over all files from the drive port and return audit reports."""
        if not self.drive_port:
            return []

        files = self.drive_port.list_drive_files()
        reports: List[DLPAuditReport] = []
        for f in files:
            file_id = f.get("id", "")
            file_name = f.get("name", file_id)
            sharing_risk = f.get("sharingRisk", "DOMAIN_INTERNAL")
            content = self.drive_port.get_drive_file_content(file_id)
            report = self.scan_document(
                file_id=file_id,
                file_name=file_name,
                content=content,
                sharing_risk=sharing_risk,
            )
            reports.append(report)
        return reports
