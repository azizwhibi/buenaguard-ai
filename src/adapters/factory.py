from typing import Optional
from src.config import settings
from src.ports.workspace_port import WorkspaceAdminPort, WorkspaceDrivePort, AuditStorePort
from src.adapters.mock_admin_adapter import MockAdminAdapter
from src.adapters.google_live_adapter import GoogleLiveAdapter
from src.adapters.audit_store import AuditStore
from src.adapters.gemini_client import GeminiClient

def get_admin_adapter(mode: Optional[str] = None) -> WorkspaceAdminPort:
    """Return appropriate WorkspaceAdminPort adapter based on mode or settings."""
    active_mode = mode or settings.WORKSPACE_MODE
    if active_mode.upper() == "MOCK":
        return MockAdminAdapter()
    return MockAdminAdapter()

def get_drive_adapter() -> WorkspaceDrivePort:
    """Return Google Drive adapter with read-only scopes and offline fallback."""
    return GoogleLiveAdapter()

def get_audit_store(db_path: Optional[str] = None) -> AuditStorePort:
    """Return AuditStorePort implementation."""
    return AuditStore(db_path=db_path)

def get_gemini_client() -> GeminiClient:
    """Return GeminiClient wrapper."""
    return GeminiClient()
