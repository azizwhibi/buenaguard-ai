# GoogleGuard AI: 15-Minute Executive Demo Script

**Audience:** Cezary Augustynowicz (CTO) & GoogleGuard Enterprise GmbH Leadership  
**Presenter:** AI Engineering Candidate  
**Project:** GoogleGuard AI (Google Workspace Security, DLP & Onboarding Copilot)  
**Target Duration:** 15 Minutes (12 min Presentation & Demo + 3 min Q&A)  

---

## Timeline & Slide Breakdown

```
[00:00 - 01:30] Slide 1: Introduction & Connection to Interview 1
[01:30 - 03:00] Slide 2: Understanding GoogleGuard Enterprise’s Enterprise Workspace Domain
[03:00 - 05:00] Slide 3: Hexagonal Architecture & Zero-Billing Hybrid Strategy
[05:00 - 07:00] Slide 4: Antigravity Governance (AGENTS.md & Addy Osmani Skills)
[07:00 - 08:30] Slide 5: Autonomous Subagent Pack & Verification Loops
[08:30 - 10:00] Slide 6: Custom Google Workspace MCP Server & Least Privilege
[10:00 - 13:00] Slide 7: Live 3-Part Demonstration (Web UI, Onboarding, MCP)
[13:00 - 15:00] Slide 8: Enterprise Business ROI & Engineering Acceleration
```

---

## Detailed Script & Live Demo Execution

### Slide 1: Introduction & Connection to Interview 1 (1.5 min)
* **Speaker Script:**
  > *"Guten Tag Cezary and GoogleGuard Enterprise team. In our first conversation, you challenged me on how modern agentic AI can interface with Google Cloud and Google Workspace Enterprise, and asked how I leverage Google Antigravity in real production workflows.
  > Today, I am proud to present **GoogleGuard AI**—an enterprise Google Workspace Security, DLP, and Onboarding Copilot built completely from scratch using Antigravity's advanced architectural orchestration."*
* **Key Visual:** GoogleGuard AI logo, tagline, and project repository overview.

---

### Slide 2: Understanding GoogleGuard Enterprise’s Enterprise Workspace Domain (1.5 min)
* **Speaker Script:**
  > *"For GoogleGuard Enterprise’s enterprise clients, Google Workspace is not just email—it is the core identity and security perimeter. In regulated German and European markets, four pillars dictate security:
  > 1. **Organizational Unit (OU) Policies:** Strict segregation between Executive Finance, Engineering, and Contractors.
  > 2. **S/MIME Email Encryption:** Non-negotiable for CFOs and finance staff handling payroll and banking.
  > 3. **2-Step Verification (2SV):** Hardware security key enforcement.
  > 4. **GDPR / DSGVO Data Residency & DLP:** Strict rules against public sharing of German IBANs, Steuer-IDs, and salary records under Art. 6, 32, and 83."*

---

### Slide 3: Hexagonal Architecture & Zero-Billing Hybrid Strategy (2 min)
* **Speaker Script:**
  > *"To ensure this solution is robust, testable, and zero-cost during development, I architected GoogleGuard AI using strict Hexagonal (Ports & Adapters) principles:
  > - **Domain Core (`src/services/`):** Pure Python business logic (`DLPScannerService`, `SecurityPostureService`, `OnboardingCopilotService`) depending strictly on abstract ports (`src/ports/`).
  > - **Zero-Billing Hybrid Engine:** In development mode (`WORKSPACE_MODE=MOCK`), it runs 100% offline using contract-tested fixtures simulating Google Admin SDK Directory and Cloud Identity DLP APIs.
  > - **Live Google APIs:** Seamlessly connects to live Google Drive, Sheets, and Google AI Studio Gemini 2.5 Flash when credentials are present, falling back gracefully without crashing."*

---

### Slide 4: Antigravity Governance (`AGENTS.md` + Addy Osmani Skills) (2 min)
* **Speaker Script:**
  > *"AI assistance without strict governance leads to bloat and security regressions. I established eleven immutable engineering rules in `AGENTS.md` and integrated Addy Osmani’s `agent-skills` subagent pack:
  > - **Rule 1 (Spec First):** Code was written only after `SPEC.md` and `TODO.md` were formalized.
  > - **Rule 2 (Graphify Knowledge Graph):** Traced 392 nodes and 857 edges across session memory to eliminate circular dependencies.
  > - **Rule 3 (Ponytail Discipline):** Channeling a 'lazy senior dev'—smallest correct changes, zero speculative abstractions.
  > - **Rule 4 (GDPR Zero Raw PII):** All text is pre-screened and tokenized into surrogate tags (`[REDACTED_IBAN_1]`); SQLite stores only SHA-256 hashes."*

---

### Slide 5: Autonomous Subagent Pack & Verification Loops (1.5 min)
* **Speaker Script:**
  > *"Never let the same agent write and approve code. At the end of every phase, I spawned specialized subagents:
  > - `test-engineer`: Audited test fixtures and drove statement coverage to **91.12% across the entire project**.
  > - `security-auditor`: Validated least-privilege OAuth scopes (`drive.readonly`) and caught a path traversal edge-case in early review.
  > - `code-reviewer`: Enforced Hexagonal port conformance and Pydantic v2 strictness.
  > - **Human-in-the-Loop (`Ctrl+R`):** I reviewed and approved structured Review Receipts before every phase transition."*

---

### Slide 6: Custom Google Workspace MCP Server (1.5 min)
* **Speaker Script:**
  > *"To make this tool accessible across Antigravity, I implemented a standalone stdio MCP server in `src/mcp_server/workspace_mcp.py` using Python's `FastMCP` / `MCPServer`.
  > It exposes four high-level administrative tools:
  > 1. `check_domain_dlp_status`: Domain-wide compliance scoring.
  > 2. `list_workspace_ous`: OU tree and policy inspection.
  > 3. `scan_drive_file_dlp`: Instant GDPR document DLP analysis.
  > 4. `simulate_user_onboarding`: Least-privilege HR onboarding.
  > In `.agents/mcp_config.json`, tool access is governed by strict granular permissions with zero wildcards."*

---

### Slide 7: Live 3-Part Demonstration (3 min)

#### Part A: Web Dashboard & DLP Document Scan
1. **Launch Server:**
   ```powershell
   python -m uvicorn src.main:app --port 8000
   ```
2. **Open Browser:** Navigate to `http://localhost:8000/`.
3. **Show Dashboard:** Point out tenant compliance score (66.7%), flagged CFO missing S/MIME, and flagged contractor missing 2SV.
4. **Trigger Scan:** Click **"Scan Drive File"** on `contract_with_iban.txt`.
5. **Observe:** Highlight `CRITICAL` risk level, detected German `IBAN` and `STEUER_ID`, cited GDPR Art. 6, 32, and 83, concrete remediation recommendation, and completely redacted preview with zero raw PII.

#### Part B: Zero-Trust HR Onboarding Copilot
1. In the Web Dashboard right panel, enter:
   - **Full Name:** `Sarah Connor`
   - **Email:** `sarah.connor@client-enterprise.de`
   - **Department:** `Finance & Accounting`
   - **Job Title:** `Senior Payroll Specialist`
2. Click **"Provision User"**.
3. **Observe:** Copilot automatically maps candidate to `/Executive_Finance`, mandates `smimeRequired: true`, enrolls into `finance-team@client-enterprise.de`, provisions user in Admin directory, and generates a personalized Welcome Security Checklist.

#### Part C: Antigravity MCP Tool Execution
1. Run pytest validating the live MCP stdio handshake and tool execution:
   ```powershell
   pytest tests/test_workspace_mcp.py -v
   ```
2. Explain how any engineer or AI agent in Antigravity can invoke `scan_drive_file_dlp` or `check_domain_dlp_status` directly from the chat prompt.

---

### Slide 8: Enterprise Business ROI & Engineering Acceleration (2 min)
* **Speaker Script:**
  > *"GoogleGuard AI delivers measurable business impact for GoogleGuard Enterprise:
  > - **40% to 60% reduction** in client tenant migration and onboarding setup time.
  > - **100% automated GDPR compliance auditing** for Google Drive and Gmail.
  > - **Zero cloud billing dependencies** during development and testing.
  > - **Reusable Antigravity Skills & MCP servers** that GoogleGuard Enterprise engineers can leverage across client engagements."*
