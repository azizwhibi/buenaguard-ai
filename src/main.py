import os
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src.config import settings
from src.models.schemas import (
    SecurityPostureReport,
    DLPAuditReport,
    OnboardingRequest,
    OnboardingResult,
)
from src.adapters.factory import (
    get_admin_adapter,
    get_drive_adapter,
    get_audit_store,
    get_gemini_client,
)
from src.services.dlp_scanner import DLPScannerService
from src.services.security_posture import SecurityPostureService
from src.services.onboarding_copilot import OnboardingCopilotService

app = FastAPI(
    title="BuenaGuard AI",
    description="Google Workspace Security, DLP & Onboarding Copilot for BuenaCloud GmbH",
    version="1.0.0",
)

# Setup Jinja2 templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize Hexagonal adapters via factory
admin_adapter = get_admin_adapter()
drive_adapter = get_drive_adapter()
audit_store = get_audit_store()
gemini_client = get_gemini_client()

# Initialize core domain services
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


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject defensive HTTP response headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


class ScanDLPRequest(BaseModel):
    file_id: str = Field(..., description="Target file id or filename")
    file_name: Optional[str] = None
    content: Optional[str] = None
    sharing_risk: Optional[str] = None


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Health status and current workspace mode."""
    return {
        "status": "ok",
        "mode": settings.WORKSPACE_MODE,
        "app": "BuenaGuard AI",
        "version": "1.0.0",
    }


@app.get("/api/v1/posture", response_model=SecurityPostureReport)
def get_security_posture() -> SecurityPostureReport:
    """Return tenant security compliance score, audited users, and flagged violations."""
    return posture_service.audit_tenant_posture()


@app.post("/api/v1/scan-dlp", response_model=DLPAuditReport)
def scan_dlp_document(request: ScanDLPRequest) -> DLPAuditReport:
    """Run regex pre-filtering, Gemini classification, and return redacted audit report."""
    file_id = request.file_id
    file_name = request.file_name or file_id
    content = request.content

    # Load content from sample docs fixture or drive port if omitted (strict path traversal prevention)
    if content is None:
        fixtures_dir = Path("fixtures/sample_docs").resolve()
        safe_name = Path(file_id).name
        target_path = (fixtures_dir / safe_name).resolve()
        if target_path.is_relative_to(fixtures_dir) and target_path.is_file():
            content = target_path.read_text(encoding="utf-8")
        else:
            content = drive_adapter.get_drive_file_content(file_id)

    return dlp_service.scan_document(
        file_id=file_id,
        file_name=file_name,
        content=content,
        sharing_risk=request.sharing_risk,
    )


@app.post("/api/v1/onboard", response_model=OnboardingResult)
def onboard_user(request: OnboardingRequest) -> OnboardingResult:
    """Evaluate role, provision user with least-privilege OU, and return security checklist."""
    return onboarding_service.provision_candidate(request)


@app.get("/api/v1/drive/files")
def list_drive_files() -> Any:
    """Return available Google Drive files from target drive_dlp_files folder."""
    return drive_adapter.list_drive_files(folder_name=settings.GOOGLE_DRIVE_DLP_FOLDER_NAME)


@app.get("/api/v1/auth/google/status")
def google_auth_status() -> Dict[str, Any]:
    """Return current Google OAuth authentication status."""
    if hasattr(drive_adapter, "_ensure_authenticated"):
        drive_adapter._ensure_authenticated()
    is_auth = getattr(drive_adapter, "is_authenticated", False)
    return {
        "authenticated": is_auth,
        "mode": settings.WORKSPACE_MODE,
        "token_exists": Path(settings.GOOGLE_OAUTH_TOKEN).exists(),
        "credentials_exists": Path(settings.GOOGLE_OAUTH_CREDENTIALS).exists(),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard_view(request: Request):
    """Serve responsive Tailwind CSS executive dashboard."""
    posture = posture_service.audit_tenant_posture()
    if hasattr(drive_adapter, "_ensure_authenticated"):
        drive_adapter._ensure_authenticated()
    is_auth = getattr(drive_adapter, "is_authenticated", False)
    drive_files = drive_adapter.list_drive_files(folder_name=settings.GOOGLE_DRIVE_DLP_FOLDER_NAME)
    sheet_rows = drive_adapter.read_sheet_rows(spreadsheet_id=settings.GOOGLE_ONBOARDING_SPREADSHEET_ID)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "posture": posture,
            "mode": settings.WORKSPACE_MODE,
            "is_authenticated": is_auth,
            "drive_files": drive_files,
            "sheet_rows": sheet_rows,
        },
    )
