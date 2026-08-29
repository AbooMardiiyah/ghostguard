"""Audit API — trail, verification, sealed PDF packet."""

import json
from fastapi import APIRouter
from fastapi.responses import Response

from app.models.database import get_db
from app.models.schemas import AuditChainStatus
from app.audit.audit_store import get_all_events, verify_chain
from app.audit.seal import create_seal_packet
from app.audit.pdf_packet import generate_audit_pdf

router = APIRouter()


@router.get("/audit")
async def get_audit_trail():
    db = await get_db()
    events = await get_all_events(db)
    return {"events": [e.model_dump() for e in events], "count": len(events)}


@router.get("/audit/verify")
async def verify_audit_chain() -> AuditChainStatus:
    db = await get_db()
    valid, count, latest = await verify_chain(db)
    return AuditChainStatus(chain_valid=valid, events_count=count, latest_hash=latest)


@router.get("/audit/packet")
async def download_audit_packet():
    db = await get_db()

    # Get anomalies
    cursor = await db.execute("SELECT * FROM anomalies")
    anomaly_rows = await cursor.fetchall()
    anomalies = []
    for row in anomaly_rows:
        anomalies.append(
            {
                "anomaly_id": row["anomaly_id"],
                "employee_id": row["employee_id"],
                "employee_name": row["employee_name"],
                "verdict": row["verdict"],
                "total_score": row["total_score"],
                "explanation": row["explanation"] or "",
            }
        )

    # Get audit events
    events = await get_all_events(db)
    event_dicts = [e.model_dump() for e in events]

    # Get chain hash
    valid, count, chain_hash = await verify_chain(db)

    # Create seal packet
    packet = create_seal_packet(anomalies, event_dicts, chain_hash)

    # Generate PDF
    pdf_bytes = generate_audit_pdf(packet)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=ghostguard-audit-packet.pdf"
        },
    )
