import json
import os
import pytest
from src.models.schemas import OrgUnit, WorkspaceUser, DLPRule, OnboardingRequest

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")

def test_fixture_schema_conformance():
    """Verify that all JSON fixtures exist and strictly conform to domain Pydantic models."""
    # 1. Org Units Fixture
    org_units_path = os.path.join(FIXTURES_DIR, "mock_org_units.json")
    assert os.path.exists(org_units_path), "mock_org_units.json must exist"
    with open(org_units_path, "r", encoding="utf-8") as f:
        org_units_data = json.load(f)
    assert len(org_units_data) >= 3
    org_units = [OrgUnit.model_validate(item) for item in org_units_data]
    ou_paths = [ou.orgUnitPath for ou in org_units]
    assert "/" in ou_paths
    assert "/Executive_Finance" in ou_paths
    assert "/Engineering" in ou_paths
    assert "/Contractors" in ou_paths

    # 2. Workspace Users Fixture
    users_path = os.path.join(FIXTURES_DIR, "mock_workspace_users.json")
    assert os.path.exists(users_path), "mock_workspace_users.json must exist"
    with open(users_path, "r", encoding="utf-8") as f:
        users_data = json.load(f)
    assert len(users_data) >= 3
    users = [WorkspaceUser.model_validate(item) for item in users_data]
    emails = {u.primaryEmail: u for u in users}
    
    assert "cfo@client-enterprise.de" in emails
    assert emails["cfo@client-enterprise.de"].smimeConfigured is False
    assert emails["cfo@client-enterprise.de"].orgUnitPath == "/Executive_Finance"

    assert "dev.lead@client-enterprise.de" in emails
    assert emails["dev.lead@client-enterprise.de"].isAdmin is True

    # 3. DLP Rules Fixture
    dlp_path = os.path.join(FIXTURES_DIR, "mock_dlp_rules.json")
    assert os.path.exists(dlp_path), "mock_dlp_rules.json must exist"
    with open(dlp_path, "r", encoding="utf-8") as f:
        dlp_data = json.load(f)
    assert len(dlp_data) >= 2
    [DLPRule.model_validate(item) for item in dlp_data]

    # 4. Onboarding Requests Fixture
    onboarding_path = os.path.join(FIXTURES_DIR, "onboarding_requests.json")
    assert os.path.exists(onboarding_path), "onboarding_requests.json must exist"
    with open(onboarding_path, "r", encoding="utf-8") as f:
        onboarding_data = json.load(f)
    assert len(onboarding_data) >= 1
    [OnboardingRequest.model_validate(item) for item in onboarding_data]

def test_sample_docs_exist_and_contain_synthetic_pii():
    """Verify that sample docs contain representative synthetic German PII for DLP testing."""
    sample_docs_dir = os.path.join(FIXTURES_DIR, "sample_docs")
    assert os.path.exists(sample_docs_dir), "fixtures/sample_docs/ directory must exist"

    contract_path = os.path.join(sample_docs_dir, "contract_with_iban.txt")
    assert os.path.exists(contract_path)
    with open(contract_path, "r", encoding="utf-8") as f:
        contract_text = f.read()
    assert "DE89" in contract_text or "IBAN" in contract_text

    tax_id_path = os.path.join(sample_docs_dir, "tax_id_export.csv")
    assert os.path.exists(tax_id_path)

    clean_notes_path = os.path.join(sample_docs_dir, "clean_notes.txt")
    assert os.path.exists(clean_notes_path)
