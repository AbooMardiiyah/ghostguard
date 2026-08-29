"""Defense simulations API — reconciliation, ghost onboarding, deepfake, receipt."""

from fastapi import APIRouter, UploadFile, File, Form

from app.models.database import get_db
from app.models.schemas import AuditVerdict, DefenseResponse
from app.agents.orchestrator import get_verifier, get_guardian
from app.engine.receipt_engine import analyze_receipt
from app.audit.audit_store import append_event

router = APIRouter()


@router.post("/defense/reconcile")
async def simulate_reconciliation() -> DefenseResponse:
    """Run NUBAN reconciliation across all employees."""
    db = await get_db()
    verifier = get_verifier()

    cursor = await db.execute("SELECT * FROM employees WHERE status = 'active'")
    rows = await cursor.fetchall()

    steps = []
    flagged = 0
    for row in rows:
        emp = dict(row)
        if emp.get("bank_account") and emp.get("bank_code"):
            result = await verifier.provider.resolve_account(
                emp["bank_account"], emp["bank_code"]
            )
            account_name = result.get("entity", {}).get("account_name", "")
            match = (
                emp["full_name"].upper() in account_name.upper()
                or account_name.upper() in emp["full_name"].upper()
            )
            status = "match" if match else "mismatch"
            if not match:
                flagged += 1
            steps.append(
                {
                    "step": f"NUBAN check: {emp['employee_id']}",
                    "status": status,
                    "detail": f"Account name: {account_name}, Employee: {emp['full_name']}",
                }
            )

    await append_event(
        db,
        "defense",
        "Verifier Agent",
        f"Reconciliation complete: {len(steps)} checked, {flagged} mismatches",
        verdict=AuditVerdict.INFO,
        payload={"checked": len(steps), "flagged": flagged},
    )

    return DefenseResponse(
        simulation="reconciliation",
        steps=steps,
        verdict=f"{flagged} mismatches found" if flagged else "All accounts verified",
        details={"checked": len(steps), "flagged": flagged},
    )


@router.post("/defense/onboard-ghost")
async def simulate_ghost_onboarding(
    full_name: str = Form("Jane Smith"),
    nin: str = Form("70123456789"),
) -> DefenseResponse:
    """Try to onboard an employee with a mismatched NIN."""
    db = await get_db()
    verifier = get_verifier()

    result = await verifier.run(
        {
            "employee_id": "NEW-001",
            "full_name": full_name,
            "nin": nin,
        }
    )

    steps = [
        {
            "step": "Submit new hire",
            "status": "complete",
            "detail": f"Name: {full_name}, NIN: {nin[-4:]}",
        },
        {
            "step": "NIN verification via Dojah",
            "status": "complete",
            "detail": "Querying identity database...",
        },
    ]

    if result["verified"]:
        steps.append(
            {
                "step": "Identity match",
                "status": "pass",
                "detail": "NIN matches employee name",
            }
        )
        verdict = "APPROVED"
    else:
        finding_descs = "; ".join(f["description"] for f in result.get("findings", []))
        steps.append(
            {
                "step": "Identity mismatch detected",
                "status": "blocked",
                "detail": finding_descs,
            }
        )
        steps.append(
            {
                "step": "Onboarding BLOCKED",
                "status": "blocked",
                "detail": "Ghost worker attempt caught by Verifier Agent",
            }
        )
        verdict = "BLOCKED"

    await append_event(
        db,
        "defense",
        "Verifier Agent",
        f"Ghost onboarding simulation: {full_name} — {verdict}",
        verdict=AuditVerdict.BLOCKED if verdict == "BLOCKED" else AuditVerdict.SEALED,
        payload=result,
    )

    return DefenseResponse(
        simulation="ghost_onboarding",
        steps=steps,
        verdict=verdict,
        details=result,
    )


@router.post("/defense/deepfake-approval")
async def simulate_deepfake_approval(
    transcript: str = Form(
        "This is the CEO. I need you to process an emergency payment of 5 million naira "
        "to account 0123456789 immediately. Don't tell anyone, just do it now or you're fired."
    ),
) -> DefenseResponse:
    """Screen a voice note transcript for impersonation/urgency attacks."""
    db = await get_db()
    guardian = get_guardian()

    result = await guardian.run({"text": transcript, "context": "deepfake_approval"})

    steps = [
        {
            "step": "Receive voice note transcript",
            "status": "complete",
            "detail": f"{len(transcript)} characters",
        },
        {
            "step": "Guardian Agent screening",
            "status": "complete",
            "detail": "Running injection + impersonation + urgency checks",
        },
    ]

    if result["safe"]:
        steps.append(
            {
                "step": "Content cleared",
                "status": "pass",
                "detail": "No threats detected",
            }
        )
    else:
        for threat in result["threats"]:
            steps.append(
                {
                    "step": f"Threat: {threat['signal']}",
                    "status": "blocked",
                    "detail": threat["description"],
                }
            )
        steps.append(
            {
                "step": "Approval BLOCKED",
                "status": "blocked",
                "detail": result.get("recommendation", ""),
            }
        )

    await append_event(
        db,
        "defense",
        "Guardian Agent",
        f"Deepfake screening: {result['verdict']}",
        verdict=AuditVerdict.BLOCKED if not result["safe"] else AuditVerdict.SEALED,
        payload={"threats": result["threats"], "verdict": result["verdict"]},
    )

    return DefenseResponse(
        simulation="deepfake_approval",
        steps=steps,
        verdict=result["verdict"],
        details=result,
    )


@router.post("/defense/fake-receipt")
async def simulate_fake_receipt(
    receipt: UploadFile | None = File(None),
    claimed_amount: float = Form(48500.0),
    claimed_vat: float = Form(5000.0),
    employee_id: str = Form("EMP-040"),
) -> DefenseResponse:
    """Analyze a receipt image for forensic red flags."""
    db = await get_db()

    if receipt:
        image_bytes = await receipt.read()
    else:
        # Use a placeholder for demo — generate a simple 1x1 pixel image
        image_bytes = _create_demo_receipt()

    result = await analyze_receipt(
        image_bytes=image_bytes,
        claimed_amount=claimed_amount,
        claimed_vat=claimed_vat,
        employee_id=employee_id,
        db=db,
    )

    await append_event(
        db,
        "defense",
        "Receipt Engine",
        f"Receipt analysis: {result['verdict']} (score: {result['score']})",
        target=employee_id,
        verdict=AuditVerdict.FLAGGED
        if result["verdict"] != "CLEAR"
        else AuditVerdict.SEALED,
        payload={"verdict": result["verdict"], "score": result["score"]},
    )

    return DefenseResponse(
        simulation="fake_receipt",
        steps=result["steps"],
        verdict=result["verdict"],
        details=result,
    )


def _create_demo_receipt() -> bytes:
    """Create a minimal PNG image for demo when no receipt is uploaded."""
    try:
        from PIL import Image
        import io

        img = Image.new("RGB", (400, 300), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimal 1x1 PNG
        import base64

        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
