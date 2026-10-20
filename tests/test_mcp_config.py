import json
from pathlib import Path
import pytest

def test_mcp_config_schema_and_permissions():
    """Verify that .agents/mcp_config.json configures googleguard-workspace and sets granular permissions."""
    config_path = Path(".agents/mcp_config.json")
    assert config_path.exists(), ".agents/mcp_config.json must exist"

    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert "mcpServers" in data, "Config must contain 'mcpServers' root key"
    assert "googleguard-workspace" in data["mcpServers"], "Server 'googleguard-workspace' must be declared"

    server_cfg = data["mcpServers"]["googleguard-workspace"]
    assert "command" in server_cfg
    assert "args" in server_cfg
    assert any("workspace_mcp.py" in arg for arg in server_cfg["args"])

    # Verify script path exists
    for arg in server_cfg["args"]:
        if "workspace_mcp.py" in arg:
            script_path = Path(arg)
            assert script_path.exists(), f"Target MCP script {arg} must exist on disk"

    # Verify permissions allowlist
    permissions = data.get("permissions", [])
    expected_permissions = [
        "mcp(googleguard-workspace/check_domain_dlp_status)",
        "mcp(googleguard-workspace/list_workspace_ous)",
        "mcp(googleguard-workspace/scan_drive_file_dlp)",
        "mcp(googleguard-workspace/simulate_user_onboarding)",
    ]
    for perm in expected_permissions:
        assert perm in permissions, f"Missing required granular permission: {perm}"
