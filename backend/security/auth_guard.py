"""Validates Supabase JWT tokens on every protected FastAPI route."""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
from config import get_settings
import logging

logger = logging.getLogger(__name__)
bearer = HTTPBearer()


class AuthUser:
    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email   = email
        self.role    = role


async def require_auth(
    creds: HTTPAuthorizationCredentials = Security(bearer),
) -> AuthUser:
    s = get_settings()
    try:
        client = create_client(s.supabase_url, s.supabase_service_key)
        resp = client.auth.get_user(creds.credentials)
        user = resp.user
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
        return AuthUser(
            user_id=str(user.id),
            email=user.email or "",
            role=user.user_metadata.get("role", "patient"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Auth error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")


async def require_clinician(user: AuthUser = Security(require_auth)) -> AuthUser:
    if user.role != "clinician":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinician access required.")
    return user
