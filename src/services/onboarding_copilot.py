import hashlib
from typing import Optional, Dict, Any, List
from src.models.schemas import OnboardingRequest, OnboardingResult, WorkspaceUser
from src.ports.workspace_port import WorkspaceAdminPort, GeminiClassifierPort, WorkspaceDrivePort

class OnboardingCopilotService:
    """Automated zero-trust HR onboarding copilot assigning least-privilege OUs and security controls."""

    def __init__(
        self,
        admin_port: Optional[WorkspaceAdminPort] = None,
        gemini_port: Optional[GeminiClassifierPort] = None,
        drive_port: Optional[WorkspaceDrivePort] = None,
    ):
        self.admin_port = admin_port
        self.gemini_port = gemini_port
        self.drive_port = drive_port

    def evaluate_role(self, request: OnboardingRequest) -> Dict[str, Any]:
        """Determine least-privilege Organizational Unit, mandatory groups, and S/MIME requirement."""
        dept = (request.department or "").strip().lower()
        role = (request.jobTitle or "").strip().lower()

        if "finance" in dept or any(k in role for k in ["payroll", "tax", "cfo", "accountant"]):
            return {
                "ou": "/Executive_Finance",
                "groups": ["finance-team@client-enterprise.de", "all-staff@client-enterprise.de"],
                "smime_required": True,
            }
        elif "engineer" in dept or any(k in role for k in ["engineer", "developer", "devops", "cloud", "architect"]):
            return {
                "ou": "/Engineering",
                "groups": ["engineering-team@client-enterprise.de", "all-staff@client-enterprise.de"],
                "smime_required": False,
            }
        elif "contractor" in dept or any(k in role for k in ["contractor", "consultant", "vendor", "external"]):
            return {
                "ou": "/Contractors",
                "groups": ["contractors-ext@client-enterprise.de"],
                "smime_required": False,
            }
        return {
            "ou": "/",
            "groups": ["all-staff@client-enterprise.de"],
            "smime_required": False,
        }

    def provision_candidate(self, request: OnboardingRequest) -> OnboardingResult:
        """Evaluate candidate role, provision user account, and create security checklist."""
        evaluated = self.evaluate_role(request)
        user_id = f"usr_{hashlib.sha256(request.email.encode('utf-8')).hexdigest()[:8]}"

        candidate_user = WorkspaceUser(
            id=user_id,
            primaryEmail=request.email,
            name={"fullName": request.fullName},
            orgUnitPath=evaluated["ou"],
            isAdmin=False,
            isEnrolledIn2Sv=False,
            smimeConfigured=False,
        )

        if self.admin_port:
            created_user = self.admin_port.provision_user(candidate_user)
        else:
            created_user = candidate_user

        checklist_id = f"doc_welcome_{created_user.id}"

        return OnboardingResult(
            user=created_user,
            recommendedOrgUnitPath=evaluated["ou"],
            assignedGroups=evaluated["groups"],
            smimeRequired=evaluated["smime_required"],
            welcomeChecklistDocumentId=checklist_id,
        )

    def generate_security_checklist(self, result: OnboardingResult) -> str:
        """Generate a personalized markdown welcome security checklist for the new hire."""
        user = result.user
        full_name = (
            user.name.fullName
            if hasattr(user.name, "fullName")
            else (user.name.get("fullName") if isinstance(user.name, dict) else str(user.name))
        )
        smime_note = (
            "- [ ] **S/MIME Encryption Setup:** Mandatory for your Organizational Unit. Obtain key pair from IT Security."
            if result.smimeRequired
            else "- [ ] **S/MIME Encryption:** Optional for your role."
        )

        return f"""# Welcome to BuenaCloud Client Corp, {full_name}!

## Corporate Account Provisioning Details
- **Email:** {user.primaryEmail}
- **Assigned Organizational Unit (Least-Privilege):** {result.recommendedOrgUnitPath}
- **Assigned Security Groups:** {', '.join(result.assignedGroups)}

## Security Checklist
- [ ] **2-Step Verification (2SV):** Enroll a FIDO2 security key or Google Authenticator within 24 hours.
{smime_note}
- [ ] **Google Drive Sharing Standards:** Public links are forbidden. All documents with PII must reside in team drives.
- [ ] **Compliance Sign-Off:** Complete GDPR / DSGVO employee data privacy acknowledgement.
"""
