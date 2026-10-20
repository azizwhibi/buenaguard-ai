# GoogleGuard AI: Master System Specification & Execution Plan

**Project Title:** GoogleGuard AI — Automated Google Workspace DLP, S/MIME & Onboarding Copilot  
**Target Audience:** GoogleGuard Enterprise GmbH Technical Leadership (Cezary Augustynowicz & CTO)  
**Primary Objective:** Demonstrate mastery of **Google Antigravity** (Addy Osmani `agent-skills`, Subagents, Custom MCPs, Artifact Review) applied directly to GoogleGuard Enterprise’s core business (**Google Workspace Enterprise Security, GDPR/DSGVO Compliance, and Gemini AI Automation**).  
**Cost / Billing Profile:** 100% Free Tier / No Cloud Billing Card Required (Hybrid Live OAuth2 + Enterprise Mock Adapter Architecture).

---

## 1. Executive Summary & Business Value for GoogleGuard Enterprise

GoogleGuard Enterprise GmbH specializes in migrating businesses to Google Workspace, securing tenants (DLP, S/MIME, Context-Aware Access), and integrating Google AI. 

**GoogleGuard AI** solves two recurring pain points for GoogleGuard Enterprise’s German and EU enterprise clients:
1. **Shadow Data & GDPR/DSGVO Compliance:** Employees store unencrypted PII (IBANs, tax IDs, contracts) in Google Drive and send sensitive emails without S/MIME encryption. GoogleGuard scans Drive files and email routing rules, using **Gemini 2.5 Flash** to classify sensitive PII and flag compliance violations.
2. **Zero-Trust Onboarding Bottlenecks:** Provisioning new hires manually in Google Workspace Admin Console leads to over-privileged accounts. GoogleGuard reads incoming HR onboarding rows from **Google Sheets**, uses Gemini to map the employee to the strictest least-privilege **Organizational Unit (OU)** and **Google Groups**, provisions the account via the **Workspace Admin SDK Adapter**, and generates a tailored Welcome Onboarding Document in **Google Drive**.

---

## 2. System Architecture & "Zero-Billing" Hybrid Strategy

To build and test this system with zero cloud billing dependencies while maintaining production-grade enterprise architecture, the application uses the **Hexagonal / Ports-and-Adapters Pattern**:

```
+-----------------------------------------------------------------------+
|                     Developer / Admin Interfaces                      |
|  1. FastAPI Web Dashboard (UI)     2. Custom Workspace MCP Server     |
+-----------------+-----------------------------------+-----------------+
                  |                                   |
                  v                                   v
+-----------------------------------------------------------------------+
|                     GoogleGuard Core Domain Engine                     |
|  - DLP & PII Scanner Service       - Smart Onboarding Orchestrator    |
|  - S/MIME & OU Compliance Engine   - GDPR PII Redaction Middleware    |
+--------+-------------------------+---------------------------+--------+
         |                         |                           |
         v                         v                           v
+----------------+       +-------------------+       +------------------+
|  LIVE API      |       |  LIVE AI ENGINE   |       |  ENTERPRISE      |
|  ADAPTERS      |       |  (AI Studio)      |       |  MOCK ADAPTERS   |
| (Free OAuth2)  |       | (Free API Key)    |       | (Local JSON/SQL) |
+----------------+       +-------------------+       +------------------+
| - Google Drive |       | - Gemini 2.5 Flash|       | - Admin SDK Dir. |
| - Google Sheets|       | - Structured JSON |       | - Workspace DLP  |
| - Gmail API    |       |   Outputs         |       | - S/MIME Certs   |
+----------------+       +-------------------+       +------------------+
```

### Component Breakdown:
* **Language & Framework:** Python 3.11+ with **FastAPI** and **Pydantic v2** (strict type validation).
* **AI Engine (Live - Free):** `google-genai` SDK using a free **Google AI Studio API Key** (`gemini-2.5-flash`).
* **Workspace Productivity APIs (Live - Free):** Google Drive API v3, Google Sheets API v4, and Gmail API v1 authenticated via a free Desktop OAuth 2.0 Client (`credentials.json`) against a personal Google account.
* **Workspace Enterprise Admin APIs (Mocked via Contract Adapters):** Because Admin SDK Directory (`users.insert`, `orgunits.list`) and Cloud Identity DLP Rules require a paid Workspace Enterprise domain, they are implemented behind an abstract `WorkspaceAdminPort` interface with a `LocalJsonAdminAdapter` backed by realistic enterprise JSON fixtures (`fixtures/`).
* **Audit Database:** Local **SQLite** database (`audit_logs.db`) with BigQuery-compatible schema design so it can be swapped to GCP BigQuery in production.

---

## 3. Core Functional Specifications (Features to Build)

### Feature 1: Intelligent Google Drive DLP & GDPR Scanner (`src/services/dlp_scanner.py`)
* **Input:** Connects to a designated Google Drive folder (live via Drive API or fallback `fixtures/drive_samples/`) containing sample corporate documents (contracts, HR sheets, notes).
* **Processing:**
  1. Extracts text content from Docs/TXT/PDF files.
  2. Passes content through a local regex pre-screen + **Gemini 2.5 Flash** structured prompt to detect EU/German PII (IBAN, Passport, Health Data, Salary, Customer Secrets) without logging raw PII to stdout.
  3. Checks file sharing permissions (`anyoneWithLink`, external domain shares).
* **Output:** Returns a structured `DLPAuditReport` (Pydantic model) with `risk_level` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `gdpr_articles_impacted`, and `recommended_remediation` (e.g., *"Revoke public link and move to /Confidential OU folder"*).

### Feature 2: S/MIME & Tenant Security Posture Auditor (`src/services/security_posture.py`)
* **Input:** Queries the `WorkspaceAdminPort` for tenant users, Organizational Units (OUs), and S/MIME certificate statuses (`fixtures/mock_workspace_users.json`).
* **Processing:**
  1. Identifies users in sensitive OUs (`/Executive`, `/Finance`, `/Legal`) who have `smime_enabled: false` or `2sv_enforced: false`.
  2. Evaluates tenant-wide DLP rules (`fixtures/mock_dlp_rules.json`) for gaps.
* **Output:** Generates a Tenant Compliance Score ($0 - 100\%$) and actionable remediation commands.

### Feature 3: Gemini Zero-Trust Onboarding Copilot (`src/services/onboarding_copilot.py`)
* **Input:** Reads pending rows from a live **Google Sheet** (or `fixtures/onboarding_requests.json`) with columns: `Full Name`, `Email`, `Department`, `Job Title`, `Manager`, `Location`.
* **Processing:**
  1. Uses **Gemini 2.5 Flash** with Structured Outputs to analyze the `Job Title` and `Department` against GoogleGuard Enterprise’s Organizational Unit tree (`fixtures/mock_org_units.json`).
  2. Recommends the exact least-privilege `orgUnitPath` (e.g., `/Engineering/Backend`), required Google Groups (`dev-team@`, `gcp-viewers@`), and whether S/MIME is mandatory.
  3. Calls `WorkspaceAdminPort.provision_user()` to write the new user record into the state store and generates a personalized Onboarding Security Checklist in Google Drive.

### Feature 4: Custom Google Workspace MCP Server (`src/mcp_server/workspace_mcp.py`)
* Built using the Python `mcp` SDK (`FastMCP`), exposing 3 tools directly to **Google Antigravity**:
  1. `get_tenant_compliance_summary()`: Returns current S/MIME, 2SV, and DLP posture metrics.
  2. `scan_drive_file_dlp(file_id: str)`: Triggers a live Gemini DLP scan on a specific file and returns the redacted risk report.
  3. `simulate_user_onboarding(name: str, role: str, department: str)`: Runs the Gemini least-privilege OU mapper directly inside the Antigravity terminal.

---

## 4. Target Repository Structure

```text
googleguard-ai/
├── .agents/
│   └── mcp_config.json              # Workspace-scoped MCP configuration for Antigravity
├── agents/
│   ├── security-auditor.md          # Custom/Extended Subagent persona for GDPR & IAM review
│   ├── test-engineer.md             # Subagent persona for pytest & contract testing
│   └── code-reviewer.md             # Subagent persona for clean architecture enforcement
├── fixtures/
│   ├── mock_workspace_users.json    # Simulated Google Workspace Enterprise directory
│   ├── mock_org_units.json          # Simulated Workspace OU hierarchy
│   ├── mock_dlp_rules.json          # Simulated Cloud Identity DLP rules
│   └── sample_docs/                 # Dummy contracts with fake German IBANs/PII for scanning
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI entry point & lightweight dashboard UI
│   ├── config.py                    # Env config & feature flags (LIVE vs MOCK mode)
│   ├── models/
│   │   └── schemas.py               # Pydantic v2 models for DLP, Users, OUs, Audit Logs
│   ├── ports/
│   │   └── workspace_port.py        # Abstract base classes for Google Workspace APIs
│   ├── adapters/
│   │   ├── google_live_adapter.py   # Live Drive & Sheets OAuth2 client
│   │   └── mock_admin_adapter.py    # Enterprise Admin SDK & S/MIME mock adapter
│   ├── services/
│   │   ├── dlp_scanner.py           # Gemini 2.5 Flash PII & DLP classification engine
│   │   ├── security_posture.py      # S/MIME, 2SV & OU compliance calculator
│   │   └── onboarding_copilot.py    # Automated HR-to-Workspace provisioning service
│   └── mcp_server/
│       └── workspace_mcp.py         # Custom stdio MCP server for Antigravity
├── tests/
│   ├── test_dlp_scanner.py
│   ├── test_security_posture.py
│   └── test_onboarding_copilot.py
├── docs/
│   └── screenshots/                 # Evidence of Antigravity skills, subagents & Ctrl+R
├── AGENTS.md                        # Antigravity project governance & GDPR coding rules
├── SPEC.md                          # Generated via /agent-skills:spec-driven-development
├── plan.md                          # This master blueprint
├── requirements.txt
└── Dockerfile                       # Google Cloud Run ready container definition
```

---

## 5. Antigravity Execution Plan (Maximizing All Features)

To prove to the CTO that you use Antigravity at an advanced architectural level, follow this exact execution sequence and capture screenshots at each step:

### Step 1: Install Addy Osmani’s `agent-skills` & Configure `AGENTS.md`
1. Install the plugin in your terminal:
   ```bash
   agy plugin install https://github.com/addyosmani/agent-skills.git
   agy plugin list
   ```
2. Create `AGENTS.md` in the root folder containing strict engineering rules:
   * **Rule 1 (Spec First):** Never write application code before `SPEC.md` is finalized.
   * **Rule 2 (GDPR Log Safety):** Never log raw file contents, email bodies, or PII to `stdout` or SQLite; only log SHA-256 hashes and redacted metadata.
   * **Rule 3 (Least Privilege OAuth):** Only request read-only scopes (`drive.readonly`, `spreadsheets.readonly`) unless explicitly provisioning.
   * **Rule 4 (TDD):** Every service in `src/services/` must have a corresponding `pytest` unit test in `tests/` before implementation is marked complete.

### Step 2: Invoke Direct Namespaced Skills (Bypassing Legacy `.toml` Issue)
Inside your Antigravity session, invoke the skills explicitly and screenshot the output:
1. `/agent-skills:spec-driven-development`
   * *Prompt:* "Read `plan.md` and `AGENTS.md`. Generate a formal technical specification in `SPEC.md` defining the Pydantic schemas, port interfaces, and Gemini system prompts for GoogleGuard AI."
2. `/agent-skills:planning-and-task-breakdown`
   * *Prompt:* "Break `SPEC.md` down into atomic, testable implementation tasks ordered by dependency."
3. `/agent-skills:test-driven-development`
   * *Prompt:* "Write the failing `pytest` test suite in `tests/` for the DLP scanner, S/MIME auditor, and onboarding copilot using the JSON fixtures."
4. `/agent-skills:incremental-implementation`
   * *Prompt:* "Implement the adapters and services incrementally until all tests in `tests/` pass."

### Step 3: Orchestrate Subagents (Parallel & Persona-Based)
1. **Parallel Execution (`antigravity-sub-agent-mcp`):**
   * Spawn three concurrent subagents using `submit_agent` and collect with `get_agent_results`:
     * **Subagent 1:** Generate realistic German enterprise mock data in `fixtures/` (`mock_workspace_users.json`, `mock_org_units.json`, `mock_dlp_rules.json`).
     * **Subagent 2:** Build the FastAPI REST endpoints and lightweight HTML/Tailwind UI dashboard in `src/main.py`.
     * **Subagent 3:** Write the `Dockerfile` and Cloud Run deployment configuration.
2. **Persona Subagents:**
   * Invoke the **`security-auditor`** subagent to inspect `src/` for hardcoded credentials, overly broad OAuth2 scopes, or GDPR logging leaks.
   * Invoke the **`code-reviewer`** subagent via `/agent-skills:code-review-and-quality` to verify adherence to `AGENTS.md`.

### Step 4: Configure & Run the Custom Workspace MCP Server
Create `.agents/mcp_config.json` in your repository:
```json
{
  "mcpServers": {
    "googleguard-workspace": {
      "command": "python",
      "args": ["src/mcp_server/workspace_mcp.py"],
      "env": {
        "PYTHONPATH": "."
      }
    },
    "sqlite-audit": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "./audit_logs.db"]
    }
  },
  "permissions": {
    "allow": [
      "mcp(googleguard-workspace/get_tenant_compliance_summary)",
      "mcp(googleguard-workspace/scan_drive_file_dlp)",
      "mcp(googleguard-workspace/simulate_user_onboarding)",
      "mcp(sqlite-audit/read_query)"
    ]
  }
}
```
* Open the `/mcp` overlay inside Antigravity, take a screenshot showing `googleguard-workspace` connected, and run a prompt that calls `get_tenant_compliance_summary` live.

### Step 5: Human-in-the-Loop Artifact Review (`Ctrl+R`)
* When Antigravity proposes multi-file changes, press **`Ctrl+R`** to open the **Artifact Review** diff view.
* Take a screenshot of yourself reviewing and approving the diffs. This proves to the CTO that you maintain strict engineering oversight over AI-generated code.

---

## 6. Data Schemas & Fixture Specifications

### `fixtures/mock_org_units.json`
```json
[
  {
    "name": "GoogleGuard Client Corp",
    "orgUnitPath": "/",
    "description": "Root Organization Unit"
  },
  {
    "name": "Executive & Finance",
    "orgUnitPath": "/Executive_Finance",
    "description": "Strict DLP, Mandatory S/MIME, 2SV Hardware Key Required",
    "policies": {"smime_required": true, "two_step_verification": true, "external_drive_sharing": "BLOCKED"}
  },
  {
    "name": "Engineering",
    "orgUnitPath": "/Engineering",
    "description": "Standard DLP, 2SV Required, GitHub & GCP SSO Enabled",
    "policies": {"smime_required": false, "two_step_verification": true, "external_drive_sharing": "WARN"}
  },
  {
    "name": "External Contractors",
    "orgUnitPath": "/Contractors",
    "description": "Zero-Trust Restricted Access, Internal Drive Only",
    "policies": {"smime_required": false, "two_step_verification": true, "external_drive_sharing": "BLOCKED"}
  }
]
```

### `fixtures/mock_workspace_users.json`
```json
[
  {
    "id": "usr_101",
    "primaryEmail": "cfo@client-enterprise.de",
    "name": {"fullName": "Hannah Weber"},
    "orgUnitPath": "/Executive_Finance",
    "isAdmin": false,
    "isEnrolledIn2Sv": true,
    "smimeConfigured": false
  },
  {
    "id": "usr_102",
    "primaryEmail": "dev.lead@client-enterprise.de",
    "name": {"fullName": "Lukas Schmidt"},
    "orgUnitPath": "/Engineering",
    "isAdmin": true,
    "isEnrolledIn2Sv": true,
    "smimeConfigured": true
  },
  {
    "id": "usr_103",
    "primaryEmail": "temp.vendor@client-enterprise.de",
    "name": {"fullName": "Marco Rossi"},
    "orgUnitPath": "/",
    "isAdmin": false,
    "isEnrolledIn2Sv": false,
    "smimeConfigured": false
  }
]
```

---

## 7. Presentation & Documentation Checklist for Sunday

Your slide deck and live demonstration should follow this 15-minute story arc:

1. **Slide 1 — From Interview 1 to Today:**
   * Acknowledge Cezary’s question from the first interview. State clearly: *"You asked about Google AI and Google Workspace, and mentioned building something with Antigravity. I built **GoogleGuard AI**—an enterprise Workspace DLP & Onboarding Copilot—using Antigravity’s full orchestration stack."*
2. **Slide 2 — Understanding GoogleGuard Enterprise’s Domain:**
   * Briefly explain Google Workspace Enterprise security pillars: **Organizational Units (OUs), S/MIME email encryption, Data Loss Prevention (DLP), Context-Aware Access, and GDPR/DSGVO data residency**.
3. **Slide 3 — GoogleGuard AI Architecture (Hexagonal + Zero-Cost Dev Mode):**
   * Show the architecture diagram from Section 2. Explain how you combined live Google Drive/Sheets OAuth2 and Gemini 2.5 Flash with contract-tested Mock Adapters for Enterprise Admin SDK APIs.
4. **Slide 4 — Antigravity Governance (`AGENTS.md` + Addy Osmani `agent-skills`):**
   * Show screenshots of `AGENTS.md` and your direct invocations of `/agent-skills:spec-driven-development` and `/agent-skills:test-driven-development` (noting how you bypassed the `agy 1.1.x` legacy `.toml` command limitation).
5. **Slide 5 — Subagent Orchestration & Security Auditing:**
   * Show how you ran parallel subagents for fixtures, API routes, and Dockerization, and used the `security-auditor` persona to verify zero PII leakage in logs. Include your `Ctrl+R` Artifact Review screenshot.
6. **Slide 6 — Custom Google Workspace MCP Server:**
   * Show `.agents/mcp_config.json` with granular `mcp(server/tool)` allowlists and explain how your custom Python MCP server lets any GoogleGuard Enterprise engineer inspect tenant compliance directly from Antigravity.
7. **Slide 7 — Live Demo (3 Minutes):**
   * **Part A (Web UI / FastAPI):** Trigger a DLP scan on a sample contract containing a German IBAN and show Gemini flagging the GDPR violation and public sharing risk.
   * **Part B (Smart Onboarding):** Trigger an onboarding analysis for a new "Senior Payroll Specialist" and show Gemini assigning `/Executive_Finance` with mandatory S/MIME.
   * **Part C (Antigravity CLI MCP):** Run a prompt inside Antigravity calling your custom `googleguard-workspace` MCP server live.
8. **Slide 8 — How This Accelerates GoogleGuard Enterprise Engineering:**
   * Propose how GoogleGuard Enterprise can standardize reusable `SKILL.md` playbooks and internal Workspace MCP servers to cut client migration, scripting, and compliance auditing time by 40–60%.