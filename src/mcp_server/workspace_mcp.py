"""
Google Workspace Security & IAM Administrative MCP Server.
Exposes standard stdio MCP tools directly to Antigravity and AI agents.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

try:
    from mcp.server.mcpserver import MCPServer
    FastMCP = MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP

from src.adapters.factory import (
    get_admin_adapter,
    get_drive_adapter,
    get_audit_store,
    get_gemini_client,
)
from src.services.dlp_scanner import DLPScannerService
from src.services.security_posture import SecurityPostureService
from src.services.onboarding_copilot import OnboardingCopilotService
from src.models.schemas import OnboardingRequest

# Initialize MCP server
mcp = FastMCP("buenaguard-workspace")

# Wire Hexagonal ports and core domain services via factory
admin_adapter = get_admin_adapter()
drive_adapter = get_drive_adapter()
audit_store = get_audit_store()
gemini_client = get_gemini_client()

posture_service = SecurityPostureService(admin_port=admin_adapter)
dlp_service = DLPScannerService(
    drive_port=drive_adapter,
    gemini_port=gemini_client,
    audit_store=audit_store,
)
onboarding_service = OnboardingCopilotService(
    admin_port=admin_adapter,
    gemini_port=gemini_client,
    drive_port=drive_adapter,
)


@mcp.tool()
def check_domain_dlp_status(domain: str = "client-enterprise.de") -> str:
    """
    Check the overall Google Workspace domain security posture, S/MIME adoption,
    2-Step Verification (2SV) enforcement, and flagged non-compliant accounts.
    """
    report = posture_service.audit_tenant_posture(domain=domain)
    return report.model_dump_json(indent=2)


@mcp.tool()
def list_workspace_ous() -> str:
    """
    List all Google Workspace Organizational Units (OUs) and their assigned
    security policies (S/MIME requirements, 2SV enforcement, DLP rules).
    """
    ous = admin_adapter.list_org_units()
    return json.dumps([ou.model_dump() for ou in ous], indent=2)


@mcp.tool()
def scan_drive_file_dlp(file_id: str) -> str:
    """
    Scan a Google Drive document for European/German PII (IBAN, Steuer-ID, passport, salaries),
    classify GDPR regulatory risk, and return a redacted compliance audit report with zero raw PII.
    """
    # Safe resolution preventing path traversal
    fixtures_dir = Path("fixtures/sample_docs").resolve()
    safe_name = Path(file_id).name
    target_path = (fixtures_dir / safe_name).resolve()

    if target_path.is_relative_to(fixtures_dir) and target_path.is_file():
        content = target_path.read_text(encoding="utf-8")
    else:
        content = drive_adapter.get_drive_file_content(file_id)

    report = dlp_service.scan_document(
        file_id=file_id,
        file_name=safe_name,
        content=content,
    )
    return report.model_dump_json(indent=2)


@mcp.tool()
def simulate_user_onboarding(name: str, role: str, department: str) -> str:
    """
    Simulate zero-trust HR candidate onboarding: evaluates candidate role and department,
    determines least-privilege Organizational Unit, assigns mandatory Google Groups,
    and returns provisioning details and security checklist.
    """
    sanitized_email = f"{name.lower().replace(' ', '.')}@client-enterprise.de"
    request = OnboardingRequest(
        fullName=name,
        email=sanitized_email,
        department=department,
        jobTitle=role,
        manager="Hannah Weber",
        location="Munich, Germany",
    )
    result = onboarding_service.provision_candidate(request)
    return result.model_dump_json(indent=2)


if __name__ == "__main__":
    mcp.run()
