import pytest
from src.models.schemas import OnboardingRequest, OnboardingResult, WorkspaceUser
from src.services.onboarding_copilot import OnboardingCopilotService
from src.adapters.mock_admin_adapter import MockAdminAdapter

def test_onboarding_copilot_least_privilege_ou_assignment():
    """Verify OnboardingCopilot assigns Finance candidate to /Executive_Finance with S/MIME."""
    admin_adapter = MockAdminAdapter()
    copilot = OnboardingCopilotService(admin_port=admin_adapter)
    
    candidate = OnboardingRequest(
        fullName="Maximilian Bauer",
        email="m.bauer@client-enterprise.de",
        department="Finance",
        jobTitle="Senior Payroll & Tax Specialist",
        manager="Hannah Weber",
        location="Munich, Germany"
    )
    
    result = copilot.provision_candidate(candidate)
    
    assert isinstance(result, OnboardingResult)
    assert result.recommendedOrgUnitPath == "/Executive_Finance"
    assert result.smimeRequired is True
    assert "finance-team@client-enterprise.de" in result.assignedGroups
    assert result.welcomeChecklistDocumentId is not None
    
    # Verify user was provisioned into admin adapter store
    stored_user = admin_adapter.get_user("m.bauer@client-enterprise.de")
    assert stored_user is not None
    assert stored_user.orgUnitPath == "/Executive_Finance"
    assert stored_user.primaryEmail == "m.bauer@client-enterprise.de"

def test_onboarding_copilot_contractor_assignment():
    """Verify Contractor candidate is assigned to /Contractors without S/MIME."""
    admin_adapter = MockAdminAdapter()
    copilot = OnboardingCopilotService(admin_port=admin_adapter)
    
    contractor = OnboardingRequest(
        fullName="Carlos Mendez",
        email="c.mendez@client-enterprise.de",
        department="Contractors",
        jobTitle="External Security Consultant",
        manager="Lukas Schmidt",
        location="Remote, Spain"
    )
    
    result = copilot.provision_candidate(contractor)
    
    assert result.recommendedOrgUnitPath == "/Contractors"
    assert result.smimeRequired is False
    assert "contractors-ext@client-enterprise.de" in result.assignedGroups
    
    stored = admin_adapter.get_user("c.mendez@client-enterprise.de")
    assert stored is not None
    assert stored.orgUnitPath == "/Contractors"

def test_onboarding_copilot_checklist_generation():
    """Verify personalized welcome security checklist contains candidate specifics."""
    copilot = OnboardingCopilotService()
    candidate = OnboardingRequest(
        fullName="Sophie Becker",
        email="s.becker@client-enterprise.de",
        department="Engineering",
        jobTitle="Cloud Infrastructure Engineer",
        manager="Lukas Schmidt",
        location="Berlin, Germany"
    )
    
    result = copilot.provision_candidate(candidate)
    checklist = copilot.generate_security_checklist(result)
    
    assert "Sophie Becker" in checklist
    assert "/Engineering" in checklist
    assert "2-Step Verification" in checklist

def test_onboarding_copilot_unrecognized_role_fallback_to_root_ou():
    """Verify fallback to root OU '/' for unspecified/general corporate departments."""
    copilot = OnboardingCopilotService()
    general = OnboardingRequest(
        fullName="Anna Frank",
        email="a.frank@client-enterprise.de",
        department="Marketing",
        jobTitle="Growth Marketing Lead",
        manager="General Manager",
        location="Frankfurt"
    )
    result = copilot.provision_candidate(general)
    assert result.recommendedOrgUnitPath == "/"
    assert result.smimeRequired is False
    assert "all-staff@client-enterprise.de" in result.assignedGroups

def test_onboarding_copilot_finance_smime_checklist_note():
    """Verify mandatory S/MIME checklist item generated for Finance candidates."""
    copilot = OnboardingCopilotService()
    finance_req = OnboardingRequest(
        fullName="Klaus Meyer",
        email="k.meyer@client-enterprise.de",
        department="Finance",
        jobTitle="Treasurer",
        manager="Hannah Weber",
        location="Munich"
    )
    result = copilot.provision_candidate(finance_req)
    checklist = copilot.generate_security_checklist(result)
    assert "S/MIME Encryption Setup" in checklist
    assert "Mandatory for your Organizational Unit" in checklist

