"""SHA-256 seal generation for audit packets."""

import hashlib
import json
from datetime import datetime, timezone


def generate_seal(data: dict) -> str:
    """Generate a SHA-256 seal from a data dictionary."""
    canonical = json.dumps(data, default=str, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_seal_packet(
    anomalies: list[dict],
    audit_events: list[dict],
    chain_hash: str,
) -> dict:
    """Create a complete seal packet with metadata and SHA-256 seal."""
    packet = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "GhostGuard v1.0",
        "company": "Sterling Distributors Ltd",
        "period": "August 2026",
        "anomaly_count": len(anomalies),
        "audit_event_count": len(audit_events),
        "chain_hash": chain_hash,
        "anomalies": anomalies,
        "audit_events": audit_events,
    }
    packet["seal"] = generate_seal(packet)
    return packet
