"""Report service — LLM executive summaries + PDF generation + email delivery."""

import logging

from app.config import settings
from app.services.email_service import send_email, build_scan_summary_html
from app.audit.pdf_packet import generate_audit_pdf
from app.audit.seal import create_seal_packet
from app.audit.audit_store import get_all_events, verify_chain
from app.models.database import get_db

logger = logging.getLogger(__name__)


async def _call_llm(prompt: str) -> str:
    """Standalone LLM call with provider fallback chain."""
    import httpx

    # Try Gemini first
    if settings.gemini_api_key:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    url,
                    params={"key": settings.gemini_api_key},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                resp.raise_for_status()
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass

    # Fallback: Together AI
    if settings.together_api_key:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.together_api_key}"},
                    json={
                        "model": settings.together_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

    # Final fallback: template
    return "Automated scan completed. Review the attached report for detailed findings."


async def generate_executive_summary(anomalies: list[dict]) -> str:
    """Use LLM to generate an executive summary paragraph."""
    total_exposure = sum(a.get("monthly_exposure", 0) for a in anomalies)
    block_count = sum(1 for a in anomalies if a.get("verdict") == "BLOCK")
    flag_count = sum(1 for a in anomalies if a.get("verdict") == "FLAG")

    findings_text = "; ".join(
        f"{a.get('employee_name', 'Unknown')} ({a.get('verdict', '')}, score {a.get('total_score', 0)}%)"
        for a in sorted(anomalies, key=lambda x: x.get("total_score", 0), reverse=True)[
            :5
        ]
    )

    prompt = (
        "You are GhostGuard, a payroll fraud detection system. Write a 2-3 paragraph executive summary "
        "for a payroll integrity scan report. Be professional and concise. Use 'anomaly' not 'fraud'. "
        "Cite specific numbers.\n\n"
        f"Results: {len(anomalies)} anomalies detected, {block_count} blocked, {flag_count} flagged. "
        f"Total monthly exposure: ₦{total_exposure:,.0f}.\n"
        f"Top findings: {findings_text}"
    )
    return await _call_llm(prompt)


async def _build_pdf_bytes(anomalies: list[dict]) -> bytes:
    """Generate the sealed audit PDF packet."""
    db = await get_db()
    events = await get_all_events(db)
    event_dicts = [e.model_dump() for e in events]
    _, _, chain_hash = await verify_chain(db)
    packet = create_seal_packet(anomalies, event_dicts, chain_hash)
    return generate_audit_pdf(packet)


async def generate_and_send_report(
    run_id: str,
    anomalies: list[dict],
    recipient_email: str,
    report_type: str = "full",
) -> dict:
    """Generate report and send via email.

    report_type: "full" (LLM summary + PDF attachment), "summary" (HTML email only), "none" (skip)
    """
    if report_type == "none" or not recipient_email:
        return {"sent": False, "reason": "notifications disabled"}

    executive_summary = None
    attachments = None

    if report_type == "full":
        executive_summary = await generate_executive_summary(anomalies)
        try:
            pdf_bytes = await _build_pdf_bytes(anomalies)
            attachments = [("ghostguard-audit-report.pdf", pdf_bytes)]
        except Exception as e:
            logger.error("PDF generation failed: %s", e)

    html = build_scan_summary_html(run_id, anomalies, executive_summary)
    subject = f"GhostGuard Scan Report — {len(anomalies)} anomalies detected"

    sent = await send_email(recipient_email, subject, html, attachments)
    return {"sent": sent, "report_type": report_type, "recipient": recipient_email}
