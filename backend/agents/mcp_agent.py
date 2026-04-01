"""
Agent 3: Communication Agent
- Email:    Auth0 Token Vault → Gmail API (user's own email)
            Falls back to Resend if Token Vault not configured
- Calendar: Auth0 Token Vault → Google Calendar API (user's own calendar)
            Falls back to ICS file download if Token Vault not configured
"""

import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from config import get_settings

logger = logging.getLogger(__name__)


# ── EMAIL ─────────────────────────────────────────────────────────────────────

async def send_explanation_email(
    to: str,
    subject: str,
    body: str,
    user_access_token: str | None = None,
    sender_email: str | None = None,
) -> dict:
    """
    Send appeal letter email.

    Priority:
    1. Auth0 Token Vault → user's own Gmail (best — real identity)
    2. Resend API → generic sender (fallback)

    Args:
        to: Recipient email
        subject: Email subject
        body: Appeal letter text
        user_access_token: Auth0 JWT (enables Token Vault)
        sender_email: User's Gmail address (required for Token Vault)
    """
    s = get_settings()

    # Try Token Vault first if configured and user token provided
    if user_access_token and sender_email and s.token_vault_enabled:
        try:
            from auth.token_vault import send_via_gmail_token_vault
            result = await send_via_gmail_token_vault(
                user_access_token=user_access_token,
                sender_email=sender_email,
                to=to,
                subject=subject,
                body=body,
            )
            logger.info(f"Email sent via Token Vault from {sender_email}")
            return result
        except Exception as e:
            logger.warning(f"Token Vault email failed, falling back to Resend: {e}")

    # Fallback: Resend API
    return await _send_via_resend(to, subject, body)


async def _send_via_resend(to: str, subject: str, body: str) -> dict:
    """Fallback email via Resend API."""
    try:
        import resend
    except ImportError:
        raise RuntimeError("Resend not installed. Run: pip install resend")

    s = get_settings()
    if not s.resend_api_key:
        raise RuntimeError("No email method configured. Add RESEND_API_KEY or configure Auth0 Token Vault.")

    resend.api_key = s.resend_api_key

    html_body = f"""
    <html>
    <body style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f0f9ff;">
      <div style="background:linear-gradient(135deg,#0284c7,#0ea5e9);padding:28px;border-radius:12px 12px 0 0;">
        <h1 style="color:white;margin:0;font-size:22px;">🏥 ClearCare</h1>
        <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:13px;">Healthcare Decision Intelligence</p>
      </div>
      <div style="background:#ffffff;padding:32px;border:1px solid #bae6fd;border-top:none;border-radius:0 0 12px 12px;">
        <h2 style="color:#0f172a;font-size:17px;margin-top:0;margin-bottom:16px;">{subject}</h2>
        <div style="color:#334155;font-size:14px;line-height:1.9;white-space:pre-wrap;">{body}</div>
        <hr style="border:none;border-top:1px solid #e0f2fe;margin:28px 0;">
        <p style="color:#94a3b8;font-size:11px;margin:0;">
          Sent by <strong>ClearCare</strong> · AI-generated content. Always verify with a licensed professional.
        </p>
      </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from":    "ClearCare <onboarding@resend.dev>",
            "to":      [to],
            "subject": subject,
            "text":    body,
            "html":    html_body,
        })
        return {"status": "sent", "message": f"Email sent to {to}", "via": "Resend"}
    except Exception as e:
        raise RuntimeError(f"Email send failed: {e}")


# ── CALENDAR ──────────────────────────────────────────────────────────────────

async def create_calendar_event(
    title: str,
    date: str,
    notes: str = "",
    user_access_token: str | None = None,
) -> dict:
    """
    Add appeal deadline to calendar.

    Priority:
    1. Auth0 Token Vault → user's own Google Calendar (best)
    2. ICS file download (fallback — works everywhere)

    Args:
        title: Event title
        date: Appeal deadline date
        notes: Event description
        user_access_token: Auth0 JWT (enables Token Vault)
    """
    s = get_settings()

    # Try Token Vault first
    if user_access_token and s.token_vault_enabled:
        try:
            from auth.token_vault import add_to_google_calendar_token_vault
            result = await add_to_google_calendar_token_vault(
                user_access_token=user_access_token,
                title=title,
                date=date,
                notes=notes,
            )
            logger.info("Calendar event created via Token Vault")
            return result
        except Exception as e:
            logger.warning(f"Token Vault calendar failed, falling back to ICS: {e}")

    # Fallback: ICS file
    return _generate_ics(title, date, notes)


def _generate_ics(title: str, date: str, notes: str = "") -> dict:
    """Fallback: generate ICS calendar file."""
    event_date = _parse_date(date)
    event_dt   = datetime.strptime(event_date, "%Y-%m-%d")
    uid        = str(uuid.uuid4())
    now        = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    ics_date   = event_dt.strftime("%Y%m%d")
    ics_end    = (event_dt + timedelta(days=1)).strftime("%Y%m%d")
    r7d        = (event_dt - timedelta(days=7)).strftime("%Y%m%d")
    r1d        = (event_dt - timedelta(days=1)).strftime("%Y%m%d")

    clean_title = title.replace(",","\\,").replace(";","\\;").replace("\n","\\n")
    clean_notes = notes.replace(",","\\,").replace(";","\\;").replace("\n","\\n")

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ClearCare//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
DTSTART;VALUE=DATE:{ics_date}
DTEND;VALUE=DATE:{ics_end}
SUMMARY:{clean_title}
DESCRIPTION:{clean_notes}
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:7-day reminder
TRIGGER;VALUE=DATE-TIME:{r7d}T090000Z
END:VALARM
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:1-day reminder
TRIGGER;VALUE=DATE-TIME:{r1d}T090000Z
END:VALARM
END:VEVENT
END:VCALENDAR"""

    os.makedirs("calendar_exports", exist_ok=True)
    filename = f"appeal_{event_date}_{uid[:8]}.ics"
    with open(os.path.join("calendar_exports", filename), "w") as f:
        f.write(ics)

    return {
        "status":      "created",
        "message":     f"Calendar file ready for {event_date}.",
        "ics_content": ics,
        "filename":    filename,
        "event_date":  event_date,
        "via":         "ICS file download",
    }


def _parse_date(date_str: str) -> str:
    date_str = date_str.strip()
    if len(date_str) == 10 and date_str[4] == "-":
        return date_str
    days_match = re.search(r"(\d+)\s*days?", date_str.lower())
    if days_match:
        return (datetime.now() + timedelta(days=int(days_match.group(1)))).strftime("%Y-%m-%d")
    for fmt in ["%B %d %Y", "%B %d, %Y", "%m/%d/%Y", "%m-%d-%Y", "%d %B %Y"]:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")