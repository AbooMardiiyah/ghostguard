"""Hash-chained append-only audit log — from L84 ComplianceAuditStore pattern."""

import hashlib
import json
import uuid
from datetime import datetime, timezone

import aiosqlite

from app.models.schemas import AuditEvent, AuditVerdict


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


async def get_latest_chain_hash(db: aiosqlite.Connection) -> str:
    """Get the chain_hash of the most recent audit event, or '0' * 64 for genesis."""
    cursor = await db.execute(
        "SELECT chain_hash FROM audit_trail ORDER BY id DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    return row["chain_hash"] if row else "0" * 64


async def append_event(
    db: aiosqlite.Connection,
    event_type: str,
    actor: str,
    action: str,
    target: str | None = None,
    verdict: AuditVerdict | None = None,
    detail: str | None = None,
    payload: dict | None = None,
) -> AuditEvent:
    """Append a new event to the audit trail with hash chaining."""
    event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc)
    payload_json = json.dumps(payload or {}, default=str, sort_keys=True)

    evidence_hash = _sha256(payload_json)
    prev_hash = await get_latest_chain_hash(db)
    chain_hash = _sha256(prev_hash + evidence_hash)

    await db.execute(
        """INSERT INTO audit_trail
           (event_id, timestamp, event_type, actor, action, target, verdict,
            detail, payload_json, evidence_hash, chain_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event_id,
            timestamp.isoformat(),
            event_type,
            actor,
            action,
            target,
            verdict.value if verdict else None,
            detail,
            payload_json,
            evidence_hash,
            chain_hash,
        ),
    )
    await db.commit()

    return AuditEvent(
        event_id=event_id,
        timestamp=timestamp,
        event_type=event_type,
        actor=actor,
        action=action,
        target=target,
        verdict=verdict,
        detail=detail,
        payload_json=payload_json,
        evidence_hash=evidence_hash,
        chain_hash=chain_hash,
    )


async def get_all_events(db: aiosqlite.Connection) -> list[AuditEvent]:
    """Return all audit events, newest first."""
    cursor = await db.execute("SELECT * FROM audit_trail ORDER BY id DESC")
    rows = await cursor.fetchall()
    events = []
    for row in rows:
        events.append(
            AuditEvent(
                event_id=row["event_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                event_type=row["event_type"],
                actor=row["actor"],
                action=row["action"],
                target=row["target"],
                verdict=AuditVerdict(row["verdict"]) if row["verdict"] else None,
                detail=row["detail"],
                payload_json=row["payload_json"],
                evidence_hash=row["evidence_hash"],
                chain_hash=row["chain_hash"],
            )
        )
    return events


async def verify_chain(db: aiosqlite.Connection) -> tuple[bool, int, str]:
    """Verify the entire hash chain. Returns (valid, count, latest_hash)."""
    cursor = await db.execute("SELECT * FROM audit_trail ORDER BY id ASC")
    rows = await cursor.fetchall()

    if not rows:
        return True, 0, ""

    prev_hash = "0" * 64
    for row in rows:
        evidence_hash = _sha256(row["payload_json"] or "{}")
        expected_chain = _sha256(prev_hash + evidence_hash)

        if row["evidence_hash"] != evidence_hash:
            return False, len(rows), row["chain_hash"]
        if row["chain_hash"] != expected_chain:
            return False, len(rows), row["chain_hash"]

        prev_hash = row["chain_hash"]

    return True, len(rows), rows[-1]["chain_hash"]
