"""Dashboard API — KPIs, anomalies, agent status."""

import json
from fastapi import APIRouter

from app.models.database import get_db
from app.models.schemas import Anomaly, DashboardResponse, LayerFinding, Verdict
from app.agents.orchestrator import get_all_agent_statuses
from app.engine.pii_masker import mask_employee_pii

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard() -> DashboardResponse:
    db = await get_db()

    # KPIs
    cursor = await db.execute(
        "SELECT COUNT(*) as c FROM employees WHERE status = 'active'"
    )
    total_employees = (await cursor.fetchone())["c"]

    cursor = await db.execute(
        "SELECT COUNT(*) as c FROM employees WHERE identity_verified = 1"
    )
    verified_count = (await cursor.fetchone())["c"]

    cursor = await db.execute(
        "SELECT COUNT(*) as c FROM anomalies WHERE status IN ('open', 'blocked')"
    )
    open_anomalies = (await cursor.fetchone())["c"]

    compliance_pct = round(
        (verified_count / total_employees * 100) if total_employees > 0 else 0, 1
    )

    # Total exposure from anomalies
    cursor = await db.execute(
        "SELECT COALESCE(SUM(monthly_exposure), 0) as total FROM anomalies WHERE status IN ('open', 'blocked')"
    )
    total_exposure = (await cursor.fetchone())["total"]

    kpis = {
        "total_employees": total_employees,
        "verified_count": verified_count,
        "open_anomalies": open_anomalies,
        "compliance_pct": compliance_pct,
        "total_exposure": total_exposure,
    }

    # Anomalies
    cursor = await db.execute("SELECT * FROM anomalies ORDER BY total_score DESC")
    rows = await cursor.fetchall()
    anomalies = []
    for row in rows:
        findings_raw = json.loads(row["findings_json"]) if row["findings_json"] else []
        findings = [LayerFinding(**f) for f in findings_raw]
        anomalies.append(
            Anomaly(
                anomaly_id=row["anomaly_id"],
                employee_id=row["employee_id"],
                employee_name=row["employee_name"],
                run_id=row["run_id"],
                findings=findings,
                total_score=row["total_score"],
                verdict=Verdict(row["verdict"]),
                monthly_exposure=row["monthly_exposure"],
                explanation=row["explanation"] or "",
                status=row["status"],
                decided_by=row["decided_by"],
            )
        )

    # Agents
    agents = get_all_agent_statuses()

    return DashboardResponse(kpis=kpis, anomalies=anomalies, agents=agents)
