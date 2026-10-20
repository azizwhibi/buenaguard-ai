import pytest
from src.models.schemas import SecurityPostureReport
from src.services.security_posture import SecurityPostureService
from src.adapters.mock_admin_adapter import MockAdminAdapter

def test_security_posture_score_calculation():
    """Verify security posture auditor identifies policy gaps and computes compliance score."""
    admin_adapter = MockAdminAdapter()
    service = SecurityPostureService(admin_port=admin_adapter)
    
    report = service.audit_tenant_posture(domain="client-enterprise.de")
    
    assert isinstance(report, SecurityPostureReport)
    assert report.tenantDomain == "client-enterprise.de"
    assert report.totalUsers == 4
    assert report.enrolledIn2SvCount == 3  # 3 of 4 enrolled
    assert report.smimeConfiguredCount == 2  # 2 of 4 have S/MIME
    
    # Assert flagged users
    flagged_emails = [u["email"] for u in report.flaggedUsers]
    assert "cfo@client-enterprise.de" in flagged_emails
    assert "temp.vendor@client-enterprise.de" in flagged_emails
    
    # Assert specific violation reasons
    cfo_flag = next(u for u in report.flaggedUsers if u["email"] == "cfo@client-enterprise.de")
    assert "SMIME" in cfo_flag["reason"]
    
    vendor_flag = next(u for u in report.flaggedUsers if u["email"] == "temp.vendor@client-enterprise.de")
    assert "2SV" in vendor_flag["reason"]
    
    # Score must be between 0 and 100
    assert 0.0 <= report.complianceScore <= 100.0
    assert report.complianceScore < 100.0  # Due to policy gaps
    
    # Prioritized remediation actions
    assert len(report.remediationActions) >= 2
    assert any("cfo@client-enterprise.de" in action for action in report.remediationActions)
    assert any("temp.vendor@client-enterprise.de" in action for action in report.remediationActions)

def test_security_posture_empty_or_no_admin_port():
    """Verify safe fallback when admin port is not configured."""
    service = SecurityPostureService(admin_port=None)
    report = service.audit_tenant_posture(domain="fallback-domain.com")
    assert report.complianceScore == 100.0
    assert report.totalUsers == 0
    assert len(report.flaggedUsers) == 0

def test_security_posture_from_live_candidate_rows():
    """Verify security posture auditor dynamically evaluates candidate rows from Google Sheets."""
    rows = [
        {"fullName": "Hannah Weber", "email": "hannah.weber@googleguard.de", "department": "Finance", "jobTitle": "Chief Financial Officer (CFO)"},
        {"fullName": "Lukas Schmidt", "email": "l.schmidt@googleguard.de", "department": "Engineering", "jobTitle": "Lead Architect"},
        {"fullName": "Carlos Mendez", "email": "c.mendez@googleguard.de", "department": "Contractors", "jobTitle": "External Pentester"},
    ]
    users = SecurityPostureService.users_from_candidate_rows(rows)
    assert len(users) == 3
    assert users[0].orgUnitPath == "/Executive_Finance"
    assert users[1].orgUnitPath == "/Engineering"
    assert users[2].orgUnitPath == "/Contractors"

    service = SecurityPostureService()
    report = service.audit_tenant_posture(users=users)
    assert report.tenantDomain == "googleguard.de"
    assert report.totalUsers == 3
    flagged = [u["email"] for u in report.flaggedUsers]
    assert "hannah.weber@googleguard.de" in flagged
    assert "c.mendez@googleguard.de" in flagged


