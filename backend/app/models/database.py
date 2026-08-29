"""SQLite database initialization and access."""

import aiosqlite
from pathlib import Path
from app.config import settings

_db: aiosqlite.Connection | None = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    nin TEXT,
    bvn TEXT,
    bank_account TEXT,
    bank_code TEXT,
    phone TEXT,
    address TEXT,
    next_of_kin TEXT,
    department TEXT DEFAULT '',
    position TEXT DEFAULT '',
    date_hired TEXT,
    date_terminated TEXT,
    monthly_salary REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_by TEXT DEFAULT '',
    approved_by TEXT,
    ncvs_credential_number TEXT,
    identity_verified INTEGER DEFAULT 0,
    verification_date TEXT,
    verification_source TEXT
);

CREATE TABLE IF NOT EXISTS payroll_runs (
    run_id TEXT PRIMARY KEY,
    period TEXT NOT NULL,
    run_date TEXT NOT NULL,
    total_headcount INTEGER DEFAULT 0,
    total_amount REAL DEFAULT 0,
    status TEXT DEFAULT 'draft',
    scanned_by TEXT,
    scan_result TEXT
);

CREATE TABLE IF NOT EXISTS payroll_entries (
    entry_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    amount REAL DEFAULT 0,
    bank_account TEXT,
    bank_code TEXT,
    allowances REAL DEFAULT 0,
    deductions REAL DEFAULT 0,
    FOREIGN KEY (run_id) REFERENCES payroll_runs(run_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS leavers (
    employee_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    department TEXT,
    date_terminated TEXT NOT NULL,
    reason TEXT DEFAULT 'resignation'
);

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    employee_name TEXT NOT NULL,
    run_id TEXT,
    findings_json TEXT DEFAULT '[]',
    total_score INTEGER DEFAULT 0,
    verdict TEXT DEFAULT 'CLEAR',
    monthly_exposure REAL DEFAULT 0,
    explanation TEXT DEFAULT '',
    status TEXT DEFAULT 'open',
    decided_by TEXT,
    decided_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    verdict TEXT,
    detail TEXT,
    payload_json TEXT,
    evidence_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS receipt_hashes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id TEXT UNIQUE NOT NULL,
    phash TEXT NOT NULL,
    employee_id TEXT,
    expense_date TEXT,
    amount REAL,
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingested_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    category TEXT,
    scan_status TEXT DEFAULT 'pending',
    row_count INTEGER,
    uploaded_at TEXT NOT NULL,
    uploaded_by TEXT
);

-- Append-only triggers for audit trail
CREATE TRIGGER IF NOT EXISTS audit_no_update
BEFORE UPDATE ON audit_trail
BEGIN
    SELECT RAISE(ABORT, 'Audit trail is append-only');
END;

CREATE TRIGGER IF NOT EXISTS audit_no_delete
BEFORE DELETE ON audit_trail
BEGIN
    SELECT RAISE(ABORT, 'Audit trail is append-only');
END;
"""


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        db_path = Path(settings.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _db = await aiosqlite.connect(str(db_path))
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        await _db.executescript(SCHEMA_SQL)
        await _db.commit()
    return _db


async def close_db():
    global _db
    if _db is not None:
        await _db.close()
        _db = None
