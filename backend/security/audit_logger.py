"""Logs every action to Supabase audit_logs table for HIPAA compliance."""

from supabase import create_client
from config import get_settings
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


async def log_action(
    action: str,
    user_id: str | None = None,
    resource: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Write audit entry. Never raises — logging must not crash main request."""
    try:
        s = get_settings()
        client = create_client(s.supabase_url, s.supabase_service_key)
        client.table("audit_logs").insert({
            "user_id":    user_id,
            "action":     action,
            "resource":   resource,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.warning(f"Audit log failed (non-critical): {e}")
