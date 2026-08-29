# GhostGuard

**Agentic Payroll Integrity System**

GhostGuard monitors payroll operations, detects ghost workers and fraudulent payments, and blocks them before money leaves the account. Built for the 10Alytics Business AI BuildFest 2026 (Track 5: AI Automation & Integrations, Case Study 4: AI Operations Assistant).

## The Problem

Ghost workers are employees who exist on paper but not in reality. They cost organizations billions in fraudulent salary payments every year. In July 2026, Nigeria's ICPC investigated 50 government agencies and found 908 ghost workers, recovering 942 million naira.

Most organizations discover payroll fraud months after payments are made. Manual audits are slow, inconsistent, and easy to circumvent.

GhostGuard catches these anomalies before payments go out, not after.

## How It Works

### Four AI Agents

| Agent | Role |
|-------|------|
| **Verifier** | Checks employee identities against national databases (NIN, BVN, NUBAN) via Dojah API |
| **Auditor** | Runs a 5-layer detection engine across the entire payroll register |
| **Guardian** | Screens communications for social engineering, impersonation, and injection attacks |
| **Red Team** | Tests all defenses with 5 adversarial attack scenarios simultaneously |

### 5-Layer Detection Engine

| Layer | What It Checks | Example |
|-------|---------------|---------|
| Identity | NIN/BVN verification, NCVS compliance | Employee NIN resolves to a different person |
| Shared Attributes | Same bank account, phone, or address across employees | Two employees paid into the same account |
| Existence | Attendance records, physical presence | Employee has zero attendance entries |
| Process | Self-approval, authorization controls | Employee created and approved their own record |
| Cross-Check | HR register vs payroll, leaver status | Terminated employee still receiving salary |

Each finding adds risk points. Below 30 = Clear. 30-69 = Flagged for review. 70+ = Blocked.

Every anomaly requires human approval before any payment action is taken. Auditors can block the payment, mark it as explained, or request more information.

### Active Defense

Beyond detection, GhostGuard actively defends against:

- **Voice/email impersonation** screening for CEO fraud, urgency pressure, and secrecy instructions
- **Receipt forensics** analyzing images for EXIF editing markers, perceptual hash duplicates, and VAT math errors
- **Ghost onboarding attempts** blocking fake employees whose identity verification fails
- **Red team testing** running 5 scripted adversarial attacks against all defenses

### Tamper-Proof Audit Trail

Every action in GhostGuard is recorded in a SHA-256 hash-chained audit trail. Every scan, every human decision, every integration event. If anyone tampers with a single record, the chain breaks and the system flags it immediately. The entire trail can be exported as a sealed PDF packet.

## Integrations

| System | Purpose | Protocol |
|--------|---------|----------|
| **Dojah** | NIN, BVN, and NUBAN verification against national identity databases | REST API (sandbox) |
| **Odoo ERP** | Employee records and attendance data | JSON-RPC |
| **Gemini 2.0 Flash** | Anomaly explanations, executive report summaries | REST API |
| **Together AI (Llama 3.3 70B)** | LLM fallback for reliability | REST API |
| **SMTP Email** | Automated scan notifications with PDF report attachments | SMTP/TLS |
| **CSV Import** | Payroll register, HR register, attendance log upload | File upload |

The LLM layer uses a fallback chain: Gemini 2.0 Flash, then Together AI Llama 3.3 70B, then a deterministic mock. The detection engine works fully without any LLM; AI enhances explanations but is not required for core detection.

## Automation

- Configurable scan schedule: daily, weekly, monthly, or custom intervals
- Email notifications on every scan completion (summary or full report with PDF attachment)
- LLM-generated executive summaries in reports
- Anomaly export as CSV, Excel, or email directly from the dashboard

## Security

- PII masking with HMAC hashing for sensitive fields (NIN, BVN, bank accounts)
- Input validation and file scanning on all uploads
- Regex-based injection and impersonation detection
- SHA-256 hash-chained audit trail (append-only, tamper-evident)
- No API keys hardcoded; all credentials loaded from environment variables

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

Copy the example environment file and fill in your credentials:

```bash
cp backend/.env.example backend/.env
```

Required variables:
- `IDENTITY_PROVIDER` - Set to `dojah` for live identity verification or `mock` for offline demo
- `LLM_PROVIDER` - Set to `gemini`, `together`, `openai`, or `mock`
- API keys for your chosen providers (DOJAH_APP_ID, DOJAH_SECRET_KEY, GEMINI_API_KEY, etc.)

Optional:
- SMTP credentials for email notifications
- Odoo credentials for ERP integration

### Run with Docker

```bash
# Build and start
docker compose build
docker compose up -d

# View logs
docker compose logs -f

# Stop
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

Backend runs on `http://localhost:8000`, frontend on `http://localhost:5173`.

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
      agents/          # Verifier, Auditor, Guardian, Red Team agents
      api/             # REST API endpoints
      audit/           # Hash-chained audit trail, PDF generation, seal
      engine/          # 5-layer rule engine, PII masker, receipt engine
      integrations/    # Dojah, Odoo, CSV connectors
      models/          # Database schema, Pydantic models
      security/        # File scanner, input validator
      services/        # Email and report services
      config.py        # Application configuration
      main.py          # FastAPI app entry point
      seed.py          # Sample data seeder
    tests/             # Backend test suite
  frontend/
    src/
      sections/        # Page-level components (CommandCenter, LiveDefense, etc.)
      components/      # Reusable UI components
      lib/             # API client, types, utilities
  docker-compose.yml
  Makefile
```

## Business Impact

For a company like Sterling Distributors with 40 employees, GhostGuard detected:

- 1.54 million naira per month in suspicious payments
- 3 employees flagged for immediate payment block
- 4 additional cases requiring human review
- 1 terminated employee still receiving salary

At scale, the ICPC's investigation of just 50 agencies recovered 942 million naira. GhostGuard automates this detection in seconds rather than months.

## Author

**Hamzat Tiamiyu**
hamzattiamiyu@gmail.com

Built solo for the 10Alytics Business AI BuildFest 2026.
