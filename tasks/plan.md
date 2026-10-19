# Implementation Plan: BuenaGuard AI

**Project Title:** BuenaGuard AI — Automated Google Workspace DLP, S/MIME & Onboarding Copilot  
**Target Organization:** BuenaCloud GmbH (Cezary Augustynowicz & CTO)  
**Cost / Billing Profile:** 100% Free Tier / Zero Billing Card Required  
**Single Source of Truth:** `plan.md` / `buenaguard_ai_master_specification_plan.md`  
**Technical Specification:** `SPEC.md`  
**Execution Roadmap:** `TODO.md` / `tasks/todo.md`  

## Overview
BuenaGuard AI is an automated Google Workspace security, DLP compliance, and zero-trust onboarding copilot designed specifically for BuenaCloud GmbH's enterprise clientele in Germany and the EU. It combines free-tier live Google Drive and Sheets APIs with Google AI Studio's Gemini 2.5 Flash and a contract-tested Enterprise Mock Adapter simulating Workspace Admin SDK Directory and Cloud Identity DLP rules.

## Architecture Decisions
1. **Hexagonal (Ports-and-Adapters) Architecture:** Core domain logic (`src/services/`) depends exclusively on abstract ports (`src/ports/workspace_port.py`), completely decoupled from live Google APIs or local mock adapters.
2. **Zero-Billing Hybrid Strategy:** Live free Google Drive/Sheets OAuth2 (`credentials.json`) + free Google AI Studio key (`geminiapikey.txt`) for active AI operations, coupled with local JSON fixtures (`fixtures/`) for Enterprise Admin SDK Directory and S/MIME APIs.
3. **GDPR/DSGVO Multi-Layered Privacy Defense:** Fast local regex pre-filter tokenizes all German PII before transmission; raw PII is never written to `stdout`, `stderr`, or persistent SQLite logs.
4. **Antigravity Custom Workspace MCP Server:** A standalone stdio MCP server exposes 4 administrative tools (`check_domain_dlp_status`, `list_workspace_ous`, `scan_drive_file_dlp`, `simulate_user_onboarding`) with granular permissions in `.agents/mcp_config.json`.
5. **Strict Test-Driven Development (TDD):** Every component has a failing unit or contract test written first, maintaining deterministic offline pass rates.

## Task List & Checkpoints

### Phase 1: Foundation, Governance & Zero-Billing Setup
- [ ] [P1-T1] Antigravity Governance & Security Rules (`AGENTS.md`)
- [ ] [P1-T2] Repository Scaffolding, Package Dependencies & Environment Configuration
- [ ] [P1-T3] Live Google AI Studio Gemini API Client Wrapper
- [ ] [P1-T4] OAuth2 Desktop Client Wiring for Free Google Drive & Sheets APIs
- [ ] **Checkpoint: Phase 1 Foundation Checkpoint** (All tests pass, zero secret leaks)

### Phase 2: Enterprise Mock Adapter & Fixtures
- [ ] [P2-T1] Enterprise Domain Pydantic Schemas & Port Definitions
- [ ] [P2-T2] German Enterprise Mock Fixtures Generation
- [ ] [P2-T3] Enterprise Mock Workspace Admin Adapter Implementation
- [ ] [P2-T4] Environment-Aware Workspace Adapter Factory & SQLite Audit Store
- [ ] **Checkpoint: Phase 2 Enterprise Mock Checkpoint** (Contract tests pass, Hexagonal decoupling verified)

### Phase 3: Core Services via TDD
- [ ] [P3-T1] Local Regex Pre-Scanner & PII Masking Engine
- [ ] [P3-T2] Gemini 2.5 Flash Structured DLP & GDPR Document Scanner
- [ ] [P3-T3] S/MIME & Tenant Security Posture Compliance Auditor
- [ ] [P3-T4] Gemini Zero-Trust HR Onboarding Copilot
- [ ] [P3-T5] FastAPI Web Dashboard & REST Endpoints
- [ ] **Checkpoint: Phase 3 Core Services Checkpoint** (All service unit tests pass offline)

### Phase 4: Custom Google Workspace Admin MCP Server
- [ ] [P4-T1] Standalone Stdio Workspace MCP Server Implementation
- [ ] [P4-T2] Antigravity Workspace MCP Configuration & Granular Tool Permissions
- [ ] **Checkpoint: Phase 4 MCP Server Checkpoint** (MCP stdio handshake & tools verified)

### Phase 5: Subagent Audits, Hardening & Cloud Run Packaging
- [ ] [P5-T1] Persona Definition Prompts for Subagents
- [ ] [P5-T2] Subagent Audits (`security-auditor` & `code-reviewer`)
- [ ] [P5-T3] Containerization & Google Cloud Run Production Configuration
- [ ] [P5-T4] Sunday Presentation Deck & Live Demo Script
- [ ] **Final Checkpoint: Complete System Validation** (100% test pass rate, >= 90% coverage)

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| AI Studio Quota Limits | Medium | Local deterministic mock fallback in Gemini client for tests and offline demos |
| Raw PII Leakage | High | Pre-filtering regex tokenization, strict `AGENTS.md` rules, SQLite SHA-256 only |
| Missing Enterprise Workspace Domain | High | `MockAdminAdapter` with 100% parity against Admin SDK Directory contracts |
| Deployment Compatibility | Low | Multi-stage Dockerfile meeting Cloud Run runtime contract (`PORT=8080`, `/health`) |

## Open Questions
- Fallback model preference (`gemini-2.5-flash` primary; support `gemini-1.5-flash` / `gemini-2.0-flash` fallback)?
- Custom styling or corporate branding for the live demo dashboard?
