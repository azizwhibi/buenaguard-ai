import pytest
from src.ports.workspace_port import WorkspaceAdminPort
from src.adapters.mock_admin_adapter import MockAdminAdapter
from src.adapters.google_live_adapter import GoogleLiveAdapter

def test_factory_switching(monkeypatch):
    """Verify that AdapterFactory returns appropriate adapters based on configuration."""
    from src.adapters.factory import get_admin_adapter, get_drive_adapter
    
    # 1. Default / MOCK mode
    monkeypatch.setenv("WORKSPACE_MODE", "MOCK")
    admin_adapter = get_admin_adapter(mode="MOCK")
    assert isinstance(admin_adapter, WorkspaceAdminPort)
    assert isinstance(admin_adapter, MockAdminAdapter)
    
    # 2. Drive adapter returns an instance implementing required methods
    drive_adapter = get_drive_adapter()
    assert hasattr(drive_adapter, "list_drive_files")
    assert hasattr(drive_adapter, "get_drive_file_content")

    # 3. AuditStore and GeminiClient factory methods
    from src.adapters.factory import get_audit_store, get_gemini_client
    from src.ports.workspace_port import AuditStorePort, GeminiClassifierPort
    audit_store = get_audit_store()
    assert isinstance(audit_store, AuditStorePort)
    gemini_client = get_gemini_client()
    assert isinstance(gemini_client, GeminiClassifierPort)
