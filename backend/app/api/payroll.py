"""Payroll API — trigger 5-layer scan."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.database import get_db
from app.models.schemas import AuditVerdict, ScanResponse
from app.agents.orchestrator import get_auditor
from app.audit.audit_store import append_event

router = APIRouter()


@router.post("/payroll/scan")
async def scan_payroll(run_id: str | None = None) -> ScanResponse:
    db = await get_db()

    # Get or create run_id
    if not run_id:
        # Use existing run
        cursor = await db.execute(
            "SELECT run_id FROM payroll_runs ORDER BY run_date DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        run_id = row["run_id"] if row else f"RUN-{uuid.uuid4().hex[:8].upper()}"

    # Load all employees
    cursor = await db.execute("SELECT * FROM employees WHERE status = 'active'")
    rows = await cursor.fetchall()
    employees = [dict(r) for r in rows]

    # Run auditor
    auditor = get_auditor()
    result = await auditor.run({"employees": employees, "run_id": run_id})

    # Store anomalies
    for anomaly_data in result["anomalies"]:
        findings_json = json.dumps(anomaly_data["findings"], default=str)
        await db.execute(
            """INSERT OR REPLACE INTO anomalies
               (anomaly_id, employee_id, employee_name, run_id, findings_json,
                total_score, verdict, monthly_exposure, explanation, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                anomaly_data["anomaly_id"],
                anomaly_data["employee_id"],
                anomaly_data["employee_name"],
                anomaly_data.get("run_id"),
                findings_json,
                anomaly_data["total_score"],
                anomaly_data["verdict"]
                if isinstance(anomaly_data["verdict"], str)
                else anomaly_data["verdict"].value,
                float(anomaly_data["monthly_exposure"]),
                anomaly_data["explanation"],
                anomaly_data["status"],
            ),
        )

    # Update payroll run status
    await db.execute(
        "UPDATE payroll_runs SET status = 'scanned', scanned_by = 'auditor', scan_result = ? WHERE run_id = ?",
        ("anomalies_found" if result["anomalies"] else "clean", run_id),
    )
    await db.commit()

    # Audit log
    verdict = (
        AuditVerdict.FLAGGED if result["anomalies_found"] > 0 else AuditVerdict.SEALED
    )
    await append_event(
        db,
        "scan",
        "Auditor Agent",
        f"Payroll scan completed for {run_id}: {result['anomalies_found']} anomalies found",
        target=run_id,
        verdict=verdict,
        payload={"run_id": run_id, "anomalies_found": result["anomalies_found"]},
    )

    return ScanResponse(
        run_id=run_id,
        anomalies_found=result["anomalies_found"],
        anomalies=result["anomalies"],
    )
