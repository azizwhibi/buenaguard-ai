import pytest
from pydantic import ValidationError

def test_workspace_schemas_validation():
    """Verify that Pydantic v2 schemas strictly validate domain entities."""
    from src.models.schemas import (
        RiskLevel,
        OrgUnit,
        WorkspaceUser,
        DLPRule,
        DLPAuditReport,
        OnboardingRequest,
        OnboardingResult,
        SecurityPostureReport
    )

    # 1. OrgUnit validation
    ou = OrgUnit(
        name="Executive & Finance",
        orgUnitPath="/Executive_Finance",
        description="Strict DLP, Mandatory S/MIME, 2SV Required",
        policies={"smime_required": True, "two_step_verification": True, "external_drive_sharing": "BLOCKED"}
    )
    assert ou.orgUnitPath == "/Executive_Finance"
    assert ou.policies["smime_required"] is True

    # 2. WorkspaceUser validation
    user = WorkspaceUser(
        id="usr_101",
        primaryEmail="cfo@client-enterprise.de",
        name={"fullName": "Hannah Weber"},
        orgUnitPath="/Executive_Finance",
        isAdmin=False,
        isEnrolledIn2Sv=True,
        smimeConfigured=False
    )
    assert user.id == "usr_101"
    assert user.primaryEmail == "cfo@client-enterprise.de"
    assert user.name["fullName"] == "Hannah Weber"
    assert user.smimeConfigured is False

    # 3. DLPAuditReport validation
    report = DLPAuditReport(
        file_id="doc_101",
        file_name="Employment_Contract.txt",
        risk_level=RiskLevel.CRITICAL,
        pii_types_detected=["IBAN", "Steuer-ID"],
        gdpr_articles_impacted=["Art. 6", "Art. 9"],
        sharing_permission_risk="PUBLIC_LINK",
        recommended_remediation="Revoke public link and move to /Confidential OU",
        content_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        redacted_preview="Contract excerpt with [REDACTED_IBAN]"
    )
    assert report.risk_level == RiskLevel.CRITICAL
    assert "IBAN" in report.pii_types_detected

    # 4. OnboardingRequest validation
    req = OnboardingRequest(
        fullName="Maximilian Bauer",
        email="m.bauer@client-enterprise.de",
        department="Finance",
        jobTitle="Senior Payroll Specialist",
        manager="Hannah Weber",
        location="Munich, Germany"
    )
    assert req.jobTitle == "Senior Payroll Specialist"

    # 5. Invalid RiskLevel raises ValidationError
    with pytest.raises(ValidationError):
        DLPAuditReport(
            file_id="doc_102",
            file_name="Notes.txt",
            risk_level="EXTREME_DANGER",  # Invalid enum value
            sharing_permission_risk="NONE",
            recommended_remediation="None",
            content_hash_sha256="abc",
            redacted_preview="clean"
        )

def test_workspace_ports_interface_contract():
    """Verify that abstract ports define expected abstract methods."""
    from src.ports.workspace_port import WorkspaceAdminPort, WorkspaceDrivePort
    import inspect

    admin_methods = dict(inspect.getmembers(WorkspaceAdminPort, predicate=inspect.isfunction))
    assert "list_users" in admin_methods
    assert "get_user" in admin_methods
    assert "list_org_units" in admin_methods
    assert "list_dlp_rules" in admin_methods
    assert "provision_user" in admin_methods
    assert "get_smime_status" in admin_methods

    drive_methods = dict(inspect.getmembers(WorkspaceDrivePort, predicate=inspect.isfunction))
    assert "list_drive_files" in drive_methods
    assert "get_drive_file_content" in drive_methods
    assert "get_file_sharing_permissions" in drive_methods
