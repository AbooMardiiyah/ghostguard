"""Verify API — identity verification via Dojah/MockAdapter."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.database import get_db
from app.models.schemas import AuditVerdict, VerifyResponse
from app.agents.orchestrator import get_verifier
from app.audit.audit_store import append_event

router = APIRouter()


class VerifyRequest(BaseModel):
    employee_id: str | None = None
    full_name: str = ""
    nin: str | None = None
    bvn: str | None = None
    bank_account: str | None = None
    bank_code: str | None = None


@router.post("/verify")
async def verify_identity(req: VerifyRequest) -> VerifyResponse:
    db = await get_db()

    # If employee_id provided, load from DB
    employee_data = req.model_dump()
    if req.employee_id:
        cursor = await db.execute(
            "SELECT * FROM employees WHERE employee_id = ?", (req.employee_id,)
        )
        row = await cursor.fetchone()
        if row:
            employee_data = dict(row)

    verifier = get_verifier()
    result = await verifier.run(employee_data)

    verified = result["verified"]

    # Update employee record if exists
    if req.employee_id:
        await db.execute(
            """UPDATE employees SET identity_verified = ?, verification_date = ?,
               verification_source = ? WHERE employee_id = ?""",
            (
                1 if verified else 0,
                datetime.now(timezone.utc).isoformat(),
                "dojah_sandbox" if verified else "dojah_sandbox_failed",
                req.employee_id,
            ),
        )
        await db.commit()

    # Audit log
    verdict = AuditVerdict.SEALED if verified else AuditVerdict.BLOCKED
    await append_event(
        db,
        "verify",
        "Verifier Agent",
        f"Identity verification {'passed' if verified else 'FAILED'} for {employee_data.get('full_name', 'unknown')}",
        target=req.employee_id,
        verdict=verdict,
        payload={"verified": verified, "citations": result.get("citations", {})},
    )

    return VerifyResponse(
        employee_id=req.employee_id or "manual",
        verified=verified,
        findings=result.get("findings", []),
        citations=result.get("citations", {}),
    )
