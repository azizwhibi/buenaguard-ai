from typing import Optional, List, Dict, Any
from src.models.schemas import SecurityPostureReport, WorkspaceUser, OrgUnit
from src.ports.workspace_port import WorkspaceAdminPort

class SecurityPostureService:
    """Audits Google Workspace tenant security posture, S/MIME adoption, and 2SV compliance."""

    def __init__(self, admin_port: Optional[WorkspaceAdminPort] = None):
        self.admin_port = admin_port

    def audit_tenant_posture(self, domain: str = "client-enterprise.de") -> SecurityPostureReport:
        """Evaluate all users against their assigned Organizational Unit security policies."""
        if not self.admin_port:
            return SecurityPostureReport(
                tenantDomain=domain,
                complianceScore=100.0,
                totalUsers=0,
                enrolledIn2SvCount=0,
                smimeConfiguredCount=0,
                flaggedUsers=[],
                remediationActions=[]
            )

        users: List[WorkspaceUser] = self.admin_port.list_users()
        org_units: List[OrgUnit] = self.admin_port.list_org_units()

        # Index Organizational Unit policies by path
        ou_policy_map: Dict[str, Dict[str, Any]] = {
            ou.orgUnitPath: (ou.policies or {}) for ou in org_units
        }

        flagged_users: List[Dict[str, Any]] = []
        remediation_actions: List[str] = []
        users_with_violations = set()

        for user in users:
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

        total_users = len(users)
        enrolled_2sv = sum(1 for u in users if u.isEnrolledIn2Sv)
        smime_configured = sum(1 for u in users if u.smimeConfigured)

        compliant_count = total_users - len(users_with_violations)
        compliance_score = round((compliant_count / total_users) * 100, 1) if total_users > 0 else 100.0

        return SecurityPostureReport(
            tenantDomain=domain,
            complianceScore=compliance_score,
            totalUsers=total_users,
            enrolledIn2SvCount=enrolled_2sv,
            smimeConfiguredCount=smime_configured,
            flaggedUsers=flagged_users,
            remediationActions=remediation_actions
        )
