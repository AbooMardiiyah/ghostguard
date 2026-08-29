"""Pydantic schemas for GhostGuard data model."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# --- Enums ---


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


class PayrollRunStatus(str, Enum):
    DRAFT = "draft"
    SCANNED = "scanned"
    APPROVED = "approved"
    PAID = "paid"


class Verdict(str, Enum):
    CLEAR = "CLEAR"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


class AuditVerdict(str, Enum):
    BLOCKED = "BLOCKED"
    FLAGGED = "FLAGGED"
    SEALED = "SEALED"
    ESCALATED = "ESCALATED"
    INFO = "INFO"


class AnomalyStatus(str, Enum):
    OPEN = "open"
    EXPLAINED = "explained"
    ESCALATED = "escalated"
    BLOCKED = "blocked"


class AgentState(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    ARMED = "armed"
    ERROR = "error"


LayerName = Literal[
    "identity", "shared_attributes", "existence", "process", "cross_check"
]


# --- Core Schemas ---


class Employee(BaseModel):
    employee_id: str
    full_name: str
    nin: str | None = None
    bvn: str | None = None
    bank_account: str | None = None
    bank_code: str | None = None
    phone: str | None = None
    address: str | None = None
    next_of_kin: str | None = None
    department: str = ""
    position: str = ""
    date_hired: date | None = None
    date_terminated: date | None = None
    monthly_salary: Decimal = Decimal("0")
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    created_by: str = ""
    approved_by: str | None = None
    ncvs_credential_number: str | None = None
    identity_verified: bool = False
    verification_date: datetime | None = None
    verification_source: str | None = None


class PayrollRun(BaseModel):
    run_id: str
    period: str  # e.g. "2026-08"
    run_date: datetime
    total_headcount: int = 0
    total_amount: Decimal = Decimal("0")
    status: PayrollRunStatus = PayrollRunStatus.DRAFT
    scanned_by: str | None = None
    scan_result: str | None = None


class PayrollEntry(BaseModel):
    entry_id: str
    run_id: str
    employee_id: str
    amount: Decimal = Decimal("0")
    bank_account: str | None = None
    bank_code: str | None = None
    allowances: Decimal = Decimal("0")
    deductions: Decimal = Decimal("0")


class LayerFinding(BaseModel):
    layer: LayerName
    signal: str
    description: str
    evidence: dict = Field(default_factory=dict)
    points: int = 0
    source: str = "rule_engine"


class Anomaly(BaseModel):
    anomaly_id: str
    employee_id: str
    employee_name: str
    run_id: str | None = None
    findings: list[LayerFinding] = Field(default_factory=list)
    total_score: int = 0
    verdict: Verdict = Verdict.CLEAR
    monthly_exposure: Decimal = Decimal("0")
    explanation: str = ""
    status: AnomalyStatus = AnomalyStatus.OPEN
    decided_by: str | None = None
    decided_at: datetime | None = None


class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: str
    actor: str
    action: str
    target: str | None = None
    verdict: AuditVerdict | None = None
    detail: str | None = None
    payload_json: str | None = None
    evidence_hash: str = ""
    chain_hash: str = ""


class AgentStatus(BaseModel):
    agent_id: str
    name: str
    state: AgentState = AgentState.IDLE
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_run: datetime | None = None
    summary_metric: str | None = None


# --- API Response Models ---


class DashboardResponse(BaseModel):
    kpis: dict
    anomalies: list[Anomaly]
    agents: list[AgentStatus]


class ScanResponse(BaseModel):
    run_id: str
    anomalies_found: int
    anomalies: list[Anomaly]


class VerifyResponse(BaseModel):
    employee_id: str
    verified: bool
    findings: list[LayerFinding] = Field(default_factory=list)
    citations: dict = Field(default_factory=dict)


class DefenseResponse(BaseModel):
    simulation: str
    steps: list[dict] = Field(default_factory=list)
    verdict: str = ""
    details: dict = Field(default_factory=dict)


class RedTeamResponse(BaseModel):
    attacks: list[dict] = Field(default_factory=list)
    all_caught: bool = False
    audit_sealed: bool = False


class ApprovalRequest(BaseModel):
    anomaly_id: str
    decision: Literal["block", "explain", "request_info"]
    actor: str = "demo-user"
    note: str = ""


class AuditChainStatus(BaseModel):
    chain_valid: bool
    events_count: int
    latest_hash: str = ""
