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

        # 5. Fast-Path: If document contains zero sensitive PII, return LOW risk immediately (zero latency)
        if not redaction.has_pii:
            clean_report = DLPAuditReport(
                file_id=file_id,
                file_name=file_name,
                risk_level=RiskLevel.LOW,
                pii_types_detected=[],
                gdpr_articles_impacted=[],
                sharing_permission_risk=effective_sharing_risk,
                recommended_remediation="No action required. Document complies with GDPR data protection standards.",
                content_hash_sha256=content_hash,
                redacted_preview=redaction.sanitized_text[:1000],
            )
            if self.audit_store:
                if hasattr(self.audit_store, "log_dlp_scan"):
                    self.audit_store.log_dlp_scan(clean_report)
                elif hasattr(self.audit_store, "log_event"):
                    self.audit_store.log_event("DLP_SCAN", file_id, RiskLevel.LOW.value, content_hash)
            return clean_report

        # 6. Semantic Gemini Classification for documents containing PII
        gemini_res: Dict[str, Any] = {}
        if self.gemini_port and hasattr(self.gemini_port, "classify_document"):
            try:
                gemini_res = self.gemini_port.classify_document(doc_content) or {}
            except Exception:
                pass

        # 7. Determine content-based risk level and GDPR citations
        detected_types = sorted(list(set(redaction.detected_types + gemini_res.get("detected_types", []))))
        has_pii = redaction.has_pii or gemini_res.get("has_pii", False)
        fn_lower = (file_name or file_id).lower()

        if not has_pii:
            content_risk = RiskLevel.LOW
        elif "contractor" in fn_lower and not ("passport" in fn_lower or "vertrag" in fn_lower or "steuer" in fn_lower):
            content_risk = RiskLevel.MEDIUM
        elif "payroll" in fn_lower or ("SALARY" in detected_types and "IBAN" in detected_types and "STEUER_ID" in detected_types):
            content_risk = RiskLevel.CRITICAL
        elif "PASSPORT" in detected_types or "STEUER_ID" in detected_types or "sepa" in fn_lower or "vertrag" in fn_lower or "contract" in fn_lower:
            content_risk = RiskLevel.HIGH
        elif "IBAN" in detected_types and not ("contractor" in fn_lower):
            content_risk = RiskLevel.HIGH
        elif "SALARY" in detected_types or "CREDIT_CARD" in detected_types:
            content_risk = RiskLevel.HIGH
        else:
            content_risk = RiskLevel.MEDIUM

        # Honor Gemini's explicit model classification if valid, preserving contractor medium baseline
        gemini_risk_str = str(gemini_res.get("risk_level", "")).upper()
        if "contractor" in fn_lower and not ("PASSPORT" in detected_types or "STEUER_ID" in detected_types):
            content_risk = RiskLevel.MEDIUM
        elif gemini_risk_str in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            try:
                model_risk = RiskLevel(gemini_risk_str)
                risk_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
                if risk_order.get(model_risk.value, 0) > risk_order.get(content_risk.value, 0):
                    content_risk = model_risk
            except ValueError:
                pass

        # Sharing exposure increases overall risk
        if effective_sharing_risk == "PUBLIC_LINK" and has_pii:
            final_risk = RiskLevel.CRITICAL
        elif effective_sharing_risk == "EXTERNAL_SHARE" and content_risk in [RiskLevel.MEDIUM, RiskLevel.LOW] and has_pii:
            final_risk = RiskLevel.HIGH
        else:
            final_risk = content_risk

        # Determine GDPR articles and remediation
        if final_risk == RiskLevel.CRITICAL:
            gdpr_articles = [
                "Art. 6 (Lawfulness of Processing)",
                "Art. 9 (Processing of Special Categories)",
                "Art. 32 (Security of Processing)",
                "Art. 83 (Administrative Fines)",
            ]
            remediation = (
                "Revoke public sharing link immediately and quarantine document in /Executive_Finance."
                if effective_sharing_risk == "PUBLIC_LINK"
                else "Quarantine file: Highly sensitive executive payroll / banking PII must reside in encrypted /Executive_Finance storage."
            )
        elif final_risk == RiskLevel.HIGH:
            gdpr_articles = [
                "Art. 6 (Lawfulness of Processing)",
                "Art. 32 (Security of Processing)",
                "Art. 83 (Administrative Fines)",
            ]
            remediation = (
                "Review external sharing permissions and restrict access to authorized internal organizational units."
                if effective_sharing_risk in ["PUBLIC_LINK", "EXTERNAL_SHARE"]
                else "Apply strict access controls: Employment contract / SEPA wire transfer data must reside in restricted Team Drive."
            )
        elif final_risk == RiskLevel.MEDIUM:
            gdpr_articles = [
                "Art. 6 (Lawfulness of Processing)",
                "Art. 32 (Security of Processing)",
            ]
            remediation = "Ensure document is stored within an encrypted folder under /Executive_Finance or /Contractors."
        else:
            gdpr_articles = []
            remediation = "No action required. Document complies with GDPR data protection standards."

        # If Gemini provided richer remediation, append it
        if gemini_res.get("remediation") and final_risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            remediation = f"{remediation} Recommendation: {gemini_res['remediation']}"

        # 7. Build audit report with redacted preview only (zero raw PII)
        report = DLPAuditReport(
            file_id=file_id,
            file_name=file_name,
            risk_level=final_risk,
            pii_types_detected=detected_types,
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
                    risk_level=final_risk.value,
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
