# BuenaGuard AI: Phased Execution Roadmap & TDD Task Breakdown

**Project Name:** BuenaGuard AI — Automated Google Workspace DLP, S/MIME & Onboarding Copilot  
**Target Organization:** BuenaCloud GmbH (Cezary Augustynowicz & CTO)  
**Methodology:** Antigravity Agent Skills (`spec-driven-development`, `planning-and-task-breakdown`, `test-driven-development`, `incremental-implementation`)  
**Single Source of Truth:** [buenaguard_ai_master_specification_plan.md](file:///D:/buenaai/buenaguard_ai_master_specification_plan.md) / [plan.md](file:///D:/buenaai/plan.md)  
**Technical Specification:** [SPEC.md](file:///D:/buenaai/SPEC.md)  
**Status:** Ready for Human Review (`Ctrl+R` Artifact Review Screen)

---

## Architecture Dependency Graph & Execution Order

```
[Phase 1: Foundation, Governance & Zero-Billing Setup]
  │
  ├── [P1-T1] AGENTS.md Governance & GDPR Safe Logging Rules
  ├── [P1-T2] Repository Scaffolding, Pydantic Config & Env
  ├── [P1-T3] Live Google AI Studio Gemini 2.5 Flash Client
  └── [P1-T4] OAuth2 Desktop Client Wiring (Drive/Sheets Read-Only)
        │
        v
[Phase 2: Enterprise Mock Adapter & Fixtures]
  │
  ├── [P2-T1] Enterprise Domain Pydantic Schemas & Ports
  ├── [P2-T2] German Enterprise Mock Fixtures (Users, OUs, DLP, Sample Docs)
  ├── [P2-T3] Local JSON Enterprise Admin SDK Adapter Implementation
  └── [P2-T4] Adapter Factory & SQLite PII-Redacted Audit Logger
        │
        v
[Phase 3: Core Services via TDD]
  │
  ├── [P3-T1] Local Regex Pre-Scanner & Tokenizer (German IBAN / Steuer-ID)
  ├── [P3-T2] Gemini 2.5 Flash Structured DLP & GDPR Document Scanner
  ├── [P3-T3] S/MIME & Tenant Security Posture Compliance Auditor
  ├── [P3-T4] Gemini Zero-Trust HR Onboarding Copilot (Least-Privilege OU)
  └── [P3-T5] FastAPI Web Dashboard & REST Endpoints
        │
        v
[Phase 4: Custom Google Workspace Admin MCP Server]
  │
  ├── [P4-T1] Standalone Stdio FastMCP Workspace Server (4 Tools)
  └── [P4-T2] Antigravity `.agents/mcp_config.json` with Granular Allowlist
        │
        v
[Phase 5: Subagent Audits, Hardening & Cloud Run Packaging]
  │
  ├── [P5-T1] Persona Definition Prompts (`security-auditor`, `test-engineer`, `code-reviewer`)
  ├── [P5-T2] Subagent Security Audit & Hexagonal Architecture Review
  ├── [P5-T3] Dockerfile & Google Cloud Run Production Configuration
  └── [P5-T4] Sunday Presentation Deck & Live Demo Script (15-Min Arc)
```

---

## Phase 1: Foundation, Governance & Zero-Billing Setup

### Task [P1-T1]: Antigravity Governance & Security Rules (`AGENTS.md`)
**Description:** Establish project-wide engineering laws in `AGENTS.md` governing GDPR/DSGVO zero raw PII logging, least-privilege OAuth scopes, spec-first adherence, and mandatory TDD for all services.
- **Dependencies:** None
- **Files to Create/Modify:**
  - `AGENTS.md`
  - `tests/test_governance.py`
- **Acceptance Criteria:**
  - [x] `AGENTS.md` mandates zero raw PII emission to `stdout`, `stderr`, or persistent logs.
  - [x] `AGENTS.md` specifies that only read-only OAuth scopes (`drive.readonly`, `spreadsheets.readonly`) may be requested.
  - [x] `AGENTS.md` defines the Hexagonal Ports-and-Adapters architectural boundary.
  - [x] `AGENTS.md` requires passing unit tests before any service is marked complete.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_governance.py::test_agents_md_rules_presence` asserting that `AGENTS.md` exists and contains mandatory keywords: `GDPR`, `PII`, `drive.readonly`, `Hexagonal`, `TDD`.
  - **Command to Verify:** `pytest tests/test_governance.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread (Antigravity Governance)
- **Estimated Scope:** XS (1-2 files)

---

### Task [P1-T2]: Repository Scaffolding, Package Dependencies & Environment Configuration
**Description:** Initialize application directory structure, pin minimal zero-billing dependencies in `requirements.txt`, create `.env.example`, and write type-safe `src/config.py` using `pydantic-settings`.
- **Dependencies:** `[P1-T1]`
- **Files to Create/Modify:**
  - `requirements.txt`
  - `.env.example`
  - `.gitignore`
  - `src/__init__.py`
  - `src/config.py`
  - `tests/__init__.py`
  - `tests/test_config.py`
- **Acceptance Criteria:**
  - [x] `requirements.txt` specifies FastAPI, Pydantic v2, pydantic-settings, google-genai, google-api-python-client, google-auth-oauthlib, mcp, and pytest.
  - [x] `src/config.py` defaults `WORKSPACE_MODE` to `"MOCK"` to guarantee zero-billing safety.
  - [x] `.gitignore` explicitly excludes `.env`, `credentials.json`, `token.json`, `geminiapikey.txt`, `audit_logs.db`, and `__pycache__`.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_config.py::test_config_defaults_and_env_loading` asserting `Settings()` loads default mock mode, parses `GEMINI_API_KEY`, and validates enum constraints.
  - **Command to Verify:** `pytest tests/test_config.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread
- **Estimated Scope:** S (2-3 files)

---

### Task [P1-T3]: Live Google AI Studio Gemini API Client Wrapper
**Description:** Implement `src/adapters/gemini_client.py` wrapping the official Google GenAI SDK (`google-genai`), reading the free API key from `geminiapikey.txt` or `.env`, configuring `gemini-2.5-flash`, and supporting structured Pydantic output schemas.
- **Dependencies:** `[P1-T2]`
- **Files to Create/Modify:**
  - `src/adapters/gemini_client.py`
  - `tests/test_gemini_client.py`
- **Acceptance Criteria:**
  - [x] Client initializes with `gemini-2.5-flash` model.
  - [x] Supports typed structured generation using Pydantic response schemas.
  - [x] Includes deterministic fallback/mocking mechanism when offline or if API key is unconfigured.
  - [x] Never logs raw prompt or raw response containing unmasked PII.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_gemini_client.py::test_gemini_client_initialization_and_mock_fallback` validating client instantiates, handles missing key gracefully, and serializes structured schema requests.
  - **Command to Verify:** `pytest tests/test_gemini_client.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread / Delegated to `test-engineer` subagent for mock fixture verification
- **Estimated Scope:** S (2 files)

---

### Task [P1-T4]: OAuth2 Desktop Client Wiring for Free Google Drive & Sheets APIs
**Description:** Implement `src/adapters/google_live_adapter.py` providing desktop OAuth2 authentication (`credentials.json`), enforcing strictly read-only scopes, and safely handling token caching in `token.json` with graceful offline fallback.
- **Dependencies:** `[P1-T2]`
- **Files to Create/Modify:**
  - `src/adapters/google_live_adapter.py`
  - `tests/test_google_live_adapter.py`
- **Acceptance Criteria:**
  - [x] Loads `credentials.json` (OAuth client ID `216921811799-...`).
  - [x] Enforces scopes `https://www.googleapis.com/auth/drive.readonly` and `https://www.googleapis.com/auth/spreadsheets.readonly`.
  - [x] Safely caches refresh tokens to `token.json` (gitignored).
  - [x] Falls back to offline fixture data without raising unhandled network exceptions when credentials are absent.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_google_live_adapter.py::test_oauth_flow_and_token_handling` validating scope restriction, token loader, and offline mode.
  - **Command to Verify:** `pytest tests/test_google_live_adapter.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread
- **Estimated Scope:** S (2 files)

---

### Checkpoint: Phase 1 Foundation Checkpoint
- [x] All Phase 1 tests pass: `pytest tests/test_governance.py tests/test_config.py tests/test_gemini_client.py tests/test_google_live_adapter.py -v`
- [x] Git status confirms zero credential leakage in untracked files
- [x] Architecture review with human before starting Phase 2


---

## Phase 2: Enterprise Mock Adapter & Fixtures

### Task [P2-T1]: Enterprise Domain Pydantic Schemas & Port Definitions
**Description:** Define core domain entities in `src/models/schemas.py` and abstract interfaces in `src/ports/workspace_port.py` enforcing strict Hexagonal separation.
- **Dependencies:** `[P1-T2]`
- **Files to Create/Modify:**
  - `src/models/schemas.py`
  - `src/ports/workspace_port.py`
  - `tests/test_schemas.py`
- **Acceptance Criteria:**
  - [x] Models defined: `WorkspaceUser`, `OrgUnit`, `DLPRule`, `DLPAuditReport`, `OnboardingRequest`, `OnboardingResult`, `SecurityPostureReport`.
  - [x] Abstract class `WorkspaceAdminPort` defines methods: `list_users()`, `get_user(email)`, `list_org_units()`, `list_dlp_rules()`, `provision_user(user)`, `get_smime_status(email)`.
  - [x] Abstract class `WorkspaceDrivePort` defines methods: `list_drive_files()`, `get_file_content(file_id)`, `get_sharing_permissions(file_id)`.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_schemas.py::test_workspace_schemas_validation` verifying validation constraints, required fields, and enum values (`RiskLevel`).
  - **Command to Verify:** `pytest tests/test_schemas.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread (Domain Contract Definition)
- **Estimated Scope:** M (3 files)

---

### Task [P2-T2]: German Enterprise Mock Fixtures Generation
**Description:** Generate realistic, DSGVO-compliant synthetic fixtures simulating a German Google Workspace Enterprise tenant (`mock_org_units.json`, `mock_workspace_users.json`, `mock_dlp_rules.json`, `onboarding_requests.json`, and sample docs).
- **Dependencies:** `[P2-T1]`
- **Files to Create/Modify:**
  - `fixtures/mock_org_units.json`
  - `fixtures/mock_workspace_users.json`
  - `fixtures/mock_dlp_rules.json`
  - `fixtures/onboarding_requests.json`
  - `fixtures/sample_docs/contract_with_iban.txt`
  - `fixtures/sample_docs/tax_id_export.csv`
  - `fixtures/sample_docs/clean_notes.txt`
  - `tests/test_fixtures.py`
- **Acceptance Criteria:**
  - [x] `mock_org_units.json` includes `/`, `/Executive_Finance`, `/Engineering`, `/Contractors` with policy attributes (`smime_required`, `two_step_verification`).
  - [x] `mock_workspace_users.json` contains CFO Hannah Weber (`smimeConfigured: false`), Lukas Schmidt Dev Lead, and Marco Rossi contractor.
  - [x] Sample document files contain synthetic German IBANs (`DE89...`) and tax IDs for DLP testing.
  - [x] Every fixture JSON file parses validly against `src/models/schemas.py`.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_fixtures.py::test_fixture_schema_conformance` validating JSON schema parsing and synthetic entity attributes.
  - **Command to Verify:** `pytest tests/test_fixtures.py -v`
- **Antigravity Feature / Subagent Assignment:** Parallel Subagent (`submit_agent` -> `fixtures-engineer`)
- **Estimated Scope:** M (4-5 files)

---

### Task [P2-T3]: Enterprise Mock Workspace Admin Adapter Implementation
**Description:** Implement `src/adapters/mock_admin_adapter.py` fulfilling `WorkspaceAdminPort` backed by `fixtures/` JSON data, supporting queries and stateful in-memory user provisioning.
- **Dependencies:** `[P2-T1]`, `[P2-T2]`
- **Files to Create/Modify:**
  - `src/adapters/mock_admin_adapter.py`
  - `tests/test_mock_admin_adapter.py`
- **Acceptance Criteria:**
  - [x] Implements all `WorkspaceAdminPort` methods reading from JSON fixtures.
  - [x] `provision_user()` adds new user records to an in-memory state store and returns the created user entity.
  - [x] `get_smime_status()` accurately returns S/MIME certificate state for any tenant email.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_mock_admin_adapter.py::test_mock_admin_adapter_crud_operations` asserting query responses and successful user provisioning state retention.
  - **Command to Verify:** `pytest tests/test_mock_admin_adapter.py -v`
- **Antigravity Feature / Subagent Assignment:** Parallel Subagent (`submit_agent`)
- **Estimated Scope:** S (2 files)

---

### Task [P2-T4]: Environment-Aware Workspace Adapter Factory & SQLite Audit Store
**Description:** Implement `src/adapters/factory.py` to toggle between live Google APIs and mock adapters based on `config.WORKSPACE_MODE`, and `src/adapters/audit_store.py` for PII-redacted local SQLite audit logging.
- **Dependencies:** `[P2-T3]`, `[P1-T4]`
- **Files to Create/Modify:**
  - `src/adapters/factory.py`
  - `src/adapters/audit_store.py`
  - `tests/test_adapter_factory.py`
  - `tests/test_audit_store.py`
- **Acceptance Criteria:**
  - [x] Factory instantiates `MockAdminAdapter` when `WORKSPACE_MODE=MOCK`.
  - [x] Factory instantiates `GoogleLiveAdapter` when `WORKSPACE_MODE=LIVE`.
  - [x] SQLite audit store records timestamp, scan type, file SHA-256 hash, and risk level, with zero raw PII stored in columns.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_adapter_factory.py::test_factory_switching` and `tests/test_audit_store.py::test_audit_logger_redacts_pii`.
  - **Command to Verify:** `pytest tests/test_adapter_factory.py tests/test_audit_store.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread / Audited by `security-auditor` subagent
- **Estimated Scope:** M (4 files)

---

### Checkpoint: Phase 2 Enterprise Mock Checkpoint
- [x] All Phase 2 tests pass: `pytest tests/test_schemas.py tests/test_fixtures.py tests/test_mock_admin_adapter.py tests/test_adapter_factory.py tests/test_audit_store.py -v`
- [x] Hexagonal architecture verified: no direct adapter imports in domain models or ports
- [x] Review with human before proceeding to Phase 3

---

## Phase 3: Core Services via TDD

### Task [P3-T1]: Local Regex Pre-Scanner & PII Masking Engine
**Description:** Implement `src/services/pii_pre_filter.py` providing lightning-fast regex pre-filtering for EU/German PII (IBAN, Steuer-ID, Passport, Credit Cards, email) and safe tokenization (`[REDACTED_IBAN_1]`).
- **Dependencies:** `[P2-T1]`
- **Files to Create/Modify:**
  - `src/services/pii_pre_filter.py`
  - `tests/test_pii_pre_filter.py`
- **Acceptance Criteria:**
  - [ ] Detects German IBANs (`DE\d{20}`) with checksum validation pattern.
  - [ ] Detects German tax identification numbers (Steuer-ID 11 digits).
  - [ ] Tokenizes sensitive strings before any external API transmission or logging.
  - [ ] Emits zero raw PII to logs.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_pii_pre_filter.py::test_regex_detection_and_redaction` asserting correct detection, token replacement, and clean output strings.
  - **Command to Verify:** `pytest tests/test_pii_pre_filter.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread / Persona `security-auditor`
- **Estimated Scope:** S (2 files)

---

### Task [P3-T2]: Gemini 2.5 Flash Structured DLP & GDPR Document Scanner
**Description:** Implement `src/services/dlp_scanner.py` orchestrating Drive document retrieval, pre-filtering, Gemini 2.5 Flash classification via structured JSON outputs, sharing permission risk evaluation, and `DLPAuditReport` generation.
- **Dependencies:** `[P3-T1]`, `[P1-T3]`, `[P2-T2]`
- **Files to Create/Modify:**
  - `src/services/dlp_scanner.py`
  - `tests/test_dlp_scanner.py`
- **Acceptance Criteria:**
  - [ ] Evaluates file permissions (flags `anyoneWithLink` and external shares).
  - [ ] Leverages Gemini 2.5 Flash Structured Outputs to classify `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and cite GDPR articles (`Art. 6`, `Art. 9`, `Art. 83`).
  - [ ] Generates concrete remediation recommendation (e.g. revoke link, move to `/Confidential_OU`).
  - [ ] Persists scan result to SQLite audit store with file SHA-256 hash.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_dlp_scanner.py::test_dlp_scanner_identifies_gdpr_risk_levels` executing on `fixtures/sample_docs/contract_with_iban.txt` and asserting `CRITICAL` risk and remediation advice.
  - **Command to Verify:** `pytest tests/test_dlp_scanner.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread (Core Service)
- **Estimated Scope:** M (2-3 files)

---

### Task [P3-T3]: S/MIME & Tenant Security Posture Compliance Auditor
**Description:** Implement `src/services/security_posture.py` calculating a Google Workspace domain security posture score ($0 - 100\%$) based on S/MIME adoption in sensitive OUs, 2SV enforcement, and DLP coverage.
- **Dependencies:** `[P2-T3]`, `[P2-T1]`
- **Files to Create/Modify:**
  - `src/services/security_posture.py`
  - `tests/test_security_posture.py`
- **Acceptance Criteria:**
  - [ ] Flags high-risk users (e.g. CFO Hannah Weber in `/Executive_Finance` with `smimeConfigured: false`).
  - [ ] Flags users lacking 2-Step Verification in enforced OUs.
  - [ ] Computes weighted compliance score ($0 - 100\%$) and outputs prioritized remediation actions.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_security_posture.py::test_security_posture_score_calculation` querying `mock_workspace_users.json` and asserting score computation and identified gaps.
  - **Command to Verify:** `pytest tests/test_security_posture.py -v`
- **Antigravity Feature / Subagent Assignment:** Parallel Subagent (`submit_agent`)
- **Estimated Scope:** S (2 files)

---

### Task [P3-T4]: Gemini Zero-Trust HR Onboarding Copilot
**Description:** Implement `src/services/onboarding_copilot.py` reading candidate onboarding rows, evaluating role & department against BuenaCloud's OU tree using Gemini 2.5 Flash, assigning least-privilege OU/groups, provisioning the user, and generating an onboarding checklist.
- **Dependencies:** `[P2-T3]`, `[P1-T3]`, `[P2-T2]`
- **Files to Create/Modify:**
  - `src/services/onboarding_copilot.py`
  - `tests/test_onboarding_copilot.py`
- **Acceptance Criteria:**
  - [ ] Evaluates input candidates (e.g., "Senior Payroll Specialist" -> `/Executive_Finance`, `smime_required: true`).
  - [ ] Recommends mandatory Google Groups (`finance-team@client-enterprise.de`).
  - [ ] Calls `provision_user()` on the port to create the account.
  - [ ] Generates personalized Welcome Security Checklist document.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_onboarding_copilot.py::test_onboarding_copilot_least_privilege_ou_assignment` asserting correct OU path, group membership, and provisioning call.
  - **Command to Verify:** `pytest tests/test_onboarding_copilot.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread (Core Service)
- **Estimated Scope:** M (2-3 files)

---

### Task [P3-T5]: FastAPI Web Dashboard & REST Endpoints
**Description:** Build `src/main.py` providing REST endpoints (`/health`, `/api/v1/posture`, `/api/v1/scan-dlp`, `/api/v1/onboard`) and a lightweight Tailwind CSS executive dashboard for live demonstrations.
- **Dependencies:** `[P3-T2]`, `[P3-T3]`, `[P3-T4]`
- **Files to Create/Modify:**
  - `src/main.py`
  - `src/templates/index.html`
  - `tests/test_api_endpoints.py`
- **Acceptance Criteria:**
  - [ ] `GET /health` returns status `200 OK` and active mode (`MOCK` or `LIVE`).
  - [ ] `GET /api/v1/posture` returns tenant compliance score and flagged accounts.
  - [ ] `POST /api/v1/scan-dlp` accepts a file id and returns structured `DLPAuditReport`.
  - [ ] `POST /api/v1/onboard` accepts an onboarding request and provisions the user.
  - [ ] `GET /` serves responsive dashboard with compliance metric cards and scan trigger buttons.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_api_endpoints.py::test_api_routes` using FastAPI `TestClient` to verify 200 responses and JSON schema output.
  - **Command to Verify:** `pytest tests/test_api_endpoints.py -v`
- **Antigravity Feature / Subagent Assignment:** Parallel Subagent (`submit_agent` -> `ui-backend-engineer`)
- **Estimated Scope:** M (3 files)

---

### Checkpoint: Phase 3 Core Services Checkpoint
- [ ] All Phase 3 service tests pass: `pytest tests/test_pii_pre_filter.py tests/test_dlp_scanner.py tests/test_security_posture.py tests/test_onboarding_copilot.py tests/test_api_endpoints.py -v`
- [ ] Verify zero-billing execution: full test suite passes with zero external network dependencies
- [ ] Review with human before starting Phase 4

---

## Phase 4: Custom Google Workspace Admin MCP Server

### Task [P4-T1]: Standalone Stdio Workspace MCP Server Implementation
**Description:** Implement `src/mcp_server/workspace_mcp.py` using Python `mcp` SDK (`FastMCP`), exposing 4 administrative tools directly to Antigravity: `check_domain_dlp_status`, `list_workspace_ous`, `scan_drive_file_dlp`, and `simulate_user_onboarding`.
- **Dependencies:** `[P3-T2]`, `[P3-T3]`, `[P3-T4]`
- **Files to Create/Modify:**
  - `src/mcp_server/workspace_mcp.py`
  - `tests/test_workspace_mcp.py`
- **Acceptance Criteria:**
  - [ ] Tool 1: `check_domain_dlp_status()` returns tenant S/MIME, 2SV, and DLP compliance summary.
  - [ ] Tool 2: `list_workspace_ous()` lists all OUs and their security policies.
  - [ ] Tool 3: `scan_drive_file_dlp(file_id: str)` runs DLP scan and returns redacted audit report.
  - [ ] Tool 4: `simulate_user_onboarding(name: str, role: str, department: str)` runs least-privilege OU analysis.
  - [ ] Server operates cleanly over standard I/O (stdio).
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_workspace_mcp.py::test_mcp_tools_registration_and_execution` asserting tool schemas and handler execution results.
  - **Command to Verify:** `pytest tests/test_workspace_mcp.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread (MCP Integration)
- **Estimated Scope:** M (2 files)

---

### Task [P4-T2]: Antigravity Workspace MCP Configuration & Granular Tool Permissions
**Description:** Create `.agents/mcp_config.json` registering `buenaguard-workspace` with Antigravity, specifying command, arguments, environment variables, and strict granular `mcp(server/tool)` permissions.
- **Dependencies:** `[P4-T1]`
- **Files to Create/Modify:**
  - `.agents/mcp_config.json`
  - `tests/test_mcp_config.py`
- **Acceptance Criteria:**
  - [ ] Config defines `buenaguard-workspace` running `python src/mcp_server/workspace_mcp.py` with `PYTHONPATH=.`.
  - [ ] Config includes granular permission allowlist:
    - `mcp(buenaguard-workspace/check_domain_dlp_status)`
    - `mcp(buenaguard-workspace/list_workspace_ous)`
    - `mcp(buenaguard-workspace/scan_drive_file_dlp)`
    - `mcp(buenaguard-workspace/simulate_user_onboarding)`
  - [ ] Config adheres strictly to Antigravity MCP JSON schema.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_mcp_config.py::test_mcp_config_schema_and_permissions` validating JSON format, required keys, and valid command path.
  - **Command to Verify:** `pytest tests/test_mcp_config.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread (Antigravity Config)
- **Estimated Scope:** S (2 files)

---

### Checkpoint: Phase 4 MCP Server Checkpoint
- [ ] All Phase 4 tests pass: `pytest tests/test_workspace_mcp.py tests/test_mcp_config.py -v`
- [ ] MCP stdio handshake validated: server starts and lists tools without error
- [ ] Review with human before Phase 5

---

## Phase 5: Subagent Audits, Hardening & Cloud Run Packaging

### Task [P5-T1]: Persona Definition Prompts for Subagents
**Description:** Create specialized Antigravity subagent persona prompt files in `agents/` (`security-auditor.md`, `test-engineer.md`, `code-reviewer.md`) tailored to German GDPR/DSGVO, OAuth security, and Hexagonal architecture.
- **Dependencies:** `[P1-T1]`
- **Files to Create/Modify:**
  - `agents/security-auditor.md`
  - `agents/test-engineer.md`
  - `agents/code-reviewer.md`
  - `tests/test_agent_personas.py`
- **Acceptance Criteria:**
  - [ ] `security-auditor.md` defines rules for detecting hardcoded keys, raw PII logging, and excessive OAuth permissions.
  - [ ] `test-engineer.md` defines pytest coverage standards, mock isolation, and edge-case testing.
  - [ ] `code-reviewer.md` defines Hexagonal port/adapter decoupling and clean code standards.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_agent_personas.py::test_subagent_markdown_structure` confirming files exist and contain required role directives.
  - **Command to Verify:** `pytest tests/test_agent_personas.py -v`
- **Antigravity Feature / Subagent Assignment:** Main Thread
- **Estimated Scope:** S (3-4 files)

---

### Task [P5-T2]: Subagent Audits (Security Auditor & Code Reviewer)
**Description:** Invoke Antigravity's built-in `security-auditor` and `code-reviewer` subagents to perform end-to-end audit of all source files, verify zero PII leaks, check branch coverage >= 90%, and document findings in `docs/AUDIT_REPORT.md`.
- **Dependencies:** `[P5-T1]`, `[P4-T2]`, `[P3-T5]`
- **Files to Create/Modify:**
  - `docs/AUDIT_REPORT.md`
  - `src/` (remediation of any auditor findings)
- **Acceptance Criteria:**
  - [ ] Zero hardcoded credentials or API keys across the entire repository.
  - [ ] Zero unmasked PII logged in stdout or SQLite.
  - [ ] Test coverage exceeds 90% across `src/`: `pytest --cov=src tests/`.
  - [ ] All findings resolved and logged in `docs/AUDIT_REPORT.md`.
- **TDD Verification Criteria:**
  - **Verification Command:** `pytest --cov=src --cov-report=term-missing tests/`
- **Antigravity Feature / Subagent Assignment:** Built-in Subagents (`security-auditor`, `code-reviewer`, `test-engineer`)
- **Estimated Scope:** M (2-3 files)

---

### Task [P5-T3]: Containerization & Google Cloud Run Production Configuration
**Description:** Create production `Dockerfile`, `.dockerignore`, and `cloudrun.yaml` for Google Cloud Run deployment, adhering to Google Cloud best practices (non-root user, dynamic `$PORT`, healthcheck).
- **Dependencies:** `[P3-T5]`, `[P5-T2]`
- **Files to Create/Modify:**
  - `Dockerfile`
  - `.dockerignore`
  - `cloudrun.yaml`
  - `tests/test_dockerfile.py`
- **Acceptance Criteria:**
  - [ ] `Dockerfile` uses lean Python base image and runs as non-root user (`USER nonroot`).
  - [ ] Binds dynamically to `0.0.0.0:${PORT:-8080}`.
  - [ ] `.dockerignore` excludes `credentials.json`, `token.json`, `geminiapikey.txt`, `.git`, `.venv`.
  - [ ] `cloudrun.yaml` defines memory, CPU, and `/health` probe settings.
- **TDD Verification Criteria:**
  - **Failing Test First:** `tests/test_dockerfile.py::test_dockerfile_best_practices` validating Dockerfile syntax, non-root user, and `.dockerignore` exclusions.
  - **Command to Verify:** `pytest tests/test_dockerfile.py -v`
- **Antigravity Feature / Subagent Assignment:** Parallel Subagent (`submit_agent`)
- **Estimated Scope:** S (3-4 files)

---

### Task [P5-T4]: Sunday Presentation Deck & Live Demo Script
**Description:** Author `docs/DEMO_SCRIPT.md` and `docs/PRESENTATION_NOTES.md` structuring the 15-minute presentation arc for Cezary Augustynowicz and BuenaCloud leadership, including Antigravity skill evidence, subagent logs, and live demo commands.
- **Dependencies:** `[P5-T3]`
- **Files to Create/Modify:**
  - `docs/DEMO_SCRIPT.md`
  - `docs/PRESENTATION_NOTES.md`
- **Acceptance Criteria:**
  - [ ] Covers all 8 presentation slides outlined in Section 7 of the Master Blueprint.
  - [ ] Details the 3 live demo moments: Web UI DLP scan, Smart Onboarding Copilot, and Antigravity MCP CLI execution.
  - [ ] Highlights business ROI: 40-60% time savings for BuenaCloud tenant migration and compliance audits.
- **TDD Verification Criteria:**
  - **Manual Check:** Review presentation script against 15-minute target duration and live demo commands.
- **Antigravity Feature / Subagent Assignment:** Main Thread
- **Estimated Scope:** S (2 files)

---

### Final Checkpoint: Complete System Validation
- [ ] Full test suite execution: `pytest tests/ -v --cov=src` with 100% pass rate and >= 90% coverage
- [ ] Zero-billing execution verified: all services run cleanly offline with synthetic fixtures
- [ ] MCP server verified: `.agents/mcp_config.json` loads cleanly in Antigravity
- [ ] Cloud Run container build tested or verified
- [ ] Artifact Review completed with human engineer (`Ctrl+R`)

---

## Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **Google AI Studio Quota Exhaustion** | Medium | Gemini client includes deterministic local mock fallback returning pre-computed structured JSON for tests and offline demonstrations. |
| **Accidental PII Leakage in Logs** | High | Multi-layered defense: `PIIPreFilter` regex sanitizes before any call, `AGENTS.md` forbids raw logging, SQLite stores only SHA-256 hashes, and `security-auditor` subagent verifies. |
| **Missing Google Workspace Enterprise Domain** | High | `MockAdminAdapter` completely simulates Admin SDK Directory and DLP rules behind `WorkspaceAdminPort` with 100% contract parity. |
| **OAuth Consent Screen Delays** | Low | Desktop OAuth client (`credentials.json`) already configured for local installed app flow; read-only scopes bypass complex verification for developer testing. |

---

## Open Questions & Human Input
1. **Gemini Model Designation:** The blueprint targets `gemini-2.5-flash` via Google AI Studio. Should we also add `gemini-1.5-flash` or `gemini-2.0-flash` as an automatic fallback if 2.5 is unavailable in certain regions?
2. **Dashboard UI Preference:** The plan provides a lightweight FastAPI + Tailwind CSS CDN dashboard for the live demo. Would you like any specific BuenaCloud branding or logo assets included?
