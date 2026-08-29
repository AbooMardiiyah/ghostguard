"""Red-Team API — run attack exercise."""

from fastapi import APIRouter

from app.models.database import get_db
from app.models.schemas import AuditVerdict, RedTeamResponse
from app.agents.orchestrator import get_redteam
from app.audit.audit_store import append_event

router = APIRouter()


@router.post("/redteam/run")
async def run_redteam() -> RedTeamResponse:
    db = await get_db()
    redteam = get_redteam()

    result = await redteam.run({})

    # Log each attack to audit trail
    for attack in result["attacks"]:
        verdict = AuditVerdict.BLOCKED if attack["caught"] else AuditVerdict.ESCALATED
        await append_event(
            db,
            "redteam",
            "Red-Team Agent",
            f"Attack '{attack['name']}': {'CAUGHT' if attack['caught'] else 'MISSED'}",
            verdict=verdict,
            payload=attack,
        )

    # Log summary
    await append_event(
        db,
        "redteam",
        "Red-Team Agent",
        f"Red-Team exercise complete: {result['caught_count']}/{result['total']} caught",
        verdict=AuditVerdict.SEALED if result["all_caught"] else AuditVerdict.ESCALATED,
        payload={
            "all_caught": result["all_caught"],
            "caught": result["caught_count"],
            "total": result["total"],
        },
    )

    return RedTeamResponse(
        attacks=result["attacks"],
        all_caught=result["all_caught"],
        audit_sealed=True,
    )
