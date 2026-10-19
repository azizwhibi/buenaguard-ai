import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import settings
from src.ports.workspace_port import WorkspaceDrivePort, WorkspaceSheetsPort

logger = logging.getLogger("buenaguard.google_live_adapter")

class GoogleLiveAdapter(WorkspaceDrivePort, WorkspaceSheetsPort):
    """
    Live Google Drive and Sheets API client using Desktop OAuth 2.0 flow.
    Enforces strictly read-only scopes and falls back to offline fixtures if credentials/tokens are absent.
    """

    SCOPES: List[str] = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    # Offline fixture documents simulating Google Drive files
    DEFAULT_OFFLINE_DOCUMENTS: List[Dict[str, Any]] = [
        {
            "id": "doc_contract_001",
            "name": "Arbeitsvertrag_Senior_Ingenieur_Schmidt.txt",
            "mimeType": "text/plain",
            "sharingRisk": "PUBLIC_LINK",
            "content": (
                "ARBEITSVERTRAG\n"
                "Zwischen der BuenaCloud Client Corp und Herrn Lukas Schmidt.\n"
                "Gehalt: 95.000 EUR p.a.\n"
                "Bankverbindung (IBAN): DE89370400440532013000\n"
                "Steuer-ID: 41234567890\n"
                "Sozialversicherungsnummer: 12 150785 S 004\n"
            )
        },
        {
            "id": "doc_notes_002",
            "name": "Weekly_Architecture_Sync_Notes.txt",
            "mimeType": "text/plain",
            "sharingRisk": "DOMAIN_INTERNAL",
            "content": (
                "Architecture Sync 2026-10-15:\n"
                "- Discussed migration of tenant to Google Workspace Enterprise.\n"
                "- Planned deployment of Gemini DLP scanner and S/MIME enforcement.\n"
                "- Next meeting scheduled for Thursday.\n"
            )
        },
        {
            "id": "doc_payroll_003",
            "name": "Gehaltsabrechnungen_Q3_Executive.csv",
            "mimeType": "text/csv",
            "sharingRisk": "EXTERNAL_SHARE",
            "content": (
                "Name,Rolle,IBAN,Steuer-ID,Gehalt\n"
                "Hannah Weber,CFO,DE21500500001234567890,11987654321,140000\n"
                "Marco Rossi,Contractor,IT60X0542811101000000123456,88123456789,75000\n"
            )
        }
    ]

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None
    ):
        self.credentials_path = credentials_path or settings.GOOGLE_OAUTH_CREDENTIALS
        self.token_path = token_path or settings.GOOGLE_OAUTH_TOKEN
        self.is_authenticated = False
        self.drive_service = None
        self.sheets_service = None
        self._initialize_credentials()

    def _initialize_credentials(self) -> None:
        """Attempt to load OAuth credentials and build services; gracefully fallback if offline."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                if creds and creds.valid:
                    self.drive_service = build("drive", "v3", credentials=creds)
                    self.sheets_service = build("sheets", "v4", credentials=creds)
                    self.is_authenticated = True
                    logger.info("Successfully connected to live Google Drive & Sheets APIs")
                    return
        except Exception as e:
            logger.debug("Live Google API init deferred (offline fallback): %s", str(e))
        
        self.is_authenticated = False
        logger.info("GoogleLiveAdapter running in offline / zero-billing fixture mode")

    def _ensure_authenticated(self) -> bool:
        """Dynamically reload credentials if token.json was generated after startup."""
        if not self.is_authenticated and os.path.exists(self.token_path):
            self._initialize_credentials()
        return self.is_authenticated

    def run_oauth_flow(self, port: int = 0) -> bool:
        """Run desktop InstalledAppFlow to authorize Google Drive & Sheets and save token.json."""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            if not os.path.exists(self.credentials_path):
                logger.error("Credentials file %s not found.", self.credentials_path)
                return False
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
            creds = flow.run_local_server(port=port)
            with open(self.token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
            self._initialize_credentials()
            return self.is_authenticated
        except Exception as e:
            logger.error("OAuth flow failed: %s", str(e))
            return False

    def list_drive_files(self) -> List[Dict[str, Any]]:
        """List files from Google Drive folder or return offline sample documents."""
        if self._ensure_authenticated() and self.drive_service:
            try:
                results = self.drive_service.files().list(
                    pageSize=30,
                    q="trashed = false",
                    fields="files(id, name, mimeType, permissions, webViewLink)"
                ).execute()
                items = results.get("files", [])
                if items:
                    files = []
                    for f in items:
                        sharing_risk = "DOMAIN_INTERNAL"
                        perms = f.get("permissions", [])
                        for p in perms:
                            if p.get("type") == "anyone":
                                sharing_risk = "PUBLIC_LINK"
                                break
                            elif p.get("role") in ["reader", "commenter", "writer"] and p.get("domain"):
                                sharing_risk = "EXTERNAL_SHARE"
                        files.append({
                            "id": f["id"],
                            "name": f["name"],
                            "mimeType": f["mimeType"],
                            "sharingRisk": sharing_risk,
                            "webViewLink": f.get("webViewLink")
                        })
                    return files
            except Exception as e:
                logger.warning("Error querying Google Drive API: %s. Using offline files.", str(e))
        
        return [
            {
                "id": doc["id"],
                "name": doc["name"],
                "mimeType": doc["mimeType"],
                "sharingRisk": doc.get("sharingRisk", "DOMAIN_INTERNAL")
            }
            for doc in self.DEFAULT_OFFLINE_DOCUMENTS
        ]

    def get_drive_file_content(self, file_id: str) -> str:
        """Retrieve plain text content of a Drive file or offline sample content."""
        if self._ensure_authenticated() and self.drive_service:
            try:
                meta = self.drive_service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
                mime = meta.get("mimeType", "")
                if mime == "application/vnd.google-apps.document":
                    content_bytes = self.drive_service.files().export_media(fileId=file_id, mimeType="text/plain").execute()
                    return content_bytes.decode("utf-8", errors="replace")
                elif mime == "application/vnd.google-apps.spreadsheet":
                    content_bytes = self.drive_service.files().export_media(fileId=file_id, mimeType="text/csv").execute()
                    return content_bytes.decode("utf-8", errors="replace")
                else:
                    content_bytes = self.drive_service.files().get_media(fileId=file_id).execute()
                    return content_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning("Error fetching live Drive file %s: %s", file_id, str(e))
        
        for doc in self.DEFAULT_OFFLINE_DOCUMENTS:
            if doc["id"] == file_id:
                return doc["content"]
        
        # Safe default fallback content with zero PII
        return f"Safe baseline document content for {file_id}. Zero sensitive PII present."

    def get_file_sharing_permissions(self, file_id: str) -> Dict[str, Any]:
        """Inspect file permissions for public or external sharing risks."""
        if self._ensure_authenticated() and self.drive_service:
            try:
                perms_res = self.drive_service.permissions().list(fileId=file_id, fields="permissions(id, type, role, domain)").execute()
                perms = perms_res.get("permissions", [])
                is_pub = any(p.get("type") == "anyone" for p in perms)
                is_ext = any(p.get("type") in ["user", "group", "domain"] and p.get("role") in ["reader", "commenter", "writer"] for p in perms)
                return {
                    "is_public": is_pub,
                    "is_external": is_ext and not is_pub,
                    "risk_classification": "PUBLIC_LINK" if is_pub else ("EXTERNAL_SHARE" if is_ext else "DOMAIN_INTERNAL")
                }
            except Exception as e:
                logger.warning("Live permission check for %s failed: %s", file_id, str(e))

        for doc in self.DEFAULT_OFFLINE_DOCUMENTS:
            if doc["id"] == file_id:
                risk = doc.get("sharingRisk", "DOMAIN_INTERNAL")
                return {
                    "is_public": risk == "PUBLIC_LINK",
                    "is_external": risk in ["PUBLIC_LINK", "EXTERNAL_SHARE"],
                    "risk_classification": risk
                }
        return {"is_public": False, "is_external": False, "risk_classification": "DOMAIN_INTERNAL"}

    def read_sheet_rows(self, spreadsheet_id: str, range_name: str = "A1:Z100") -> List[Dict[str, Any]]:
        """Read candidate rows from a Google Sheet or return sample onboarding records."""
        if self._ensure_authenticated() and self.sheets_service:
            try:
                res = self.sheets_service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name or "A1:Z100"
                ).execute()
                values = res.get("values", [])
                if values and len(values) > 1:
                    headers = [h.strip() for h in values[0]]
                    rows = []
                    for row in values[1:]:
                        row_dict = {}
                        for idx, header in enumerate(headers):
                            val = row[idx] if idx < len(row) else ""
                            row_dict[header] = val
                        rows.append(row_dict)
                    if rows:
                        return rows
            except Exception as e:
                logger.warning("Live sheet fetch %s failed (%s). Using sample rows.", spreadsheet_id, str(e))

        # Realistic sample German HR onboarding rows
        return [
            {
                "fullName": "Maximilian Bauer",
                "email": "m.bauer@client-enterprise.de",
                "department": "Finance",
                "jobTitle": "Senior Payroll & Tax Specialist",
                "manager": "Hannah Weber",
                "location": "Munich, Germany"
            },
            {
                "fullName": "Sophie Becker",
                "email": "s.becker@client-enterprise.de",
                "department": "Engineering",
                "jobTitle": "Cloud Infrastructure Engineer",
                "manager": "Lukas Schmidt",
                "location": "Berlin, Germany"
            },
            {
                "fullName": "Carlos Mendez",
                "email": "c.mendez@client-enterprise.de",
                "department": "Contractors",
                "jobTitle": "External Security Consultant",
                "manager": "Lukas Schmidt",
                "location": "Remote, Spain"
            }
        ]
