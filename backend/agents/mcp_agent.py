# ══════════════════════════════════════════════════════════════
# CALENDAR — ICS File Generation
# Works with Google Calendar, Outlook, Apple Calendar
# Zero OAuth. Zero setup. Zero Google libraries needed.
# ══════════════════════════════════════════════════════════════

import uuid

async def create_calendar_event(title: str, date: str, notes: str = "") -> dict:
    from datetime import datetime, timedelta
    import uuid, os

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
        "message":     f"Calendar file ready for {event_date}. Open it to add to Google Calendar, Outlook, or Apple Calendar.",
        "ics_content": ics,
        "filename":    filename,
        "event_date":  event_date,
    }