import pytest
from src.models.schemas import WorkspaceUser

def test_mock_admin_adapter_crud_operations():
    """Verify that MockAdminAdapter implements WorkspaceAdminPort backed by realistic fixtures."""
    from src.adapters.mock_admin_adapter import MockAdminAdapter
    
    adapter = MockAdminAdapter()
    
    # 1. List users
    users = adapter.list_users()
    assert len(users) >= 3
    assert any(u.primaryEmail == "cfo@client-enterprise.de" for u in users)
    
    # 2. Get single user
    cfo = adapter.get_user("cfo@client-enterprise.de")
    assert cfo is not None
    assert cfo.orgUnitPath == "/Executive_Finance"
    assert cfo.smimeConfigured is False
    
    non_existent = adapter.get_user("unknown@nowhere.de")
    assert non_existent is None
    
    # 3. List Org Units
    ous = adapter.list_org_units()
    assert len(ous) >= 3
    ou_paths = [ou.orgUnitPath for ou in ous]
    assert "/Executive_Finance" in ou_paths
    assert "/Engineering" in ou_paths
    
    # 4. List DLP rules
    rules = adapter.list_dlp_rules()
    assert len(rules) >= 2
    
    # 5. S/MIME status check
    assert adapter.get_smime_status("cfo@client-enterprise.de") is False
    assert adapter.get_smime_status("dev.lead@client-enterprise.de") is True
    
    # 6. Provision new user
    new_user = WorkspaceUser(
        id="usr_999",
        primaryEmail="new.hire@client-enterprise.de",
        name={"fullName": "Klaus Meyer"},
        orgUnitPath="/Engineering",
        isAdmin=False,
        isEnrolledIn2Sv=True,
        smimeConfigured=False
    )
    created = adapter.provision_user(new_user)
    assert created.id == "usr_999"
    assert adapter.get_user("new.hire@client-enterprise.de") is not None
