"""5-Layer Deterministic Rule Engine — the heart of GhostGuard.

Scores employees across 5 layers: Identity, Shared Attributes, Existence,
Process, and Cross-Check. Entirely deterministic — no LLM needed.
"""

from datetime import date, timedelta
from decimal import Decimal

from app.models.schemas import LayerFinding, Verdict

# --- Rule Definitions ---

IDENTITY_RULES = {
    "nin_name_mismatch": {
        "points": 50,
        "hard_block": True,
        "desc": "NIN verifies to a different name",
    },
    "bvn_name_mismatch": {
        "points": 50,
        "hard_block": True,
        "desc": "BVN verifies to a different name",
    },
    "unverified_identity": {"points": 30, "desc": "No identity verification on file"},
    "no_ncvs_credential": {"points": 15, "desc": "No NCVS credential number on file"},
    "expired_verification": {
        "points": 20,
        "desc": "Identity verification older than 12 months",
    },
}

SHARED_ATTRIBUTE_RULES = {
    "shared_bank_account": {
        "points": 40,
        "desc": "Bank account shared with another employee",
    },
    "shared_bvn": {"points": 45, "desc": "BVN shared with another employee"},
    "shared_phone": {"points": 25, "desc": "Phone number shared with another employee"},
    "shared_address": {"points": 15, "desc": "Address shared with another employee"},
    "shared_next_of_kin": {
        "points": 10,
        "desc": "Next-of-kin shared with another employee",
    },
}

EXISTENCE_RULES = {
    "no_attendance_6m": {"points": 35, "desc": "No attendance records in 6+ months"},
    "never_took_leave": {"points": 20, "desc": "Never requested leave since hire date"},
    "no_performance_review": {"points": 15, "desc": "No performance review on record"},
    "identical_clockins": {
        "points": 25,
        "desc": "Suspiciously identical clock-in patterns",
    },
}

PROCESS_RULES = {
    "self_approved": {
        "points": 50,
        "hard_block": True,
        "desc": "Same user created and approved this record",
    },
    "bank_change_before_payday": {
        "points": 35,
        "desc": "Bank details changed within 5 days of payday",
    },
    "salary_change_no_approval": {
        "points": 40,
        "desc": "Salary changed with no approval trail",
    },
    "off_cycle_payment": {
        "points": 30,
        "desc": "Payment outside the regular payroll cycle",
    },
}

CROSS_CHECK_RULES = {
    "not_in_hr_register": {"points": 40, "desc": "On payroll but not in HR register"},
    "terminated_still_paid": {
        "points": 50,
        "hard_block": True,
        "desc": "Terminated employee still on payroll",
    },
    "duplicate_position": {"points": 30, "desc": "Duplicate position entry detected"},
    "headcount_mismatch": {
        "points": 25,
        "desc": "Payroll total does not match headcount",
    },
}

HARD_BLOCK_SIGNALS = {
    signal
    for rules in [
        IDENTITY_RULES,
        SHARED_ATTRIBUTE_RULES,
        EXISTENCE_RULES,
        PROCESS_RULES,
        CROSS_CHECK_RULES,
    ]
    for signal, rule in rules.items()
    if rule.get("hard_block")
}


def _make_finding(layer: str, signal: str, rules: dict, evidence: dict) -> LayerFinding:
    rule = rules[signal]
    return LayerFinding(
        layer=layer,
        signal=signal,
        description=rule["desc"],
        evidence=evidence,
        points=rule["points"],
        source="rule_engine",
    )


def check_identity(employee: dict) -> list[LayerFinding]:
    """Layer 1: Identity verification checks."""
    findings = []

    verified = employee.get("identity_verified")
    # Handle string "false"/"true" from CSV and integer 0/1 from SQLite
    if isinstance(verified, str):
        verified = verified.lower() not in ("false", "0", "")
    if not verified:
        findings.append(
            _make_finding(
                "identity",
                "unverified_identity",
                IDENTITY_RULES,
                {"employee_id": employee["employee_id"], "identity_verified": False},
            )
        )

    if not employee.get("ncvs_credential_number"):
        findings.append(
            _make_finding(
                "identity",
                "no_ncvs_credential",
                IDENTITY_RULES,
                {
                    "employee_id": employee["employee_id"],
                    "ncvs_credential_number": None,
                },
            )
        )

    if employee.get("verification_date"):
        ver_date = employee["verification_date"]
        if isinstance(ver_date, str):
            ver_date = date.fromisoformat(ver_date[:10])
        if (date.today() - ver_date).days > 365:
            findings.append(
                _make_finding(
                    "identity",
                    "expired_verification",
                    IDENTITY_RULES,
                    {
                        "employee_id": employee["employee_id"],
                        "verification_date": str(ver_date),
                    },
                )
            )

    return findings


def check_shared_attributes(
    employee: dict, all_employees: list[dict]
) -> list[LayerFinding]:
    """Layer 2: Detect shared bank accounts, BVN, phone, address, next-of-kin."""
    findings = []
    eid = employee["employee_id"]

    for other in all_employees:
        if other["employee_id"] == eid:
            continue

        # Shared bank account
        if (
            employee.get("bank_account")
            and other.get("bank_account")
            and employee["bank_account"] == other["bank_account"]
            and employee.get("bank_code") == other.get("bank_code")
        ):
            findings.append(
                _make_finding(
                    "shared_attributes",
                    "shared_bank_account",
                    SHARED_ATTRIBUTE_RULES,
                    {
                        "employee_id": eid,
                        "shared_with": other["employee_id"],
                        "bank_account_last4": employee["bank_account"][-4:]
                        if employee["bank_account"]
                        else "",
                    },
                )
            )
            break  # Only flag once per shared field

        # Shared BVN
        if employee.get("bvn") and other.get("bvn") and employee["bvn"] == other["bvn"]:
            findings.append(
                _make_finding(
                    "shared_attributes",
                    "shared_bvn",
                    SHARED_ATTRIBUTE_RULES,
                    {
                        "employee_id": eid,
                        "shared_with": other["employee_id"],
                    },
                )
            )
            break

    # Shared phone
    for other in all_employees:
        if other["employee_id"] == eid:
            continue
        if (
            employee.get("phone")
            and other.get("phone")
            and employee["phone"] == other["phone"]
        ):
            findings.append(
                _make_finding(
                    "shared_attributes",
                    "shared_phone",
                    SHARED_ATTRIBUTE_RULES,
                    {
                        "employee_id": eid,
                        "shared_with": other["employee_id"],
                    },
                )
            )
            break

    # Shared address
    for other in all_employees:
        if other["employee_id"] == eid:
            continue
        if (
            employee.get("address")
            and other.get("address")
            and employee["address"].strip().lower() == other["address"].strip().lower()
        ):
            findings.append(
                _make_finding(
                    "shared_attributes",
                    "shared_address",
                    SHARED_ATTRIBUTE_RULES,
                    {
                        "employee_id": eid,
                        "shared_with": other["employee_id"],
                        "address_match": True,
                    },
                )
            )
            break

    # Shared next-of-kin
    for other in all_employees:
        if other["employee_id"] == eid:
            continue
        if (
            employee.get("next_of_kin")
            and other.get("next_of_kin")
            and employee["next_of_kin"].strip().lower()
            == other["next_of_kin"].strip().lower()
        ):
            findings.append(
                _make_finding(
                    "shared_attributes",
                    "shared_next_of_kin",
                    SHARED_ATTRIBUTE_RULES,
                    {
                        "employee_id": eid,
                        "shared_with": other["employee_id"],
                    },
                )
            )
            break

    return findings


def check_existence(
    employee: dict, attendance_records: list[dict]
) -> list[LayerFinding]:
    """Layer 3: Check for signs of non-existence (no attendance, no leave, etc.)."""
    findings = []
    eid = employee["employee_id"]

    # Filter attendance for this employee
    emp_attendance = [a for a in attendance_records if a.get("employee_id") == eid]

    if not emp_attendance:
        findings.append(
            _make_finding(
                "existence",
                "no_attendance_6m",
                EXISTENCE_RULES,
                {"employee_id": eid, "attendance_records": 0},
            )
        )

    return findings


def check_process(employee: dict) -> list[LayerFinding]:
    """Layer 4: Process integrity checks (SoD, suspicious changes)."""
    findings = []
    eid = employee["employee_id"]

    # Self-approved: same user created AND approved
    created_by = (employee.get("created_by") or "").strip().lower()
    approved_by = (employee.get("approved_by") or "").strip().lower()
    if created_by and approved_by and created_by == approved_by:
        findings.append(
            _make_finding(
                "process",
                "self_approved",
                PROCESS_RULES,
                {
                    "employee_id": eid,
                    "created_by": employee.get("created_by"),
                    "approved_by": employee.get("approved_by"),
                },
            )
        )

    return findings


def check_cross(
    employee: dict, hr_register_ids: set[str], leaver_ids: set[str]
) -> list[LayerFinding]:
    """Layer 5: Cross-reference payroll vs HR register vs leavers."""
    findings = []
    eid = employee["employee_id"]

    # On payroll but not in HR register
    if eid not in hr_register_ids:
        findings.append(
            _make_finding(
                "cross_check",
                "not_in_hr_register",
                CROSS_CHECK_RULES,
                {"employee_id": eid, "in_hr_register": False},
            )
        )

    # Terminated but still on payroll
    if eid in leaver_ids:
        findings.append(
            _make_finding(
                "cross_check",
                "terminated_still_paid",
                CROSS_CHECK_RULES,
                {"employee_id": eid, "in_leavers_list": True},
            )
        )

    return findings


def score_employee(
    employee: dict,
    all_employees: list[dict],
    attendance_records: list[dict],
    hr_register_ids: set[str],
    leaver_ids: set[str],
) -> list[LayerFinding]:
    """Run all 5 layers against a single employee. Returns list of findings."""
    findings = []
    findings.extend(check_identity(employee))
    findings.extend(check_shared_attributes(employee, all_employees))
    findings.extend(check_existence(employee, attendance_records))
    findings.extend(check_process(employee))
    findings.extend(check_cross(employee, hr_register_ids, leaver_ids))
    return findings


def compute_verdict(findings: list[LayerFinding]) -> tuple[int, Verdict]:
    """Compute total score and verdict from findings."""
    total = sum(f.points for f in findings)
    total = min(total, 100)

    # Hard rules override
    if any(f.signal in HARD_BLOCK_SIGNALS for f in findings):
        return total, Verdict.BLOCK

    if total >= 70:
        return total, Verdict.BLOCK
    elif total >= 30:
        return total, Verdict.FLAG
    else:
        return total, Verdict.CLEAR
