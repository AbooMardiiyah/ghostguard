"""Scheduler API — configure and manage automated payroll scans with email notifications."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter

from app.models.database import get_db
from app.models.schemas import AuditVerdict
from app.api.payroll import scan_payroll
from app.audit.audit_store import append_event
from app.services.report_service import generate_and_send_report
from app.services.email_service import send_email, build_scan_summary_html

logger = logging.getLogger(__name__)

router = APIRouter()


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


# In-memory scheduler state
_schedule = {
    "enabled": False,
    "frequency": "monthly",
    "custom_seconds": None,
    "notification_preference": "none",  # "full" | "summary" | "none"
    "notification_email": "",
    "next_run": None,
    "last_run": None,
    "runs_completed": 0,
}
_task: asyncio.Task | None = None

INTERVAL_MAP = {
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
}


async def _scheduler_loop():
    """Background loop that runs scans at the configured interval."""
    while _schedule["enabled"]:
        # Determine interval
        if _schedule["frequency"] == "custom" and _schedule["custom_seconds"]:
            interval = _schedule["custom_seconds"]
        else:
            interval = INTERVAL_MAP.get(_schedule["frequency"], 2592000)

        # Run the scan
        try:
            db = await get_db()
            await append_event(
                db,
                "scheduler",
                "GhostGuard Scheduler",
                f"Automated {_schedule['frequency']} scan triggered",
                verdict=AuditVerdict.INFO,
            )
            result = await scan_payroll()
            _schedule["last_run"] = datetime.now(timezone.utc).isoformat()
            _schedule["runs_completed"] += 1

            # Send email notification if configured
            pref = _schedule["notification_preference"]
            email = _schedule["notification_email"]
            if pref != "none" and email:
                try:
                    anomalies = [
                        a.model_dump() if hasattr(a, "model_dump") else a
                        for a in (result.anomalies or [])
                    ]
                    await generate_and_send_report(
                        run_id=result.run_id or "scheduled",
                        anomalies=anomalies,
                        recipient_email=email,
                        report_type=pref,
                    )
                except Exception as e:
                    logger.error("Scheduler email notification failed: %s", e)

        except Exception as e:
            logger.error("Scheduled scan failed: %s", e)

        # Wait for next interval
        await asyncio.sleep(interval)


@router.get("/scheduler")
async def get_schedule():
    """Get current scheduler configuration."""
    return _schedule


@router.post("/scheduler/configure")
async def configure_schedule(
    frequency: Frequency = Frequency.MONTHLY,
    enabled: bool = True,
    custom_seconds: int | None = None,
    notification_preference: str = "none",
    notification_email: str = "",
):
    """Configure the automated scan schedule."""
    global _task

    _schedule["frequency"] = frequency.value
    _schedule["enabled"] = enabled
    _schedule["custom_seconds"] = custom_seconds
    _schedule["notification_preference"] = notification_preference
    _schedule["notification_email"] = notification_email

    # Stop existing task if running
    if _task and not _task.done():
        _task.cancel()
        _task = None

    if enabled:
        _task = asyncio.create_task(_scheduler_loop())
        _schedule["next_run"] = datetime.now(timezone.utc).isoformat()

        db = await get_db()
        freq_label = (
            f"custom ({custom_seconds}s)"
            if frequency == Frequency.CUSTOM
            else frequency.value
        )
        await append_event(
            db,
            "scheduler",
            "GhostGuard Scheduler",
            f"Scheduler enabled: {freq_label} scans",
            verdict=AuditVerdict.INFO,
        )
    else:
        _schedule["next_run"] = None
        db = await get_db()
        await append_event(
            db,
            "scheduler",
            "GhostGuard Scheduler",
            "Scheduler disabled",
            verdict=AuditVerdict.INFO,
        )

    return _schedule


@router.post("/scheduler/run-now")
async def run_now():
    """Trigger an immediate scan (outside the schedule)."""
    db = await get_db()
    await append_event(
        db,
        "scheduler",
        "GhostGuard Scheduler",
        "Manual scan triggered via scheduler",
        verdict=AuditVerdict.INFO,
    )

    result = await scan_payroll()
    _schedule["last_run"] = datetime.now(timezone.utc).isoformat()
    _schedule["runs_completed"] += 1

    return {
        "triggered": True,
        "scan_result": result,
        "schedule": _schedule,
    }


@router.post("/scheduler/send-email")
async def send_anomaly_email(recipient: str, anomalies_json: str = "[]"):
    """Send current anomaly data to a specified email address."""
    anomalies = json.loads(anomalies_json)
    html = build_scan_summary_html("manual-export", anomalies)
    success = await send_email(recipient, "GhostGuard Anomaly Report", html)
    return {"sent": success}
