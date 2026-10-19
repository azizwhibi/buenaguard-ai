import pytest
import json
from src.mcp_server.workspace_mcp import mcp

@pytest.mark.anyio
async def test_mcp_tools_registration():
    """Verify that the 4 administrative tools are properly registered on MCPServer."""
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    expected_tools = {
        "check_domain_dlp_status",
        "list_workspace_ous",
        "scan_drive_file_dlp",
        "simulate_user_onboarding",
    }
    assert expected_tools.issubset(tool_names)

@pytest.mark.anyio
async def test_tool_check_domain_dlp_status():
    """Verify check_domain_dlp_status returns compliance metrics and flagged violations."""
    result = await mcp.call_tool("check_domain_dlp_status", {"domain": "client-enterprise.de"})
    assert result.is_error is False
    content_text = result.content[0].text
    data = json.loads(content_text) if isinstance(content_text, str) else content_text
    assert "complianceScore" in data
    assert "flaggedUsers" in data
    assert data["tenantDomain"] == "client-enterprise.de"

@pytest.mark.anyio
async def test_tool_list_workspace_ous():
    """Verify list_workspace_ous returns all enterprise organizational units and policies."""
    result = await mcp.call_tool("list_workspace_ous", {})
    assert result.is_error is False
    content_text = result.content[0].text
    data = json.loads(content_text) if isinstance(content_text, str) else content_text
    assert isinstance(data, list)
    ou_paths = [ou.get("orgUnitPath") for ou in data]
    assert "/Executive_Finance" in ou_paths
    assert "/Engineering" in ou_paths
    assert "/Contractors" in ou_paths

@pytest.mark.anyio
async def test_tool_scan_drive_file_dlp():
    """Verify scan_drive_file_dlp evaluates PII and ensures zero raw PII in output."""
    result = await mcp.call_tool("scan_drive_file_dlp", {"file_id": "contract_with_iban.txt"})
    assert result.is_error is False
    content_text = result.content[0].text
    data = json.loads(content_text) if isinstance(content_text, str) else content_text
    assert data["file_id"] == "contract_with_iban.txt"
    assert "risk_level" in data
    assert "pii_types_detected" in data
    assert "redacted_preview" in data
    # GDPR Rule 4: Verify zero raw IBAN leakage in output
    assert "DE89 3704 0044 0532 0130 00" not in data["redacted_preview"]

@pytest.mark.anyio
async def test_tool_simulate_user_onboarding():
    """Verify simulate_user_onboarding maps role to least-privilege OU and groups."""
    result = await mcp.call_tool("simulate_user_onboarding", {
        "name": "Alex Mercer",
        "role": "Lead Site Reliability Engineer",
        "department": "Engineering"
    })
    assert result.is_error is False
    content_text = result.content[0].text
    data = json.loads(content_text) if isinstance(content_text, str) else content_text
    assert data["recommendedOrgUnitPath"] == "/Engineering"
    assert data["smimeRequired"] is False
    assert "engineering-team@client-enterprise.de" in data["assignedGroups"]

def test_workspace_mcp_stdio_handshake():
    """Verify MCP server starts over stdio transport and completes protocol handshake."""
    import subprocess
    import os
    import sys

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["WORKSPACE_MODE"] = "MOCK"

    proc = subprocess.Popen(
        [sys.executable, "-u", "src/mcp_server/workspace_mcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }

    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()

    try:
        stdout, _ = proc.communicate(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()

    assert "buenaguard-workspace" in stdout
    assert "2024-11-05" in stdout

