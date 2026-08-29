"""CSV upload, validation, and import into SQLite."""

import csv
import io
import uuid
from datetime import datetime, timezone

import aiosqlite


PAYROLL_REGISTER_COLUMNS = {
    "employee_id",
    "full_name",
    "nin",
    "bvn",
    "bank_account",
    "bank_code",
    "phone",
    "address",
    "next_of_kin",
    "department",
    "position",
    "date_hired",
    "monthly_salary",
    "status",
}

HR_REGISTER_COLUMNS = {"employee_id", "full_name", "department", "position", "status"}

ATTENDANCE_COLUMNS = {"employee_id", "date", "clock_in", "clock_out"}


def detect_category(headers: set[str]) -> str | None:
    """Detect CSV category based on column headers."""
    if "monthly_salary" in headers and "employee_id" in headers:
        return "payroll_register"
    if "clock_in" in headers and "employee_id" in headers:
        return "attendance"
    if (
        "department" in headers
        and "employee_id" in headers
        and "monthly_salary" not in headers
    ):
        return "hr_register"
    return None


async def import_csv(
    db: aiosqlite.Connection,
    file_content: bytes,
    filename: str,
    uploaded_by: str = "demo-user",
) -> dict:
    """Parse and import a CSV file into the database."""
    text = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return {"success": False, "error": "CSV file is empty", "rows": 0}

    headers = set(rows[0].keys())
    category = detect_category(headers)

    if not category:
        return {"success": False, "error": "Unrecognized CSV format", "rows": 0}

    # Track ingestion
    file_id = f"FILE-{uuid.uuid4().hex[:8].upper()}"
    await db.execute(
        """INSERT INTO ingested_files (filename, file_type, category, scan_status, row_count, uploaded_at, uploaded_by)
           VALUES (?, 'csv', ?, 'clean', ?, ?, ?)""",
        (
            filename,
            category,
            len(rows),
            datetime.now(timezone.utc).isoformat(),
            uploaded_by,
        ),
    )

    imported = 0

    if category == "payroll_register":
        for row in rows:
            eid = row.get("employee_id", "").strip()
            if not eid:
                continue
            identity_verified = row.get("identity_verified", "false")
            if isinstance(identity_verified, str):
                identity_verified = 1 if identity_verified.lower() == "true" else 0
            await db.execute(
                """INSERT OR REPLACE INTO employees
                   (employee_id, full_name, nin, bvn, bank_account, bank_code,
                    phone, address, next_of_kin, department, position,
                    date_hired, date_terminated, monthly_salary, status,
                    created_by, approved_by, ncvs_credential_number,
                    identity_verified, verification_date, verification_source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    eid,
                    row.get("full_name", ""),
                    row.get("nin"),
                    row.get("bvn"),
                    row.get("bank_account"),
                    row.get("bank_code"),
                    row.get("phone"),
                    row.get("address"),
                    row.get("next_of_kin"),
                    row.get("department", ""),
                    row.get("position", ""),
                    row.get("date_hired"),
                    row.get("date_terminated") or None,
                    float(row.get("monthly_salary", 0)),
                    row.get("status", "active"),
                    row.get("created_by", uploaded_by),
                    row.get("approved_by"),
                    row.get("ncvs_credential_number") or None,
                    identity_verified,
                    row.get("verification_date") or None,
                    row.get("verification_source") or None,
                ),
            )
            imported += 1

    elif category == "hr_register":
        # HR register is used for cross-check — we don't insert into employees
        # Just log the ingestion; the rule engine reads the CSV directly
        imported = len(rows)

    elif category == "attendance":
        imported = len(rows)

    await db.commit()

    return {
        "success": True,
        "category": category,
        "rows": imported,
        "filename": filename,
        "file_id": file_id,
    }
