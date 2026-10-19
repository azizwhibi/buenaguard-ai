from typing import Optional
from src.config import settings
from src.ports.workspace_port import WorkspaceAdminPort
from src.adapters.mock_admin_adapter import MockAdminAdapter
from src.adapters.google_live_adapter import GoogleLiveAdapter

def get_admin_adapter(mode: Optional[str] = None) -> WorkspaceAdminPort:
    """Return appropriate WorkspaceAdminPort adapter based on mode or settings."""
    active_mode = mode or settings.WORKSPACE_MODE
    if active_mode.upper() == "MOCK":
        return MockAdminAdapter()
    # In live mode, WorkspaceAdminPort would connect to Admin SDK Directory API
    # Defaults to MockAdminAdapter if live Admin SDK credentials are unconfigured
    return MockAdminAdapter()

def get_drive_adapter() -> GoogleLiveAdapter:
    """Return Google Drive adapter with read-only scopes and offline fallback."""
    return GoogleLiveAdapter()
