from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.models.schemas import WorkspaceUser, OrgUnit, DLPRule

class WorkspaceAdminPort(ABC):
    """Abstract port for Google Workspace Enterprise Admin SDK operations."""

    @abstractmethod
    def list_users(self) -> List[WorkspaceUser]:
        """Retrieve all users in the tenant directory."""
        pass

    @abstractmethod
    def get_user(self, email: str) -> Optional[WorkspaceUser]:
        """Fetch a specific user by primary email."""
        pass

    @abstractmethod
    def list_org_units(self) -> List[OrgUnit]:
        """List all Organizational Units in the tenant hierarchy."""
        pass

    @abstractmethod
    def list_dlp_rules(self) -> List[DLPRule]:
        """Retrieve active Cloud Identity DLP rules."""
        pass

    @abstractmethod
    def provision_user(self, user: WorkspaceUser) -> WorkspaceUser:
        """Provision or register a new user in the workspace directory."""
        pass

    @abstractmethod
    def get_smime_status(self, email: str) -> bool:
        """Check whether S/MIME encryption certificates are configured for a user."""
        pass

class WorkspaceDrivePort(ABC):
    """Abstract port for Google Drive and document scanning operations."""

    @abstractmethod
    def list_drive_files(self) -> List[Dict[str, Any]]:
        """List documents available for DLP scanning."""
        pass

    @abstractmethod
    def get_drive_file_content(self, file_id: str) -> str:
        """Retrieve plain text contents of a document."""
        pass

    @abstractmethod
    def get_file_sharing_permissions(self, file_id: str) -> Dict[str, Any]:
        """Inspect file sharing access and visibility."""
        pass

class WorkspaceSheetsPort(ABC):
    """Abstract port for Google Sheets reading and HR candidate intake."""

    @abstractmethod
    def read_sheet_rows(self, spreadsheet_id: str, range_name: str) -> List[Any]:
        """Read rows from a specified Google Sheet range."""
        pass

class GeminiClassifierPort(ABC):
    """Abstract port for Google AI Studio Gemini classification and policy reasoning."""

    @abstractmethod
    def classify_document(self, text: str) -> Dict[str, Any]:
        """Classify document sensitivity and extract DLP violations."""
        pass

    @abstractmethod
    def recommend_onboarding_ou(self, ticket: Any) -> Dict[str, Any]:
        """Analyze employee ticket and determine least-privilege OU and security flags."""
        pass

class AuditStorePort(ABC):
    """Abstract port for persistent, GDPR-compliant audit logging."""

    @abstractmethod
    def log_event(self, event_type: str, target_id: str, risk_level: str, content_hash: str) -> None:
        """Record an audit trail event with SHA-256 hash and zero raw PII."""
        pass

    @abstractmethod
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent audit events for compliance reporting."""
        pass
