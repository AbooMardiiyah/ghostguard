"""Employees API — list, detail, onboard."""

from fastapi import APIRouter, HTTPException, Header, Query

from app.models.database import get_db
from app.models.schemas import AuditVerdict
from app.engine.pii_masker import mask_employee_pii
from app.audit.audit_store import append_event

router = APIRouter()


@router.get("/employees")
async def list_employees(
    unmask: bool = Query(False),
    x_user_role: str = Header("auditor"),
):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM employees ORDER BY employee_id")
    rows = await cursor.fetchall()
    employees = [dict(row) for row in rows]
    if unmask:
        if x_user_role not in ("auditor", "admin"):
            raise HTTPException(
                status_code=403, detail="Insufficient role for PII access"
            )
        await append_event(
            db,
            "pii_access",
            x_user_role,
            f"Unmasked employee list ({len(employees)} records)",
            verdict=AuditVerdict.INFO,
        )
    else:
        employees = [mask_employee_pii(e) for e in employees]
    return {"employees": employees, "count": len(employees)}


@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, unmask: bool = Query(False)):
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM employees WHERE employee_id = ?", (employee_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp = dict(row)
    if not unmask:
        emp = mask_employee_pii(emp)
    return emp
