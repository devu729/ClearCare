"""
Agent 3: Communication Agent
- Email:    Resend API (free, 3000 emails/month)
- Calendar: ICS file generation (works everywhere, no OAuth)
"""

import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from config import get_settings

logger = logging.getLogger(__name__)


# ── EMAIL — Resend API ────────────────────────────────────────────────────────

async def send_explanation_email(to: str, subject: str, body: str) -> dict:
    try:
        import resend
    except ImportError:
        raise RuntimeError("Resend not installed. Run: pip install resend")

    s = get_settings()
    if not s.resend_api_key:
        raise RuntimeError("Add RESEND_API_KEY to your .env file. Get free key at https://resend.com")

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
        <p style="color:#94a3b8;font-size:11px;margin:0;line-height:1.6;">
          Sent by <strong>ClearCare</strong> · Healthcare Decision Intelligence<br>
          ⚠️ AI-generated content. Always verify with a licensed healthcare professional.
        </p>
      </div>
    </body>
    </html>
    """

    try:
        params = {
            "from":    "ClearCare <onboarding@resend.dev>",
            "to":      [to],
            "subject": subject,
            "text":    body,
            "html":    html_body,
        }
        resend.Emails.send(params)
        logger.info(f"Email sent to {to} via Resend")
        return {"status": "sent", "message": f"Email successfully sent to {to}"}
    except Exception as e:
        logger.error(f"Resend email error: {e}")
        raise RuntimeError(f"Email send failed: {e}")


# ── CALENDAR — ICS File ───────────────────────────────────────────────────────

async def create_calendar_event(title: str, date: str, notes: str = "") -> dict:
    event_date = _parse_date(date)
    event_dt   = datetime.strptime(event_date, "%Y-%m-%d")
    uid        = str(uuid.uuid4())
    now        = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    ics_date   = event_dt.strftime("%Y%m%d")
    ics_end    = (event_dt + timedelta(days=1)).strftime("%Y%m%d")
    r7d        = (event_dt - timedelta(days=7)).strftime("%Y%m%d")
    r1d        = (event_dt - timedelta(days=1)).strftime("%Y%m%d")

    clean_title = title.replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    clean_notes = notes.replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")

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

    logger.info(f"ICS calendar file created: {filename}")
    return {
        "status":      "created",
        "message":     f"Calendar file ready for {event_date}. Open it to add to Google Calendar, Outlook, or Apple Calendar.",
        "ics_content": ics,
        "filename":    filename,
        "event_date":  event_date,
    }


# ── HELPER — Date Parser ──────────────────────────────────────────────────────

def _parse_date(date_str: str) -> str:
    date_str = date_str.strip()

    # Already YYYY-MM-DD
    if len(date_str) == 10 and date_str[4] == "-":
        return date_str

    # "30 days from now" / "in 30 days" / "180 days"
    days_match = re.search(r"(\d+)\s*days?", date_str.lower())
    if days_match:
        return (datetime.now() + timedelta(days=int(days_match.group(1)))).strftime("%Y-%m-%d")

    # Common date formats
    for fmt in ["%B %d %Y", "%B %d, %Y", "%m/%d/%Y", "%m-%d-%Y", "%d %B %Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Default: 30 days from today
    logger.warning(f"Could not parse date '{date_str}', defaulting to 30 days from now")
    return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")