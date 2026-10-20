# GoogleGuard AI: Google Workspace Security, GDPR/DSGVO DLP & Onboarding Copilot

[![Python 3.13+](https://img.shields.io/badge/python-3.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.10+-e92063.svg)](https://docs.pydantic.dev/)
[![Google GenAI SDK](https://img.shields.io/badge/Google%20AI%20Studio-Gemini%203.8%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Standard%20Stdio-purple.svg)](https://modelcontextprotocol.io/)
[![GDPR Compliant](https://img.shields.io/badge/GDPR%2FDSGVO-Zero%20Raw%20PII-green.svg)](https://gdpr-info.eu/)
[![Tests Passing](https://img.shields.io/badge/tests-76%20passed-brightgreen.svg)](file:///D:/buenaai/tests)

**GoogleGuard AI** is an enterprise-grade Google Workspace security automation platform and copilot engineered for **GoogleGuard Enterprise GmbH** (DACH Google Cloud & Workspace Premier Partner). It combines local regex-based privacy filtering, **Google AI Studio Gemini 3.8 Flash** structured reasoning, and Google Drive & Sheets APIs into a zero-trust compliance engine.

Designed under a **Zero-Billing Hybrid Strategy**, GoogleGuard AI operates seamlessly in two modes:
1. **LIVE Mode:** Interacts directly with Google AI Studio and real Google Drive folders / Google Sheets using read-only OAuth 2.0 scopes.
2. **MOCK Mode:** Operates 100% offline with zero cloud billing dependencies, using synthetic German enterprise fixtures matching Google Workspace Admin SDK schemas.

---

## Table of Contents

1. [Key Capabilities & Architecture](#key-capabilities--architecture)
2. [Hexagonal Architecture (Ports & Adapters)](#hexagonal-architecture-ports--adapters)
3. [GDPR / DSGVO Privacy & Security Governance](#gdpr--dsgvo-privacy--security-governance)
4. [Live Google Integrations](#live-google-integrations)
5. [Repository Structure](#repository-structure)
6. [Installation & Getting Started](#installation--getting-started)
7. [Authentication Setup (Google OAuth 2.0 & Gemini API)](#authentication-setup-google-oauth-20--gemini-api)
8. [Running the Application](#running-the-application)
   - [Web Dashboard & REST API](#1-executive-web-dashboard--rest-api)
   - [Custom Workspace MCP Server](#2-custom-google-workspace-mcp-server)
   - [Executing Unit & Contract Tests](#3-running-tests-with-coverage)
9. [API Endpoints Reference](#api-endpoints-reference)
10. [Test Dataset Guide (`drive_dlp_files` & Sheets)](#test-dataset-guide)
11. [Containerization & Google Cloud Run Deployment](#containerization--google-cloud-run-deployment)
12. [Verification Receipts & Quality Assurance](#verification-receipts--quality-assurance)

---

## Key Capabilities & Architecture

```
                          ┌─────────────────────────────────────┐
                          │         GoogleGuard AI Core          │
                          └──────────────────┬──────────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               ▼                             ▼                             ▼
    ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
    │  GDPR / DSGVO DLP    │      │  Zero-Trust HR       │      │  Tenant Posture &    │
    │  Document Scanner    │      │  Onboarding Copilot  │      │  Compliance Auditor  │
    └──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘
               │                             │                             │
    ┌──────────▼───────────┐      ┌──────────▼───────────┐      ┌──────────▼───────────┐
    │ PIIPreFilter Tokenizer│     │ Least-Privilege OU   │      │ 2SV Enforcement &    │
    │ & SHA-256 Audit DB   │      │ & S/MIME Encryption  │      │ S/MIME Coverage Audit│
    └──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘
               │                             │                             │
               └─────────────────────────────┼─────────────────────────────┘
                                             │
               ┌─────────────────────────────┴─────────────────────────────┐
               ▼                                                           ▼
    ┌───────────────────────────────────────┐             ┌───────────────────────────────────┐
    │  FastAPI Executive Web Dashboard     │             │  Antigravity Stdio FastMCP Server │
    │  http://127.0.0.1:8000                │             │  4 Granular Administrative Tools  │
    └───────────────────────────────────────┘             └───────────────────────────────────┘
```

### 1. GDPR / DSGVO DLP Document Scanner
- **Local Regex Pre-Screener (`PIIPreFilter`):** Detects German IBANs (`DE...`), Tax Identification Numbers (`Steuer-ID`), German Passport numbers, European credit cards, employee salaries, and email addresses.
- **Tokenization:** Automatically masks sensitive substrings (e.g., `[REDACTED_IBAN_1]`, `[REDACTED_STEUER_ID_1]`) before text is emitted to logs, databases, or LLMs.
- **Gemini 3.8 Flash Analysis:** Evaluates regulatory impact under GDPR (Articles 6, 9, 32), assigns severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and generates actionable remediation guidance.
- **Tamper-Resistant Audit Store:** Stores strictly SHA-256 hashes and redacted risk assessments in SQLite (`audit_logs.db`).

### 2. Zero-Trust HR Onboarding Copilot
- Evaluates incoming employee role, department, and location.
- Automatically assigns the single strictest least-privilege Organizational Unit (OU):
  - `/Executive_Finance`: Mandatory S/MIME certificate encryption, mandatory 2SV (FIDO2 keys), restricted financial shared drives.
  - `/Engineering`: Standard 2SV hardware key enforcement, developer Google Groups.
  - `/Contractors`: Zero-trust restricted boundary, no external sharing, read-only internal access.
  - `/`: Standard staff.
- Generates individualized security onboarding checklists.

### 3. Tenant Security Posture Compliance Auditor
- Computes overall domain compliance score (0–100%).
- Audits active 2-Step Verification (2SV) enrollment and S/MIME deployment rates across all tenant accounts.
- Identifies policy gaps (e.g., Finance managers lacking S/MIME certificates or admins lacking 2SV) and issues remediation steps.

### 4. Custom Model Context Protocol (MCP) Server
- Exposes 4 administrative tools over JSON-RPC stdio for autonomous AI assistants:
  1. `check_domain_dlp_status`: Domain posture, compliance score, and non-compliant accounts.
  2. `list_workspace_ous`: Hierarchy of OUs and assigned security policies.
  3. `scan_drive_file_dlp`: Deep DLP scan of Google Drive files with redacted preview.
  4. `simulate_user_onboarding`: Evaluation of candidate roles and OU provisioning.
- Governed by granular tool permissions in [`.agents/mcp_config.json`](file:///D:/buenaai/.agents/mcp_config.json).

---

## Hexagonal Architecture (Ports & Adapters)

The project strictly follows Hexagonal Architecture principles (Rule 7 in `AGENTS.md`). Business logic has zero concrete external dependencies:

```
src/
├── models/schemas.py         <-- Pure Pydantic v2 domain schemas (zero framework imports)
├── ports/workspace_port.py   <-- Abstract domain interfaces (Python ABCs)
├── services/                 <-- Core domain business logic (depends ONLY on ports & models)
│   ├── pii_prefilter.py      <-- Regex tokenizer & zero-PII masking
│   ├── dlp_scanner.py        <-- GDPR DLP scanning orchestrator
│   ├── onboarding_copilot.py <-- Zero-trust OU mapper & checklist generator
│   └── security_posture.py   <-- Tenant posture audit & scoring engine
└── adapters/                 <-- Concrete implementations wired dynamically via factory
    ├── factory.py            <-- Environment-driven adapter factory
    ├── gemini_client.py      <-- Google AI Studio Gemini API client with multi-model fallback
    ├── google_live_adapter.py<-- Live Google Drive v3 & Sheets v4 client
    ├── mock_admin_adapter.py <-- Local synthetic JSON Google Workspace Admin SDK adapter
    └── audit_store.py        <-- SQLite zero-raw-PII audit logger
```

---

## GDPR / DSGVO Privacy & Security Governance

Every line of code complies with the engineering prime directives documented in [`AGENTS.md`](file:///D:/buenaai/AGENTS.md):

- **Rule 4 (Zero Raw PII Logging):** Raw personal information (German IBANs, Steuer-ID, passports, salaries) is **never** emitted to `stdout`, `stderr`, application loggers, or SQLite records.
- **Rule 5 (Least-Privilege OAuth Scopes):** Live Google Drive and Sheets clients strictly request read-only permissions:
  - `https://www.googleapis.com/auth/drive.readonly`
  - `https://www.googleapis.com/auth/spreadsheets.readonly`
- **Rule 6 (Mandatory TDD):** 100% of services and adapters are verified by unit and contract test suites with $\ge 90\%$ statement coverage.
- **Rule 8 (Zero-Billing Hybrid Mode):** All features operate fully offline in `MOCK` mode using synthetic JSON contracts when credentials are not present.

---

## Live Google Integrations

### 1. Google AI Studio (Gemini 3.8 Flash)
The platform integrates with Google AI Studio using the official `google-genai` SDK. To guard against Google API model retirements (such as the sunsetting of `gemini-2.5-flash`), [`src/adapters/gemini_client.py`](file:///D:/buenaai/src/adapters/gemini_client.py) incorporates an automatic resilient fallback chain:
`gemini-3.8-flash` $\longrightarrow$ `gemini-flash-latest` $\longrightarrow$ `gemini-3.5-flash` $\longrightarrow$ `gemini-2.0-flash`.

### 2. Google Drive API (v3)
- **Folder Isolation:** To prevent scanning unrelated user files, file enumeration is strictly scoped to the dedicated folder **`drive_dlp_files`**.
- **Media Ingestion:** Automatically exports Google Docs (`text/plain`), Google Sheets (`text/csv`), and downloads text/binary files via `get_media()`.
- **Live Sharing Audit:** Evaluates Google Drive file permissions to detect public links (`anyone`) and external domain collaborators.

### 3. Google Sheets API (v4)
- **Live Spreadsheet Sync:** Automatically reads onboarding rows from Google Spreadsheet:
  `https://docs.google.com/spreadsheets/d/16LPTEw5fk2MS9Jal7stUQwopkWjmQdKhUZbGFqAnzp8/edit?gid=1074968164`
- **Dynamic Ingestion:** Extracts candidate records (`fullName`, `email`, `department`, `jobTitle`, `manager`, `location`) to populate the interactive onboarding copilot in real time.

---

## Repository Structure

```
D:/buenaai/
├── .agents/
│   └── mcp_config.json                 # Antigravity MCP server tool permissions
├── agents/                             # Antigravity subagent persona definitions
│   ├── code-reviewer.md                # 5-axis code reviewer persona
│   ├── security-auditor.md             # Security and GDPR compliance persona
│   └── test-engineer.md                # QA and edge-case verification persona
├── docs/
│   ├── AUDIT_REPORT.md                 # Security & architecture audit receipt
│   ├── DEMO_SCRIPT.md                  # 15-minute presentation & live demo guide
│   └── PRESENTATION_NOTES.md           # Business ROI & executive briefing notes
├── fixtures/                           # Synthetic German enterprise test contracts
│   ├── dlp_rules.json                  # Google Workspace Cloud Identity DLP rules
│   ├── org_units.json                  # Workspace Organizational Unit hierarchy
│   ├── sample_docs/                    # Sample offline test documents
│   │   ├── clean_notes.txt
│   │   ├── contract_with_iban.txt
│   │   └── tax_id_export.csv
│   └── users.json                      # Enterprise staff, contractors, and admins
├── scripts/
│   └── authenticate_google.py          # Google OAuth 2.0 loopback authentication script
├── src/
│   ├── adapters/                       # Hexagonal adapters (Gemini, Google Drive/Sheets, Mock)
│   ├── mcp_server/                     # Stdio FastMCP Workspace server
│   │   └── workspace_mcp.py
│   ├── models/                         # Pydantic v2 schemas
│   ├── ports/                          # Abstract ABC interfaces
│   ├── services/                       # Business logic (DLP scanner, Onboarding, Posture)
│   ├── templates/                      # Tailwind CSS dashboard template
│   │   └── index.html
│   ├── config.py                       # Pydantic-settings configuration
│   └── main.py                         # FastAPI web application entrypoint
├── test_data_for_google/               # Live test files for Google Drive & Sheets
│   ├── drive_dlp_files/                # 5 realistic test documents (Critical, High, Medium, Low)
│   ├── google_sheets_onboarding_candidates.csv # 6 candidate onboarding records
│   └── README.md                       # Upload & testing instructions
├── tests/                              # Comprehensive pytest suite (76 tests)
├── .env.example                        # Template environment configuration
├── .gitignore                          # Strict secret exclusion
├── AGENTS.md                           # 11 engineering governance rules
├── cloudrun.yaml                       # Google Cloud Run deployment configuration
├── Dockerfile                          # Production container specification (non-root)
├── pyproject.toml                      # Pytest and coverage settings
├── requirements.txt                    # Pinned zero-billing dependencies
└── TODO.md                             # Phased execution roadmap
```

---

## Installation & Getting Started

### Prerequisites
- **Python:** Version 3.13 or 3.14 (64-bit).
- **Git:** Installed and configured.
- **Operating System:** Windows, macOS, or Linux.

### 1. Clone the Repository
```bash
git clone https://github.com/azizwhibi/googleguard-ai.git
cd googleguard-ai
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Using standard Python launcher
py -3.13 -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Review your `.env` configuration:
```ini
# Execution mode: LIVE for real Google services, MOCK for offline zero-billing fixtures
WORKSPACE_MODE=LIVE

# Google AI Studio Gemini API Key (or place in geminiapikey.txt)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash

# Google OAuth Credentials
GOOGLE_OAUTH_CREDENTIALS=credentials.json
GOOGLE_OAUTH_TOKEN=token.json

# Live Google Resources
GOOGLE_ONBOARDING_SPREADSHEET_ID=16LPTEw5fk2MS9Jal7stUQwopkWjmQdKhUZbGFqAnzp8
GOOGLE_DRIVE_DLP_FOLDER_NAME=drive_dlp_files

# Server Configuration
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO
AUDIT_DB_PATH=audit_logs.db
```

---

## Authentication Setup (Google OAuth 2.0 & Gemini API)

### Step 1: Google AI Studio API Key
1. Obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Save the key in `geminiapikey.txt` in the project root, or set `GEMINI_API_KEY` in `.env`.

### Step 2: Google Cloud OAuth 2.0 Credentials
1. In your Google Cloud Console project, enable:
   - **Google Drive API** (`drive.googleapis.com`)
   - **Google Sheets API** (`sheets.googleapis.com`)
2. Go to **APIs & Services** > **Credentials** and create an **OAuth 2.0 Client ID** with Application Type: **Desktop app**.
3. Download the JSON file and save it as `credentials.json` in the project root.
4. Under **OAuth consent screen** > **Test users**, add your Gmail address.

### Step 3: Run the One-Click OAuth Flow
Run the authentication script:
```powershell
python scripts/authenticate_google.py
```
- Your default browser will launch automatically.
- Log in and grant read-only access to Drive and Sheets.
- The script captures the code via loopback and generates `token.json`.
- `token.json` is stored locally and protected by `.gitignore`.

---

## Running the Application

### 1. Executive Web Dashboard & REST API
Start the FastAPI server using Uvicorn:
```powershell
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

#### What the Dashboard Displays:
- **Tenant Posture Score:** 2SV and S/MIME compliance rate across enterprise accounts.
- **Live Google Drive Repository:** Enumerates all files located inside `drive_dlp_files` with real-time sharing risk indicators (`PUBLIC_LINK`, `EXTERNAL_SHARE`, `DOMAIN_INTERNAL`).
- **Interactive 1-Click DLP Scanner:** Scan any Drive file to view PII tokenization, GDPR Articles impacted, and Gemini recommendations.
- **Interactive HR Onboarding Copilot:** Select any candidate from your live Google Sheet to simulate zero-trust OU provisioning and S/MIME enforcement.

---

### 2. Custom Google Workspace MCP Server
GoogleGuard AI provides a standalone Model Context Protocol server communicating over stdio.

#### Run Directly:
```powershell
python -m src.mcp_server.workspace_mcp
```

#### Antigravity / Claude Desktop Integration:
Add to your MCP configuration file (e.g. `.agents/mcp_config.json`):
```json
{
  "mcpServers": {
    "googleguard-workspace": {
      "command": "python",
      "args": ["-m", "src.mcp_server.workspace_mcp"],
      "env": {
        "WORKSPACE_MODE": "LIVE",
        "PYTHONPATH": "."
      }
    }
  }
}
```

---

### 3. Running Tests with Coverage
Execute the complete test suite:
```powershell
# Run all tests
pytest -v

# Run with statement coverage report
pytest --cov=src --cov-report=term-missing tests/
```

**Status:** **76 passed in 15.70s** with >90% coverage across domain services.

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Responsive Tailwind CSS executive compliance dashboard |
| `GET` | `/health` | Health probe reporting `status`, `mode`, and version |
| `GET` | `/api/v1/posture` | Tenant compliance score, audited users, and flagged violations |
| `POST` | `/api/v1/scan-dlp` | Evaluates file for PII, returns redacted preview & risk rating |
| `POST` | `/api/v1/onboard` | Evaluates candidate and assigns least-privilege OU & checklist |
| `GET` | `/api/v1/drive/files` | Lists files strictly inside target Google Drive folder |
| `GET` | `/api/v1/auth/google/status`| Current OAuth authentication state and token health |

---

## Test Dataset Guide

Ready-to-use testing datasets are located in [`test_data_for_google/`](file:///D:/buenaai/test_data_for_google/):

### Google Drive Test Documents ([`test_data_for_google/drive_dlp_files/`](file:///D:/buenaai/test_data_for_google/drive_dlp_files/))
Upload these files into a folder named **`drive_dlp_files`** on your Google Drive:

1. `01_CRITICAL_Executive_Payroll_Q4_2026.csv`: Executive salaries, German IBANs, Steuer-IDs (**Expected: CRITICAL / HIGH**).
2. `02_HIGH_Arbeitsvertrag_Senior_Ingenieur.txt`: Employment contract with German passport number and bank details (**Expected: HIGH**).
3. `03_HIGH_SEPA_B2B_Payment_Instructions.txt`: Wire transfer batch containing DE, FR, and AT IBANs (**Expected: HIGH**).
4. `04_MEDIUM_External_Contractor_Agreement.txt`: Freelancer agreement with Spanish IBAN and contractor terms (**Expected: MEDIUM**).
5. `05_LOW_Clean_Sprint_Planning_Notes.txt`: Engineering notes with zero personal data (**Expected: LOW / COMPLIANT**).

### Google Sheets Onboarding Candidates ([`google_sheets_onboarding_candidates.csv`](file:///D:/buenaai/test_data_for_google/google_sheets_onboarding_candidates.csv))
Contains 6 candidate profiles (CFO, Payroll Specialist, Cloud Architect, Backend Engineer, Contractor Pentester, Compliance Officer) demonstrating automated routing to `/Executive_Finance`, `/Engineering`, and `/Contractors`.

---

## Containerization & Google Cloud Run Deployment

GoogleGuard AI is packaged for cloud-native zero-downtime deployment:

### Docker Container Build
```bash
docker build -t googleguard-ai:latest .
docker run -p 8080:8080 --env-file .env googleguard-ai:latest
```
- **Security:** Runs as non-root user (`USER nonroot`).
- **Secret Protection:** `.dockerignore` excludes `token.json`, `credentials.json`, `geminiapikey.txt`, `.env`, and `audit_logs.db`.

### Deploy to Google Cloud Run
Deploy using the provided [`cloudrun.yaml`](file:///D:/buenaai/cloudrun.yaml):
```bash
gcloud run services replace cloudrun.yaml --region europe-west3
```

---

## Verification Receipts & Quality Assurance

- **Phase 1 Receipt:** Foundations, governance, and `PIIPreFilter` verified.
- **Phase 2 Receipt:** Mock Admin SDK fixtures and SQLite audit store verified.
- **Phase 3 Receipt:** Core DLP scanner, onboarding copilot, and REST endpoints verified.
- **Phase 4 Receipt:** Custom Workspace FastMCP server and `.agents/mcp_config.json` verified.
- **Phase 5 Receipt:** End-to-end security audits, Cloud Run configuration, and live demo script verified.
- **Full Audit Report:** Detailed in [`docs/AUDIT_REPORT.md`](file:///D:/buenaai/docs/AUDIT_REPORT.md).
- **15-Minute Executive Demo Script:** Detailed in [`docs/DEMO_SCRIPT.md`](file:///D:/buenaai/docs/DEMO_SCRIPT.md).

---

## License & Compliance Notice

Developed for **GoogleGuard Enterprise GmbH**. Built in accordance with European General Data Protection Regulation (**GDPR / DSGVO Art. 6, 9, 32**) and Google Workspace API Services User Data Policy.
