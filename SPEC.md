# GoogleGuard AI: Technical Specification (SPEC.md)

**Project Title:** GoogleGuard AI — Automated Google Workspace DLP, S/MIME & Onboarding Copilot  
**Author / Lead:** Antigravity AI Engineering Assistant  
**Stakeholder Audience:** GoogleGuard Enterprise GmbH Technical Leadership (Cezary Augustynowicz, CTO)  
**Specification Version:** 1.0.0 (Gated Spec Phase)  
**Reference Document:** `plan.md` (`googleguard_ai_master_specification_plan.md`)  

---

## 1. Objective & Business Value

GoogleGuard AI is an enterprise-grade security, DLP compliance, and zero-trust onboarding copilot tailored for Google Workspace tenants managed by GoogleGuard Enterprise GmbH.

### Key Pain Points Solved
1. **Shadow Data & GDPR/DSGVO Non-Compliance:** Unencrypted PII (German IBANs, Tax IDs/Steuer-ID, employment agreements) stored in Google Drive folders with public or over-permissive sharing links, and sensitive email communications without S/MIME encryption.
2. **Over-Privileged Manual Onboarding:** Delay and human error during new hire provisioning in Google Workspace Admin Console, causing new hires to be assigned broad root OU permissions instead of least-privilege Organizational Units and dedicated Google Groups.

### Target Personas & Primary Workflows
* **GoogleGuard Enterprise Security Engineer / Tenant Admin:** Reviews domain security posture score ($0 - 100\%$), identifies users in sensitive OUs missing S/MIME or 2-Step Verification (2SV), and enforces automated remediation via Antigravity MCP tools or FastAPI dashboard.
* **HR & Operations Specialist:** Submits new hire records via Google Sheets or REST API; GoogleGuard evaluates role requirements using Gemini 2.5 Flash Structured Outputs and provisions users into the exact least-privilege OU with mandatory security controls.
* **Compliance Officer (DSGVO/GDPR):** Receives automated, redacted DLP audit reports without exposing raw employee or customer PII in logs or storage.

---

## 2. Tech Stack & Zero-Billing Architecture

| Component | Technology | Version | Purpose / Licensing |
|---|---|---|---|
| **Runtime** | Python | 3.11+ / 3.14 compatible | Core application runtime |
| **API Framework** | FastAPI + Uvicorn | ^0.115.0 / ^0.30.0 | REST API endpoints & dashboard host |
| **Validation & Schemas** | Pydantic v2 + pydantic-settings | ^2.10.0 / ^2.6.0 | Strict schema validation, JSON schema export |
| **AI Engine (Live)** | `google-genai` / Google AI Studio | Gemini 2.5 Flash | Structured JSON classification (Free API key, no billing card) |
| **Workspace APIs (Live)** | `google-api-python-client`, `google-auth-oauthlib` | Latest | Google Drive v3 & Google Sheets v4 (Free Desktop OAuth2) |
| **Workspace Admin (Mock)** | Local JSON Adapter (`src/adapters/mock_admin_adapter.py`) | Internal | Realistic Enterprise Admin SDK Directory & DLP simulation |
| **MCP Server** | Python `mcp` SDK (`FastMCP`) | ^1.2.0 / ^2.2.0 | Custom stdio MCP server for Antigravity integration |
| **Audit Database** | SQLite (`audit_logs.db`) | 3.x (stdlib) | Local audit log store with BigQuery-compatible schema |
| **Testing** | `pytest`, `pytest-mock`, `pytest-cov`, `httpx` | ^8.0.0+ | Strict TDD unit & contract testing |
| **Deployment** | Docker & Cloud Run Manifest | Container OCI | Google Cloud Run deployment configuration |

---

## 3. System Architecture: Hexagonal (Ports & Adapters)

```
                       +-------------------------------------------------------+
                       |              Primary / Driving Adapters               |
                       |  - FastAPI Web Dashboard (`src/main.py`)              |
                       |  - Workspace Admin MCP Server (`workspace_mcp.py`)     |
                       |  - Antigravity Subagents (`agents/*.md`)              |
                       +---------------------------+---------------------------+
                                                   |
                                                   v
                       +-------------------------------------------------------+
                       |             Core Domain Services (Ports)              |
                       |  - `DLPScannerService` (GDPR PII & Drive Scanner)     |
                       |  - `SecurityPostureService` (S/MIME & 2SV Auditor)    |
                       |  - `OnboardingCopilot` (Gemini Least-Privilege OU)    |
                       |  - `PIIPreFilter` (Local Regex Sanitizer & Tokenizer) |
                       +---------------------------+---------------------------+
                                                   |
                        +--------------------------+--------------------------+
                        |                                                     |
                        v                                                     v
+-----------------------------------------------+   +-----------------------------------------------+
|      Live Free Adapters (Driving Cloud)       |   |       Enterprise Mock Adapter (Fixtures)      |
+-----------------------------------------------+   +-----------------------------------------------+
| - `GoogleLiveAdapter`: Drive v3, Sheets v4    |   | - `MockAdminAdapter`: Workspace Enterprise     |
|   (OAuth 2.0 Installed App, Read-Only Scopes) |   |   Directory, OU hierarchy, S/MIME, DLP rules  |
| - `GeminiClient`: Google AI Studio            |   | - `audit_logs.db`: SQLite PII-redacted store  |
|   (`gemini-2.5-flash` Structured Outputs)     |   | - `fixtures/`: Contract-tested JSON fixtures  |
+-----------------------------------------------+   +-----------------------------------------------+
```

---

## 4. Commands

```bash
# Environment Setup
python -m venv .venv
.venv\Scripts\activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run Test Suite (TDD)
pytest tests/ -v
pytest tests/ --cov=src --cov-report=term-missing

# Run FastAPI Development Server
uvicorn src.main:app --reload --port 8000

# Run Custom Workspace MCP Server (stdio)
python src/mcp_server/workspace_mcp.py

# Lint & Static Checks
flake8 src/ tests/
black --check src/ tests/

# Docker Build & Run (Cloud Run Simulation)
docker build -t googleguard-ai .
docker run -p 8080:8080 -e PORT=8080 --env-file .env googleguard-ai
```

---

## 5. Project Directory Structure

```text
buenaai/
├── .agents/
│   └── mcp_config.json              # Antigravity Workspace MCP registration
├── agents/
│   ├── security-auditor.md          # Subagent persona for GDPR & IAM review
│   ├── test-engineer.md             # Subagent persona for contract test suites
│   └── code-reviewer.md             # Subagent persona for Hexagonal architecture
├── fixtures/
│   ├── mock_workspace_users.json    # Simulated Google Workspace Enterprise directory
│   ├── mock_org_units.json          # Simulated Workspace OU hierarchy & security policies
│   ├── mock_dlp_rules.json          # Simulated Cloud Identity DLP rules
│   ├── onboarding_requests.json     # Sample HR candidate records
│   └── sample_docs/
│       ├── contract_with_iban.txt   # Synthetic German IBAN & contract text
│       ├── tax_id_export.csv        # Synthetic German Steuer-ID data
│       └── clean_notes.txt          # Baseline doc without PII
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app & dashboard routes
│   ├── config.py                    # Pydantic Settings & environment flags
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Pydantic v2 models (Users, OUs, DLP, Onboarding)
│   ├── ports/
│   │   ├── __init__.py
│   │   └── workspace_port.py        # Abstract base classes (Hexagonal Ports)
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── gemini_client.py         # Google AI Studio Gemini 2.5 Flash wrapper
│   │   ├── google_live_adapter.py   # Live Drive & Sheets OAuth 2.0 client
│   │   ├── mock_admin_adapter.py    # Enterprise Admin SDK Directory mock
│   │   ├── factory.py               # Environment-aware adapter factory
│   │   └── audit_store.py           # SQLite audit logger (PII tokenized)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pii_pre_filter.py        # Fast regex pre-screener & redactor
│   │   ├── dlp_scanner.py           # Gemini DLP & GDPR compliance classifier
│   │   ├── security_posture.py      # S/MIME, 2SV & OU compliance calculator
│   │   └── onboarding_copilot.py    # Zero-Trust HR onboarding service
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   └── workspace_mcp.py         # FastMCP stdio server exposing 4 tools
│   └── templates/
│       └── index.html               # Tailwind CSS lightweight dashboard
├── tests/
│   ├── __init__.py
│   ├── test_governance.py
│   ├── test_config.py
│   ├── test_schemas.py
│   ├── test_fixtures.py
│   ├── test_mock_admin_adapter.py
│   ├── test_google_live_adapter.py
│   ├── test_gemini_client.py
│   ├── test_adapter_factory.py
│   ├── test_audit_store.py
│   ├── test_pii_pre_filter.py
│   ├── test_dlp_scanner.py
│   ├── test_security_posture.py
│   ├── test_onboarding_copilot.py
│   ├── test_api_endpoints.py
│   ├── test_workspace_mcp.py
│   ├── test_mcp_config.py
│   ├── test_agent_personas.py
│   └── test_dockerfile.py
├── docs/
│   ├── DEMO_SCRIPT.md               # 15-minute presentation & demo walk-through
│   ├── PRESENTATION_NOTES.md        # Talking points for GoogleGuard Enterprise leadership
│   └── screenshots/                 # Antigravity artifacts, skills, and MCP evidence
├── AGENTS.md                        # Antigravity governance rules & security contract
├── SPEC.md                          # This specification document
├── TODO.md                          # Actionable, phased execution task breakdown
├── requirements.txt                 # Pinned Python package dependencies
├── Dockerfile                       # Google Cloud Run production container
├── cloudrun.yaml                    # Google Cloud Run service specification
└── README.md                        # Repository overview & quickstart
```

---

## 6. Code Style & Architectural Patterns

### Strict Hexagonal Separation
* Core domain logic in `src/services/` must depend **only** on abstractions in `src/ports/` and models in `src/models/`. It must never import concrete adapters (`google_live_adapter`, `mock_admin_adapter`, or `audit_store`) directly.
* Concrete adapters are injected via `src/adapters/factory.py`.

### Pydantic v2 Schema Example
```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DLPAuditReport(BaseModel):
    file_id: str = Field(..., description="Unique identifier or path of scanned document")
    file_name: str
    risk_level: RiskLevel
    pii_types_detected: List[str] = Field(default_factory=list)
    gdpr_articles_impacted: List[str] = Field(default_factory=list)
    sharing_permission_risk: str
    recommended_remediation: str
    content_hash_sha256: str
    redacted_preview: str = Field(..., description="Sanitized excerpt with zero raw PII")
```

### GDPR / DSGVO Logging Safety Rule
* **Raw PII must never be emitted to stdout, stderr, or database logs.**
* All text is passed through `PIIPreFilter.sanitize()` before logging.
* Files and records are referenced only by their SHA-256 checksum and masked tokens (`DE89...XXXX`, `Steuer-ID [REDACTED]`).

---

## 7. Testing Strategy & Quality Bar

1. **Test-Driven Development (TDD):**
   - For every service, port, and adapter, a failing unit test in `tests/` must be authored and committed before implementation begins.
2. **Deterministic Offline Tests:**
   - The test suite must run 100% offline and pass without requiring external network access or paid cloud services, relying on `fixtures/` and mocked Gemini calls.
3. **Coverage Expectation:**
   - Minimum 90% branch coverage across `src/services/`, `src/models/`, and `src/adapters/`.
4. **Contract Verification:**
   - Fixture JSON files must be verified for schema conformance against Pydantic models on every test run.

---

## 8. Boundaries & Guardrails

* **Always Do:**
  - Enforce read-only OAuth scopes (`drive.readonly`, `spreadsheets.readonly`) for scanning operations.
  - Run `pytest` before committing changes.
  - Redact PII in memory before generating audit records.
  - Fall back cleanly to `MockAdminAdapter` when live credentials are not present.
* **Ask First:**
  - Introducing any new external cloud dependency or billing-required SDK.
  - Adding write or delete scopes to Google Workspace APIs.
  - Altering the core Hexagonal port definitions.
* **Never Do:**
  - Hardcode API keys, secrets, or real customer credentials in any file.
  - Log raw document text or unmasked employee PII.
  - Skip failing tests or silence lint checks with suppressions (`noqa`, `type: ignore`) without explicit architectural justification.

---

## 9. Success Criteria

- [ ] Complete test suite (`tests/`) passes cleanly with 0 failures: `pytest tests/ -v`.
- [ ] 100% free-tier zero-billing setup confirmed: application boots in both `MOCK` and `LIVE` modes.
- [ ] Gemini 2.5 Flash Structured Outputs successfully classify German PII and map least-privilege OUs.
- [ ] Custom stdio MCP server (`googleguard-workspace`) connects cleanly to Antigravity and executes all 4 administrative tools.
- [ ] Docker container builds cleanly and satisfies Google Cloud Run runtime contract (`PORT=8080`, `/health` 200 OK).
- [ ] Executive presentation and live demo script documented for Sunday demonstration to GoogleGuard Enterprise leadership.
