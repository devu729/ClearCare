from fastapi import APIRouter, Depends, HTTPException
from security.auth_guard import require_auth, AuthUser
from supabase import create_client
from config import get_settings

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs")
async def get_audit_logs(limit: int = 100, user: AuthUser = Depends(require_auth)):
    try:
        s = get_settings()
        client = create_client(s.supabase_url, s.supabase_service_key)
        resp = (
            client.table("audit_logs")
            .select("*")
            .eq("user_id", user.user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"logs": resp.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
