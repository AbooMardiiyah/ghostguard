"""Approvals API — human gate for anomaly decisions."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.database import get_db
from app.models.schemas import ApprovalRequest, AuditVerdict
from app.audit.audit_store import append_event

router = APIRouter()


@router.post("/approvals/decide")
async def decide_anomaly(req: ApprovalRequest):
    db = await get_db()

    # Look up the anomaly
    cursor = await db.execute(
        "SELECT * FROM anomalies WHERE anomaly_id = ?", (req.anomaly_id,)
    )
    row = await cursor.fetchone()
    if not row:
        return {"success": False, "error": "Anomaly not found"}

    # Map decision to status
    status_map = {
        "block": "blocked",
        "explain": "explained",
        "request_info": "escalated",
    }
    new_status = status_map.get(req.decision, "open")

    # Update anomaly — we can't update audit_trail, but anomalies table is fine
    await db.execute(
        """UPDATE anomalies SET status = ?, decided_by = ?, decided_at = ?
           WHERE anomaly_id = ?""",
        (new_status, req.actor, datetime.now(timezone.utc).isoformat(), req.anomaly_id),
    )
    await db.commit()

    # Audit log
    verdict_map = {
        "block": AuditVerdict.BLOCKED,
        "explain": AuditVerdict.SEALED,
        "request_info": AuditVerdict.ESCALATED,
    }
    await append_event(
        db,
        "approval",
        req.actor,
        f"Anomaly {req.anomaly_id} — decision: {req.decision}"
        + (f" — {req.note}" if req.note else ""),
        target=req.anomaly_id,
        verdict=verdict_map.get(req.decision, AuditVerdict.INFO),
        payload={"decision": req.decision, "note": req.note, "actor": req.actor},
    )

    return {
        "success": True,
        "anomaly_id": req.anomaly_id,
        "new_status": new_status,
        "decided_by": req.actor,
    }
