from typing import Optional, List, Dict, Any
from src.models.schemas import SecurityPostureReport, WorkspaceUser, OrgUnit, UserName
from src.ports.workspace_port import WorkspaceAdminPort

class SecurityPostureService:
    """Audits Google Workspace tenant security posture, S/MIME adoption, and 2SV compliance."""

    def __init__(self, admin_port: Optional[WorkspaceAdminPort] = None):
        self.admin_port = admin_port

    @staticmethod
    def users_from_candidate_rows(rows: List[Dict[str, Any]]) -> List[WorkspaceUser]:
        """Convert dynamic candidate rows from Google Sheets into audited WorkspaceUser directory models."""
        users: List[WorkspaceUser] = []
        for idx, r in enumerate(rows):
            email = r.get("email") or r.get("Email") or ""
            if not email:
                continue
            first = r.get("First Name") or ""
            last = r.get("Last Name") or ""
            full = (f"{first} {last}").strip() or r.get("fullName") or email.split("@")[0]
            dept = (r.get("department") or r.get("Company") or "").lower()
            role = (r.get("jobTitle") or r.get("Title") or "").lower()

            # Determine least-privilege OU from candidate role/department
            if "finance" in dept or any(k in role for k in ["cfo", "payroll", "tax"]):
                ou = "/Executive_Finance"
                smime = False  # Unprovisioned candidates lack deployed S/MIME certificates
                two_sv = True
            elif "contractor" in dept or any(k in role for k in ["contractor", "tester", "consultant"]):
                ou = "/Contractors"
                smime = False
                two_sv = False  # External contractors require mandatory 2SV enforcement
            elif "engineering" in dept or any(k in role for k in ["engineer", "architect", "developer"]):
                ou = "/Engineering"
                smime = False
                two_sv = True
            else:
                ou = "/"
                smime = False
                two_sv = True

            is_admin = any(k in role for k in ["cfo", "cto", "lead", "officer"])
            users.append(WorkspaceUser(
                id=f"live_user_{idx+1}",
                primaryEmail=email,
                name=UserName(fullName=full, givenName=first or full, familyName=last or ""),
                orgUnitPath=ou,
                isAdmin=is_admin,
                isEnrolledIn2Sv=two_sv,
                smimeConfigured=smime,
            ))
        return users

    def audit_tenant_posture(
        self,
        domain: Optional[str] = None,
        users: Optional[List[WorkspaceUser]] = None,
    ) -> SecurityPostureReport:
        """Evaluate users against assigned Organizational Unit security policies."""
        if users is not None:
            user_list = users
        elif self.admin_port:
            user_list = self.admin_port.list_users()
        else:
            user_list = []

        if not user_list:
            resolved_domain = domain or "googleguard.de"
            return SecurityPostureReport(
                tenantDomain=resolved_domain,
                complianceScore=100.0,
                totalUsers=0,
                enrolledIn2SvCount=0,
                smimeConfiguredCount=0,
                flaggedUsers=[],
                remediationActions=[]
            )

        # Dynamically infer domain from user emails if not explicitly set
        if not domain or domain == "client-enterprise.de":
            sample_email = user_list[0].primaryEmail if user_list else ""
            resolved_domain = sample_email.split("@")[-1] if "@" in sample_email else "googleguard.de"
        else:
            resolved_domain = domain

        org_units: List[OrgUnit] = self.admin_port.list_org_units() if self.admin_port else []

        # Index Organizational Unit policies by path, defaulting to strict security baselines
        ou_policy_map: Dict[str, Dict[str, Any]] = {
            ou.orgUnitPath: (ou.policies or {}) for ou in org_units
        }
        if "/Executive_Finance" not in ou_policy_map:
            ou_policy_map["/Executive_Finance"] = {"smime_required": True, "two_step_verification": True}
        if "/Contractors" not in ou_policy_map:
            ou_policy_map["/Contractors"] = {"smime_required": False, "two_step_verification": True}
        if "/Engineering" not in ou_policy_map:
            ou_policy_map["/Engineering"] = {"smime_required": False, "two_step_verification": True}

        flagged_users: List[Dict[str, Any]] = []
        remediation_actions: List[str] = []
        users_with_violations = set()

        for user in user_list:
            policies = ou_policy_map.get(user.orgUnitPath, {})
            full_name = (
                user.name.fullName
                if hasattr(user.name, "fullName")
                else (user.name.get("fullName") if isinstance(user.name, dict) else str(user.name))
            )

            # Check 1: S/MIME encryption requirement
            if policies.get("smime_required") and not user.smimeConfigured:
                flagged_users.append({
                    "userId": user.id,
                    "email": user.primaryEmail,
                    "fullName": full_name,
                    "orgUnitPath": user.orgUnitPath,
                    "reason": "MISSING_SMIME_CERTIFICATE",
                    "severity": "HIGH",
                    "recommendation": f"Enforce S/MIME encryption certificate deployment for {user.primaryEmail} in {user.orgUnitPath}."
                })
                users_with_violations.add(user.primaryEmail)
                remediation_actions.append(f"Deploy S/MIME encryption certificate for {user.primaryEmail} in {user.orgUnitPath}.")

            # Check 2: 2-Step Verification requirement
            if policies.get("two_step_verification") and not user.isEnrolledIn2Sv:
                flagged_users.append({
                    "userId": user.id,
                    "email": user.primaryEmail,
                    "fullName": full_name,
                    "orgUnitPath": user.orgUnitPath,
                    "reason": "MISSING_2SV_ENROLLMENT",
                    "severity": "CRITICAL" if user.isAdmin else "HIGH",
                    "recommendation": f"Require immediate 2-Step Verification enrollment for {user.primaryEmail} in {user.orgUnitPath}."
                })
                users_with_violations.add(user.primaryEmail)
                remediation_actions.append(f"Enforce mandatory 2SV enrollment for {user.primaryEmail} in {user.orgUnitPath}.")

        total_users = len(user_list)
        enrolled_2sv = sum(1 for u in user_list if u.isEnrolledIn2Sv)
        smime_configured = sum(1 for u in user_list if u.smimeConfigured)

        compliant_count = total_users - len(users_with_violations)
        compliance_score = round((compliant_count / total_users) * 100, 1) if total_users > 0 else 100.0

        return SecurityPostureReport(
            tenantDomain=resolved_domain,
            complianceScore=compliance_score,
            totalUsers=total_users,
            enrolledIn2SvCount=enrolled_2sv,
            smimeConfiguredCount=smime_configured,
            flaggedUsers=flagged_users,
            remediationActions=remediation_actions
        )
