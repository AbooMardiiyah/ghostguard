"""Email service — SMTP-based email sending with HTML templates."""

import asyncio
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    attachments: list[tuple[str, bytes]] | None = None,
) -> bool:
    """Send an email via SMTP. Returns True on success, False on failure."""
    if not settings.smtp_host:
        logger.warning("SMTP not configured — skipping email to %s", to)
        return False

    def _send():
        msg = MIMEMultipart()
        msg["From"] = settings.email_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        if attachments:
            for filename, data in attachments:
                part = MIMEApplication(data, Name=filename)
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)

        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=30
            )
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.starttls()

        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.email_from, [to], msg.as_string())
        server.quit()

    try:
        await asyncio.to_thread(_send)
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def build_scan_summary_html(
    run_id: str,
    anomalies: list[dict],
    executive_summary: str | None = None,
) -> str:
    """Build a styled HTML email body for a scan report."""
    total_exposure = sum(a.get("monthly_exposure", 0) for a in anomalies)
    block_count = sum(1 for a in anomalies if a.get("verdict") == "BLOCK")
    flag_count = sum(1 for a in anomalies if a.get("verdict") == "FLAG")

    # Top 5 anomalies table rows
    top = sorted(anomalies, key=lambda a: a.get("total_score", 0), reverse=True)[:5]
    rows_html = ""
    for a in top:
        verdict = a.get("verdict", "")
        color = (
            "#dc2626"
            if verdict == "BLOCK"
            else "#f59e0b"
            if verdict == "FLAG"
            else "#10b981"
        )
        rows_html += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #27272a;color:#e4e4e7">{a.get("employee_name", "")}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #27272a;color:#e4e4e7;text-align:center">{a.get("total_score", 0)}%</td>
          <td style="padding:8px 12px;border-bottom:1px solid #27272a;color:{color};font-weight:600;text-align:center">{verdict}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #27272a;color:#e4e4e7;text-align:right">&#8358;{a.get("monthly_exposure", 0):,.0f}</td>
        </tr>"""

    summary_section = ""
    if executive_summary:
        summary_section = f"""
        <div style="background:#064e3b;border:1px solid #10b981;border-radius:8px;padding:16px;margin-bottom:24px">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#6ee7b7;margin-bottom:8px;font-weight:600">Executive Summary</div>
          <p style="color:#d1fae5;margin:0;font-size:14px;line-height:1.6">{executive_summary}</p>
        </div>"""

    return f"""
    <div style="background:#09090b;padding:32px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
      <div style="max-width:600px;margin:0 auto">
        <div style="text-align:center;margin-bottom:24px">
          <div style="font-size:20px;font-weight:700;color:#10b981">GhostGuard</div>
          <div style="font-size:12px;color:#71717a;margin-top:4px">Payroll Integrity Report</div>
        </div>

        {summary_section}

        <div style="background:#18181b;border:1px solid #27272a;border-radius:12px;padding:20px;margin-bottom:24px">
          <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#71717a;margin-bottom:12px;font-weight:600">Scan Summary</div>
          <div style="display:flex;gap:16px">
            <div style="flex:1;text-align:center">
              <div style="font-size:28px;font-weight:700;color:#e4e4e7">{len(anomalies)}</div>
              <div style="font-size:11px;color:#71717a">Anomalies</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="font-size:28px;font-weight:700;color:#dc2626">{block_count}</div>
              <div style="font-size:11px;color:#71717a">Blocked</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="font-size:28px;font-weight:700;color:#f59e0b">{flag_count}</div>
              <div style="font-size:11px;color:#71717a">Flagged</div>
            </div>
            <div style="flex:1;text-align:center">
              <div style="font-size:28px;font-weight:700;color:#e4e4e7">&#8358;{total_exposure:,.0f}</div>
              <div style="font-size:11px;color:#71717a">Exposure</div>
            </div>
          </div>
        </div>

        <div style="background:#18181b;border:1px solid #27272a;border-radius:12px;overflow:hidden;margin-bottom:24px">
          <div style="padding:12px 16px;border-bottom:1px solid #27272a">
            <span style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#71717a;font-weight:600">Top Anomalies</span>
          </div>
          <table style="width:100%;border-collapse:collapse">
            <tr style="background:#27272a">
              <th style="padding:8px 12px;text-align:left;font-size:11px;color:#a1a1aa;font-weight:600">Employee</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;color:#a1a1aa;font-weight:600">Risk</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;color:#a1a1aa;font-weight:600">Verdict</th>
              <th style="padding:8px 12px;text-align:right;font-size:11px;color:#a1a1aa;font-weight:600">Exposure</th>
            </tr>
            {rows_html}
          </table>
        </div>

        <div style="text-align:center;padding:16px">
          <p style="font-size:12px;color:#52525b;margin:0">
            Run ID: {run_id} &middot; Generated by GhostGuard v1.0
          </p>
          <p style="font-size:11px;color:#3f3f46;margin:8px 0 0">
            Log in to review findings and take action.
          </p>
        </div>
      </div>
    </div>
    """
