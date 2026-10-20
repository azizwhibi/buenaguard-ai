import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "mode" in data

def test_security_posture_endpoint():
    response = client.get("/api/v1/posture")
    assert response.status_code == 200
    data = response.json()
    assert "complianceScore" in data
    assert "tenantDomain" in data
    assert "flaggedUsers" in data
    assert "remediationActions" in data
    assert len(data["flaggedUsers"]) > 0

def test_scan_dlp_endpoint_default_file():
    response = client.post("/api/v1/scan-dlp", json={"file_id": "contract_with_iban.txt"})
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == "contract_with_iban.txt"
    assert "risk_level" in data
    assert "pii_types_detected" in data
    assert "redacted_preview" in data
    # GDPR Rule 4: Zero raw PII in output
    assert "DE89 3704 0044 0532 0130 00" not in data["redacted_preview"]

def test_scan_dlp_endpoint_clean_content():
    payload = {
        "file_id": "clean_notes.txt",
        "file_name": "clean_notes.txt",
        "content": "This is a clean corporate memo without any financial or personal secrets.",
        "sharing_risk": "DOMAIN_INTERNAL"
    }
    response = client.post("/api/v1/scan-dlp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "LOW"
    assert len(data["pii_types_detected"]) == 0

def test_scan_dlp_endpoint_drive_adapter_fallback():
    # doc_notes_002 is registered in DEFAULT_OFFLINE_DOCUMENTS with sharingRisk: DOMAIN_INTERNAL
    response = client.post("/api/v1/scan-dlp", json={"file_id": "doc_notes_002"})
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == "doc_notes_002"
    assert data["sharing_permission_risk"] == "DOMAIN_INTERNAL"

    # doc_payroll_003 is registered in DEFAULT_OFFLINE_DOCUMENTS with sharingRisk: EXTERNAL_SHARE
    response_ext = client.post("/api/v1/scan-dlp", json={"file_id": "doc_payroll_003"})
    assert response_ext.status_code == 200
    data_ext = response_ext.json()
    assert data_ext["sharing_permission_risk"] == "EXTERNAL_SHARE"

def test_onboard_endpoint():
    payload = {
        "fullName": "Sarah Connor",
        "email": "sarah.connor@client-enterprise.de",
        "department": "Finance & Accounting",
        "jobTitle": "Payroll Specialist",
        "manager": "Hannah Weber",
        "location": "Munich"
    }
    response = client.post("/api/v1/onboard", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommendedOrgUnitPath"] == "/Executive_Finance"
    assert data["smimeRequired"] is True
    assert "finance-team@client-enterprise.de" in data["assignedGroups"]
    assert "welcomeChecklistDocumentId" in data

def test_dashboard_html_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "GoogleGuard AI" in response.text
    # Verify security headers
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"

def test_scan_dlp_path_traversal_prevention():
    # Attempting directory traversal via file_id must not leak files outside fixtures/sample_docs
    response = client.post("/api/v1/scan-dlp", json={"file_id": "../../geminiapikey.txt"})
    assert response.status_code == 200
    data = response.json()
    # Content should not be the secret API key
    assert "AIzaSy" not in data["redacted_preview"]

def test_onboard_endpoint_validation_error_422():
    response = client.post("/api/v1/onboard", json={})
    assert response.status_code == 422

def test_drive_files_endpoint():
    response = client.get("/api/v1/drive/files")
    assert response.status_code == 200
    files = response.json()
    assert isinstance(files, list)
    assert len(files) > 0
    assert "id" in files[0]
    assert "name" in files[0]

def test_google_auth_status_endpoint():
    response = client.get("/api/v1/auth/google/status")
    assert response.status_code == 200
    data = response.json()
    assert "authenticated" in data
    assert "mode" in data
    assert "credentials_exists" in data

