import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from src.ports.workspace_port import WorkspaceAdminPort
from src.models.schemas import WorkspaceUser, OrgUnit, DLPRule

logger = logging.getLogger("googleguard.mock_admin_adapter")

class MockAdminAdapter(WorkspaceAdminPort):
    """
    Mock adapter simulating Google Workspace Enterprise Admin SDK Directory & DLP APIs.
    Backed by local JSON fixtures with in-memory state tracking for user provisioning.
    """

    def __init__(self, fixtures_dir: Optional[str] = None):
        if fixtures_dir:
            self.fixtures_dir = Path(fixtures_dir)
        else:
            self.fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"
            
        self._users: Dict[str, WorkspaceUser] = {}
        self._org_units: List[OrgUnit] = []
        self._dlp_rules: List[DLPRule] = []
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        """Load JSON fixture files into memory."""
        # 1. Load users
        users_file = self.fixtures_dir / "mock_workspace_users.json"
        if users_file.exists():
            with open(users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    user = WorkspaceUser.model_validate(item)
                    self._users[user.primaryEmail.lower()] = user
        else:
            logger.warning("Users fixture not found at %s", users_file)

        # 2. Load Org Units
        ou_file = self.fixtures_dir / "mock_org_units.json"
        if ou_file.exists():
            with open(ou_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._org_units = [OrgUnit.model_validate(item) for item in data]
        else:
            logger.warning("Org units fixture not found at %s", ou_file)

        # 3. Load DLP Rules
        dlp_file = self.fixtures_dir / "mock_dlp_rules.json"
        if dlp_file.exists():
            with open(dlp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._dlp_rules = [DLPRule.model_validate(item) for item in data]
        else:
            logger.warning("DLP rules fixture not found at %s", dlp_file)

    def list_users(self) -> List[WorkspaceUser]:
        """Retrieve all users in the simulated tenant directory."""
        return list(self._users.values())

    def get_user(self, email: str) -> Optional[WorkspaceUser]:
        """Fetch a specific user by primary email."""
        return self._users.get(email.strip().lower())

    def list_org_units(self) -> List[OrgUnit]:
        """List all Organizational Units in the simulated tenant hierarchy."""
        return list(self._org_units)

    def list_dlp_rules(self) -> List[DLPRule]:
        """Retrieve active simulated Cloud Identity DLP rules."""
        return list(self._dlp_rules)

    def provision_user(self, user: WorkspaceUser) -> WorkspaceUser:
        """Provision or register a new user in the in-memory workspace directory."""
        email_key = user.primaryEmail.strip().lower()
        self._users[email_key] = user
        logger.info("Provisioned user in mock directory: %s (OU: %s)", email_key, user.orgUnitPath)
        return user

    def get_smime_status(self, email: str) -> bool:
        """Check whether S/MIME encryption certificates are configured for a user."""
        user = self.get_user(email)
        return bool(user.smimeConfigured) if user else False
