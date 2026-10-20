import sys
import pytest
from abc import ABC
from pydantic import ValidationError

def test_models_import_and_validation():
    """Verify core Pydantic v2 domain models can be instantiated and validated."""
    from src.models import (
        DLPRiskLevel,
        ScanResult,
        OnboardingTicket,
        ProvisioningPlan,
    )

    # 1. DLPRiskLevel Enum
    assert DLPRiskLevel.LOW == "LOW"
    assert DLPRiskLevel.CRITICAL == "CRITICAL"

    # 2. ScanResult
    scan = ScanResult(
        file_id="drive_doc_1",
        file_name="Contract_DE.pdf",
        risk_level=DLPRiskLevel.HIGH,
        pii_detected=["IBAN", "Steuer-ID"],
        content_hash="abc123sha256",
        redacted_preview="Preview [REDACTED_IBAN_1]",
    )
    assert scan.file_id == "drive_doc_1"
    assert scan.risk_level == DLPRiskLevel.HIGH

    # Negative validation
    with pytest.raises(ValidationError):
        ScanResult(
            file_id="drive_doc_1",
            file_name="Contract_DE.pdf",
            risk_level="INVALID_LEVEL",  # Invalid enum value
            pii_detected=[],
            content_hash="abc",
            redacted_preview="",
        )

    # 3. OnboardingTicket
    ticket = OnboardingTicket(
        candidate_name="Lukas Weber",
        email="lukas.weber@googleguard.de",
        role="DevOps Engineer",
        department="Engineering",
        manager_email="cto@googleguard.de",
    )
    assert ticket.candidate_name == "Lukas Weber"

    # 4. ProvisioningPlan
    plan = ProvisioningPlan(
        user_email="lukas.weber@googleguard.de",
        target_ou="/Engineering",
        assigned_groups=["devops-team@googleguard.de", "all-staff@googleguard.de"],
        smime_required=True,
    )
    assert plan.target_ou == "/Engineering"
    assert plan.smime_required is True

def test_abstract_ports_contracts():
    """Verify abstract ports define required interfaces without concrete implementations."""
    from src.ports import (
        WorkspaceDrivePort,
        WorkspaceSheetsPort,
        WorkspaceAdminPort,
        GeminiClassifierPort,
        AuditStorePort,
    )

    # All ports must be abstract ABCs
    ports = [
        WorkspaceDrivePort,
        WorkspaceSheetsPort,
        WorkspaceAdminPort,
        GeminiClassifierPort,
        AuditStorePort,
    ]
    for port_cls in ports:
        assert issubclass(port_cls, ABC)
        # Instantiation without implementing abstract methods must raise TypeError
        with pytest.raises(TypeError):
            port_cls()

    # Verify method contracts
    assert hasattr(WorkspaceDrivePort, "list_drive_files")
    assert hasattr(WorkspaceDrivePort, "get_drive_file_content")
    assert hasattr(WorkspaceSheetsPort, "read_sheet_rows")
    assert hasattr(WorkspaceAdminPort, "list_users")
    assert hasattr(WorkspaceAdminPort, "provision_user")
    assert hasattr(GeminiClassifierPort, "classify_document")
    assert hasattr(AuditStorePort, "log_event")

def test_hexagonal_boundary_cleanliness():
    """Verify that domain models and ports do not import any concrete adapters."""
    import src.models
    import src.ports

    # Ensure adapters module was not imported as a dependency of models or ports
    loaded_modules = sys.modules.keys()
    adapter_submodules = [
        m for m in loaded_modules if m.startswith("src.adapters.")
    ]
    # If any adapter is loaded, inspect if it's imported by src.models or src.ports
    for mod_name in ["src.models", "src.ports"]:
        mod = sys.modules.get(mod_name)
        if mod:
            assert not hasattr(mod, "MockAdminAdapter")
            assert not hasattr(mod, "GoogleLiveAdapter")
            assert not hasattr(mod, "AuditStore")
