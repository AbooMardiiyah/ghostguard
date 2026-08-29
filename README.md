# GhostGuard

**Payroll fraud is stopped before the money moves, not found in next year's audit.**

GhostGuard sits between your HR and finance systems and the payment file. It scores every employee, blocks what fails, and hands a human the evidence to decide. Built for the 10Alytics Business AI BuildFest 2026 (Track 5: AI Automation & Integrations, Case Study 4: AI Operations Assistant).

## The Problem

Ghost workers are not a solved problem. Fifty years of payroll reform, biometric enrolment and centralised systems have not removed them. They are still being found today, at scale, in the institutions that already deployed the fix.

| Year | What happened |
|------|--------------|
| 1975 | Murtala Mohammed's audit removes thousands of ghost names from federal payroll |
| 2007 | Nigeria deploys IPPIS to centralise payroll. 65,000 ghost workers later removed |
| 2014 | Kenya's biometric registration removes 12,000 ghost workers in a single exercise |
| 2026 | Kenya's audit still finds 15,994 payroll discrepancies across 72 institutions |
| 2026 | ICPC finds 908 ghost workers across 50 Nigerian agencies. 570 in the Police alone |

The question is not whether ghost workers exist. It is whether you find them before or after the money leaves.

## The Cost

Documented annual ghost-worker payroll exposure across five places alone totals roughly 72 billion naira a year. Each figure is from a published audit or investigation, not an estimate.

- **Federal payroll (23,000 multi-salary):** 27.5 billion naira
- **Bayelsa State:** 24.0 billion naira
- **Osun State:** 13.7 billion naira
- **Adamawa State:** 3.6 billion naira
- **Kano State:** 3.4 billion naira

IPPIS has saved 185 billion naira to date by removing 65,000 ghost workers from federal payroll. The ICPC recovered 942 million naira in July 2026 alone from 908 ghost workers across 50 agencies.

## Why It Persists

Global occupational-fraud data (ACFE, 2,402 cases across 143 countries) explains why detection is worth so much more than recovery:

- **12 months** median time to detection. A payroll scheme runs a full year before anyone notices.
- **43%** found by tip-off, not by controls or audit.
- **27x** cost of waiting. Median loss grows from $40,000 under six months to $1.1 million past five years.

Every naira of ghost salary is paid out roughly twelve times before it is questioned, and recovering it afterwards needs investigators, lawyers and years. Moving detection to before the payment run removes the loss instead of chasing it.

## How It Works

### Four AI Agents

| Agent | Role |
|-------|------|
| **Verifier** | Checks identity against national databases (NIN, BVN, NUBAN) through Dojah |
| **Auditor** | Runs the 5-layer detection engine across the entire register, scoring every employee |
| **Guardian** | Screens approval messages and voice notes for impersonation, pressure and injection |
| **Red Team** | Attacks our own defenses with 5 adversarial scenarios, every run |

The engine is deterministic. Detection is rules and arithmetic, so a verdict is reproducible and explainable in court. The language model writes the explanation; it never decides the outcome, and the system runs without it.

### 5-Layer Detection Engine

| Layer | What it checks | Caught in our test run |
|-------|---------------|----------------------|
| Identity | NIN and BVN resolve to this person; NCVS credential present and current | Two staff with no verification on file |
| Shared Attributes | Bank account, BVN, phone, address or next-of-kin repeated across staff | Two pairs sharing an account and an address |
| Existence | Attendance records, leave history, clock-in patterns | Two staff with zero attendance in six months |
| Process | Separation of duties, bank changes near payday, salary changes without approval | One record created and approved by the same user |
| Cross-check | Payroll against HR register, against the leavers list, headcount reconciliation | One terminated employee still being paid |

Scoring: findings add points. Under 30 clears. 30 to 69 is flagged for review. 70 and above is blocked. Four signals hard-block regardless of score: identity mismatch, self-approval, and a terminated employee still on payroll.

### Active Defense

GhostGuard does not just detect. It actively defends against:

- **Ghost onboarding attempts** blocking fake employees whose NIN resolves to a different identity
- **Voice/email impersonation** screening transcribed messages for CEO fraud, urgency pressure, secrecy instructions
- **Receipt tampering** analyzing images for EXIF editing markers, perceptual hash duplicates, VAT math errors
- **Red team testing** running 5 scripted adversarial attacks against all defenses simultaneously. Currently caught 5 of 5.

### Workflow

**Collect** (Odoo ERP, CSV upload, or direct onboarding) > **Detect** (5 layers score every employee, anomalies ranked by exposure) > **Decide** (a human auditor blocks, explains, or requests more information) > **Act** (payment blocked, notification sent, report generated and emailed) > **Seal** (every step written to a hash-chained, append-only audit trail)

Nothing is paid or blocked automatically. The system recommends. A named auditor decides, and the decision is logged with their name and note.

## Proof

Sterling Distributors, August 2026 payroll. Total run of 11,480,000 naira across 40 staff. Scan completes in seconds.

| Employee | Verdict | Score | Exposure | Finding |
|----------|---------|-------|----------|---------|
| Adaeze Okafor | BLOCK | 100 | 200,000 | Shares a bank account, no attendance, unverified identity |
| Musa Ibrahim | BLOCK | 100 | 220,000 | Terminated in April. Still on the August payroll |
| Tunde Bakare | BLOCK | 70 | 300,000 | Created and approved his own record |
| Chinedu Okafor | FLAG | 60 | 400,000 | Shares a bank account with another employee |
| Yusuf & Fatima Bello | FLAG | 35 | 430,000 | Share an address. Siblings, resolved as explained |

**7 anomalies** out of 40 employees. **3 blocked** on hard-block signals. **4 flagged** for human review. **15.2% of payroll at risk** (1.75 million naira this month).

### The Return

Year one: 7.92 million naira avoided. That is the cumulative loss from the three hard-blocked ghost salaries (720,000 naira a month) over twelve months. Without GhostGuard, the ACFE median of twelve months to discovery applies. With GhostGuard, the scan runs before the payment file is released.

Conservative basis: only the three hard-blocked salaries are counted. The four flagged cases (a further 1.03 million naira a month) are excluded pending human review.

## Security

This system holds national identity numbers, bank details and salaries for every employee. That shaped the architecture before any feature was written.

- **Tamper-evident by construction.** Every event is SHA-256 chained to the one before it. Database triggers reject UPDATE and DELETE on the audit table outright, so the trail is append-only at the storage layer, not by convention.
- **Identifiers are never stored in the clear.** NIN, BVN and account numbers are HMAC-hashed for comparison and shown as last-four. Matching two employees to the same account never requires reading either account number.
- **The security path has no model in it.** Injection, impersonation and pressure screening is deterministic pattern matching. A prompt cannot talk its way past a regular expression.
- **We attack it ourselves, every run.** Five adversarial scenarios run against live defenses. Currently caught 5 of 5.
- **No credentials in source.** All keys loaded from environment. Uploads are scanned and validated before parsing.

## Integrations

Real systems, not mocked endpoints.

| System | Purpose | Detail | Protocol |
|--------|---------|--------|----------|
| **Dojah** | Identity verification | NIN, BVN and NUBAN checked against national databases | REST, live sandbox |
| **Odoo ERP** | Employee and attendance data | Live instance at mazex.odoo.com, polled and reconciled | JSON-RPC, live |
| **Gemini 2.0 Flash** | Explanations and summaries | Turns findings into plain English for the auditor | REST, live |
| **Together AI** | Model fallback | Llama 3.3 70B takes over if Gemini fails; rules run without either | REST, live |
| **SMTP** | Scheduled notification | Scan summary and sealed PDF report delivered on a schedule | SMTP over TLS |
| **CSV import** | The spreadsheet reality | Payroll, HR register and attendance uploaded directly | Validated upload |

Three independent data sources feed one register. The fallback chain means a failed integration degrades the explanation, never the detection.

## Automation

- Configurable scan schedule: daily, weekly, monthly, or custom intervals
- Email notifications on every scan completion (summary or full report with PDF attachment)
- LLM-generated executive summaries in reports
- Anomaly export as CSV, Excel, or email directly from the dashboard

## Why This One

**1. It runs before the payment, not after the audit.** Every comparable control operates on money already gone. The ACFE median for discovery is twelve months. GhostGuard scores the register while the payment file is still a draft.

**2. A verdict you can defend in a tribunal.** The engine is deterministic, so the same register always produces the same score, and every point is traceable to a named rule and a piece of evidence. The model writes prose; it never decides. Nobody loses a salary because a model had an opinion.

**3. The evidence survives the person who made it.** Findings are worthless if the accused can edit them. The trail is SHA-256 chained and the database itself refuses updates and deletes, so tampering breaks the chain visibly and the sealed packet exports as evidence.

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.12, FastAPI, SQLite (aiosqlite), ReportLab |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| AI Models | Google Gemini 2.0 Flash, Meta Llama 3.3 70B (via Together AI) |
| External APIs | Dojah (identity), Odoo (ERP), SMTP (notifications) |
| Infrastructure | Docker, Nginx, Docker Compose |

## Getting Started

### Prerequisites

- Docker and Docker Compose (for containerized deployment)
- OR Node.js 20+ and Python 3.12+ (for local development)

### Environment Setup

```bash
cp backend/.env.example backend/.env
```

Required variables:
- `IDENTITY_PROVIDER` - Set to `dojah` for live identity verification or `mock` for offline demo
- `LLM_PROVIDER` - Set to `gemini`, `together`, `openai`, or `mock`
- API keys for your chosen providers

Optional:
- SMTP credentials for email notifications
- Odoo credentials for ERP integration

### Run with Docker

```bash
docker compose build
docker compose up -d
docker compose logs -f
docker compose down
```

The application will be available at `http://localhost` (port 80).

### Run Locally

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in a separate terminal)
cd frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

### Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

## Project Structure

```
ghostguard/
  backend/
    app/
      agents/          # Verifier, Auditor, Guardian, Red Team
      api/             # REST API endpoints
      audit/           # Hash-chained audit trail, PDF generation, seal
      engine/          # 5-layer rule engine, PII masker, receipt engine
      integrations/    # Dojah, Odoo, CSV connectors
      models/          # Database schema, Pydantic models
      security/        # File scanner, input validator
      services/        # Email and report services
    tests/
  frontend/
    src/
      sections/        # CommandCenter, LiveDefense, Integrations, Scheduler, AuditTrail
      components/      # AgentCard, AnomalyTable, VerdictBadge, Shell, etc.
      lib/             # API client, types, utilities
  docker-compose.yml
  Makefile
```

*Sources: Daily Trust; AllAfrica; ICPC (July 2026); The Star (Kenya, 2026); ACFE, Occupational Fraud 2026: A Report to the Nations.*
