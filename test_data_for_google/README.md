# BuenaGuard AI: Live Demonstration & Testing Dataset

This directory contains realistic enterprise testing data designed specifically to demonstrate **BuenaGuard AI's** core capabilities in live Google Workspace environments:

1. **Google Sheets HR Onboarding Copilot** (Least-privilege OU assignment, S/MIME encryption, 2SV enforcement)
2. **Google Drive GDPR / DSGVO DLP Scanner** (German IBANs, Steuer-ID, passports, salaries, SEPA transfers)

---

## 1. How to Populate Google Sheets (`Sheet 1`)

File: [`google_sheets_onboarding_candidates.csv`](file:///D:/buenaai/test_data_for_google/google_sheets_onboarding_candidates.csv)

### Option A: Copy & Paste into your existing `Sheet 1`
Open your `Sheet 1` in Google Sheets and paste these rows:

```text
fullName	email	department	jobTitle	manager	location
Hannah Weber	hannah.weber@buenacloud.de	Finance	Chief Financial Officer (CFO)	Cezary Augustynowicz	Munich Germany
Maximilian Bauer	m.bauer@buenacloud.de	Finance	Senior Payroll & Tax Specialist	Hannah Weber	Frankfurt Germany
Lukas Schmidt	l.schmidt@buenacloud.de	Engineering	Lead Cloud Infrastructure Architect	CTO	Berlin Germany
Sophie Becker	s.becker@buenacloud.de	Engineering	Senior Backend Engineer	Lukas Schmidt	Hamburg Germany
Carlos Mendez	c.mendez@buenacloud.de	Contractors	External Penetration Tester	Lukas Schmidt	Madrid Spain
Elena Rostova	e.rostova@buenacloud.de	Legal	Corporate Compliance & Data Privacy Officer	Hannah Weber	Munich Germany
```

### Option B: Import CSV File
1. In Google Sheets, click **Fichier** > **Importer** (*File* > *Import*).
2. Upload `google_sheets_onboarding_candidates.csv`.
3. Select **Insérer de nouvelles feuilles** or **Remplacer la feuille actuelle**.

---

## 2. How to Upload Files to Google Drive

Directory: [`test_data_for_google/drive_dlp_files/`](file:///D:/buenaai/test_data_for_google/drive_dlp_files/)

Simply drag-and-drop any of these files into your [Google Drive](https://drive.google.com):

| File Name | Test Scenario | Expected BuenaGuard AI Classification |
| :--- | :--- | :--- |
| `01_CRITICAL_Executive_Payroll_Q4_2026.csv` | Executive salaries, German IBANs, Steuer-IDs | 🔴 **CRITICAL / HIGH RISK** (Art. 6 & 32 DSGVO, PII Redaction) |
| `02_HIGH_Arbeitsvertrag_Senior_Ingenieur.txt` | German employment contract with passport & bank details | 🔴 **HIGH RISK** (Mandatory redaction, move to restricted OU) |
| `03_HIGH_SEPA_B2B_Payment_Instructions.txt` | Multi-country EU SEPA wire transfers (DE, FR, AT IBANs) | 🟠 **HIGH RISK** (Financial banking PII) |
| `04_MEDIUM_External_Contractor_Agreement.txt` | External contractor rate agreement (Spanish IBAN) | 🟡 **MEDIUM RISK** (Zero-trust /Contractors OU assignment) |
| `05_LOW_Clean_Sprint_Planning_Notes.txt` | Engineering architecture notes with zero PII | 🟢 **LOW RISK / COMPLIANT** (Clean pass, zero false positives) |

---

## 3. Immediate Live Testing

Once uploaded:
1. Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.
2. In the **Live Google Drive Repository** table, click **Scan DLP** next to any uploaded file.
3. In the **Zero-Trust HR Onboarding Copilot**, pick any candidate from the dropdown to see Gemini 3.8 Flash evaluate and provision their account in real time!
