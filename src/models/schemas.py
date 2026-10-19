from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class DLPRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

RiskLevel = DLPRiskLevel

class ScanResult(BaseModel):
    file_id: str
    file_name: str
    risk_level: DLPRiskLevel
    pii_detected: List[str] = Field(default_factory=list)
    content_hash: str
    redacted_preview: str

class OnboardingTicket(BaseModel):
    candidate_name: str
    email: str
    role: str
    department: str
    manager_email: str

class ProvisioningPlan(BaseModel):
    user_email: str
    target_ou: str
    assigned_groups: List[str] = Field(default_factory=list)
    smime_required: bool = False

class OrgUnit(BaseModel):
    name: str = Field(..., description="Human readable name of the Organizational Unit")
    orgUnitPath: str = Field(..., description="Workspace hierarchy path, e.g. /Executive_Finance")
    description: Optional[str] = None
    policies: Optional[Dict[str, Any]] = Field(default_factory=dict)

class UserName(BaseModel):
    fullName: str
    givenName: Optional[str] = None
    familyName: Optional[str] = None

class WorkspaceUser(BaseModel):
    id: str = Field(..., description="Unique user identifier, e.g. usr_101")
    primaryEmail: str = Field(..., description="User corporate email address")
    name: Union[UserName, Dict[str, str], str] = Field(..., description="Name container with fullName")
    orgUnitPath: str = Field(default="/", description="Current OU path")
    isAdmin: bool = False
    isEnrolledIn2Sv: bool = False
    smimeConfigured: bool = False

class DLPRule(BaseModel):
    ruleId: str
    name: str
    condition: str
    action: str
    severity: str
    isActive: bool = True

class DLPAuditReport(BaseModel):
    file_id: str
    file_name: str
    risk_level: RiskLevel
    pii_types_detected: List[str] = Field(default_factory=list)
    gdpr_articles_impacted: List[str] = Field(default_factory=list)
    sharing_permission_risk: str
    recommended_remediation: str
    content_hash_sha256: str
    redacted_preview: str

class OnboardingRequest(BaseModel):
    fullName: str
    email: str
    department: str
    jobTitle: str
    manager: str
    location: str

class OnboardingResult(BaseModel):
    user: WorkspaceUser
    recommendedOrgUnitPath: str
    assignedGroups: List[str] = Field(default_factory=list)
    smimeRequired: bool = False
    welcomeChecklistDocumentId: Optional[str] = None

class SecurityPostureReport(BaseModel):
    tenantDomain: str
    complianceScore: float = Field(..., ge=0.0, le=100.0)
    totalUsers: int
    enrolledIn2SvCount: int
    smimeConfiguredCount: int
    flaggedUsers: List[Dict[str, Any]] = Field(default_factory=list)
    remediationActions: List[str] = Field(default_factory=list)
