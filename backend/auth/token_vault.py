"""
Auth0 Token Vault Integration for ClearCare
==========================================
Token Vault allows ClearCare to send appeal letters FROM the user's
own Gmail/Google Workspace account — without ever storing their password.

Flow:
1. User connects their Google account via Auth0 (one time)
2. Auth0 stores the Google OAuth token securely in Token Vault
3. When user clicks "Send from my Gmail", ClearCare asks Auth0 for the token
4. Auth0 exchanges the user's access token for their Google token
5. ClearCare uses the Google token to send email via Gmail API
6. Appeal letter arrives FROM the patient's real email address

Why this matters for healthcare:
- An appeal from john.smith@gmail.com carries legal weight
- An appeal from onboarding@resend.dev gets ignored or marked as spam
- Insurance companies take patient-sent appeals more seriously
"""

import base64
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


async def exchange_token_for_google(user_access_token: str) -> str:
    """
    Exchange the user's Auth0 access token for their Google OAuth token
    using Auth0 Token Vault.

    Auth0 Token Vault stores the user's Google credentials securely.
    We never see or store their Google password or refresh token directly.

    Args:
        user_access_token: The Auth0 JWT access token from the user's session

    Returns:
        Google access token that can be used to call Gmail API
    """
    s = get_settings()

    if not s.token_vault_enabled:
        raise RuntimeError(
            "Auth0 Token Vault not configured. "
            "Add AUTH0_DOMAIN, AUTH0_CUSTOM_API_CLIENT_ID, "
            "AUTH0_CUSTOM_API_CLIENT_SECRET to your .env"
        )

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://{s.auth0_domain}/oauth/token",
            json={
                "grant_type":         "urn:auth0:params:oauth:grant-type:token-vault",
                "client_id":          s.auth0_custom_api_client_id,
                "client_secret":      s.auth0_custom_api_client_secret,
                "subject_token":      user_access_token,
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "audience":           "https://www.googleapis.com/",
                "connection":         "google-oauth2",
                "scope":              "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar",
            }
        )

        if response.status_code != 200:
            logger.error(f"Token Vault exchange failed: {response.text}")
            raise RuntimeError(
                f"Token Vault exchange failed: {response.json().get('error_description', 'Unknown error')}. "
                "Make sure the user has connected their Google account."
            )

        data = response.json()
        google_token = data.get("access_token")

        if not google_token:
            raise RuntimeError("Token Vault returned no access token")

        logger.info("Token Vault exchange successful — got Google token")
        return google_token


async def send_via_gmail_token_vault(
    user_access_token: str,
    sender_email: str,
    to: str,
    subject: str,
    body: str,
) -> dict:
    """
    Send an email using the user's own Gmail via Auth0 Token Vault.

    The appeal letter arrives FROM the patient's real email address,
    not from a generic service address. This is critical for healthcare
    appeals — insurance companies take them more seriously.

    Args:
        user_access_token: Auth0 JWT from user's session
        sender_email: The user's Gmail address (shown in From field)
        to: Recipient email
        subject: Email subject
        body: Email body (plain text appeal letter)
    """
    # Get Google token from Auth0 Token Vault
    google_token = await exchange_token_for_google(user_access_token)

    # Build the email
    msg = MIMEMultipart("alternative")
    msg["To"]      = to
    msg["From"]    = f"ClearCare Appeal <{sender_email}>"
    msg["Subject"] = subject

    # Plain text version
    text_part = MIMEText(body, "plain")

    # HTML version with ClearCare branding
    html_body = f"""
    <html>
    <body style="font-family:'Segoe UI',Arial,sans-serif;max-width:640px;margin:0 auto;padding:20px;background:#f0f9ff;">
      <div style="background:linear-gradient(135deg,#0284c7,#0ea5e9);padding:24px;border-radius:12px 12px 0 0;">
        <h1 style="color:white;margin:0;font-size:20px;">🏥 ClearCare</h1>
        <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:12px;">
          Healthcare Decision Intelligence · Sent via Auth0 Token Vault
        </p>
      </div>
      <div style="background:#fff;padding:32px;border:1px solid #bae6fd;border-top:none;border-radius:0 0 12px 12px;">
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px 16px;margin-bottom:20px;">
          <p style="margin:0;font-size:12px;color:#166534;">
            🔐 <strong>Sent securely</strong> from {sender_email} via Auth0 Token Vault. 
            ClearCare never stored your Google credentials.
          </p>
        </div>
        <div style="color:#334155;font-size:14px;line-height:1.9;white-space:pre-wrap;font-family:'Courier New',monospace;">{body}</div>
        <hr style="border:none;border-top:1px solid #e0f2fe;margin:28px 0;">
        <p style="color:#94a3b8;font-size:11px;margin:0;line-height:1.6;">
          Generated by <strong>ClearCare</strong> · AI-generated content.<br>
          Always verify with a licensed healthcare professional before submitting.
        </p>
      </div>
    </body>
    </html>
    """

    html_part = MIMEText(html_body, "html")
    msg.attach(text_part)
    msg.attach(html_part)

    # Encode for Gmail API
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    # Send via Gmail API using the user's own Google token
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {google_token}",
                "Content-Type":  "application/json",
            },
            json={"raw": raw},
        )

        if response.status_code not in (200, 201):
            logger.error(f"Gmail API error: {response.text}")
            raise RuntimeError(
                f"Gmail send failed: {response.json().get('error', {}).get('message', 'Unknown error')}"
            )

    logger.info(f"Email sent from {sender_email} to {to} via Gmail Token Vault")
    return {
        "status":     "sent",
        "message":    f"Appeal letter sent from your Gmail ({sender_email}) to {to}",
        "sent_from":  sender_email,
        "via":        "Auth0 Token Vault → Gmail API",
    }


async def add_to_google_calendar_token_vault(
    user_access_token: str,
    title: str,
    date: str,
    notes: str = "",
) -> dict:
    """
    Add appeal deadline to user's own Google Calendar via Token Vault.
    No OAuth popup. No credentials.json. Just their own calendar.
    """
    from datetime import datetime, timedelta
    import re

    # Parse date
    date_str = date.strip()
    if len(date_str) == 10 and date_str[4] == "-":
        event_date = date_str
    else:
        days_match = re.search(r"(\d+)\s*days?", date_str.lower())
        if days_match:
            event_date = (datetime.now() + timedelta(days=int(days_match.group(1)))).strftime("%Y-%m-%d")
        else:
            event_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    # Get Google token from Token Vault
    google_token = await exchange_token_for_google(user_access_token)

    # Build calendar event
    end_date = (datetime.strptime(event_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    event = {
        "summary":     title,
        "description": notes,
        "start":       {"date": event_date},
        "end":         {"date": end_date},
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

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={
                "Authorization": f"Bearer {google_token}",
                "Content-Type":  "application/json",
            },
            json=event,
        )

        if response.status_code not in (200, 201):
            raise RuntimeError(f"Calendar API error: {response.json().get('error', {}).get('message', 'Unknown')}")

        created = response.json()

    logger.info(f"Calendar event created via Token Vault: {title} on {event_date}")
    return {
        "status":     "created",
        "message":    f"Appeal deadline added to your Google Calendar for {event_date}. Reminders set 7 days and 1 day before.",
        "event_link": created.get("htmlLink", ""),
        "event_date": event_date,
        "via":        "Auth0 Token Vault → Google Calendar API",
    }