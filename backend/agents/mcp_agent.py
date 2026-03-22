"""
Agent 3: Communication Agent
- Email: Resend API (free, 3000 emails/month, no SMTP issues)
- Calendar: Google Calendar API (free, OAuth2)

No Anthropic key required. No credit card. Works forever free.
"""

import logging
import os
import pickle
import re
from datetime import datetime, timedelta
from config   import get_settings

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# EMAIL — Resend API
# Free: 3,000 emails/month. No SMTP, no 2FA needed.
# Get free key at: https://resend.com
# ══════════════════════════════════════════════════════════════

async def send_explanation_email(to: str, subject: str, body: str) -> dict:
    """
    Send email via Resend API.
    Requires RESEND_API_KEY in .env
    Get free key at: https://resend.com (sign in with Google, no card)
    """
    try:
        import resend
    except ImportError:
        raise RuntimeError("Resend not installed. Run: pip install resend")

    s = get_settings()

    if not s.resend_api_key:
        raise RuntimeError(
            "Resend not configured. Add RESEND_API_KEY to your .env file.\n"
            "Get a free key at: https://resend.com"
        )

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


# ══════════════════════════════════════════════════════════════
# CALENDAR — Google Calendar API
# Free forever. Uses OAuth2 with your Google account.
# Requires credentials.json from Google Cloud Console in backend/ folder.
# ══════════════════════════════════════════════════════════════

async def create_calendar_event(title: str, date: str, notes: str = "") -> dict:
    """
    Create a Google Calendar event with reminders.
    Requires credentials.json in backend/ folder.
    First run opens browser for Google login — one time only.
    Token saved in token.pickle — works automatically after that.
    """
    try:
        from googleapiclient.discovery      import build
        from google_auth_oauthlib.flow      import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        raise RuntimeError(
            "Google Calendar library not installed.\n"
            "Run: pip install google-api-python-client google-auth-oauthlib"
        )

    SCOPES           = ["https://www.googleapis.com/auth/calendar"]
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE       = "token.pickle"

    if not os.path.exists(CREDENTIALS_FILE):
        raise RuntimeError(
            "credentials.json not found in backend/ folder.\n"
            "1. Go to https://console.cloud.google.com\n"
            "2. Create project → Enable Google Calendar API\n"
            "3. Credentials → Create OAuth 2.0 Client ID → Desktop app\n"
            "4. Download JSON → rename to credentials.json → put in backend/ folder"
        )

    try:
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow  = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)

        service    = build("calendar", "v3", credentials=creds)
        event_date = _parse_date(date)

        event = {
            "summary":     title,
            "description": notes,
            "start": {"date": event_date, "timeZone": "America/New_York"},
            "end":   {"date": event_date, "timeZone": "America/New_York"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 7 * 24 * 60},
                    {"method": "email",  "minutes": 1 * 24 * 60},
                    {"method": "popup",  "minutes": 1 * 24 * 60},
                ],
            },
            "colorId": "1",
        }

        created    = service.events().insert(calendarId="primary", body=event).execute()
        event_link = created.get("htmlLink", "")

        logger.info(f"Calendar event created: {title} on {event_date}")
        return {
            "status":     "created",
            "message":    f"Appeal deadline '{title}' added to Google Calendar for {event_date}. Reminders set 7 days and 1 day before.",
            "event_link": event_link,
            "event_date": event_date,
        }

    except Exception as e:
        logger.error(f"Calendar error: {e}")
        raise RuntimeError(f"Calendar event creation failed: {e}")


def _parse_date(date_str: str) -> str:
    """Parse various date formats into YYYY-MM-DD."""
    date_str = date_str.strip()

    # Already YYYY-MM-DD
    if len(date_str) == 10 and date_str[4] == "-":
        return date_str

    # "30 days from now" / "in 30 days"
    days_match = re.search(r"(\d+)\s*days?", date_str.lower())
    if days_match:
        return (datetime.now() + timedelta(days=int(days_match.group(1)))).strftime("%Y-%m-%d")

    # Common formats
    for fmt in ["%B %d %Y", "%B %d, %Y", "%m/%d/%Y", "%m-%d-%Y", "%d %B %Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Default: 30 days from today
    logger.warning(f"Could not parse date '{date_str}', defaulting to 30 days from now")
    return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")