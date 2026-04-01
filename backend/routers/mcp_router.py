from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from security.auth_guard import require_auth, AuthUser
from security.audit_logger import log_action
from agents.mcp_agent import send_explanation_email, create_calendar_event

router = APIRouter(prefix="/api/mcp", tags=["MCP"])


class EmailRequest(BaseModel):
    to:           str
    subject:      str
    body:         str
    sender_email: str | None = None  # User's Gmail for Token Vault


class CalendarRequest(BaseModel):
    title: str
    date:  str
    notes: str = ""


@router.post("/email")
async def send_email(
    body: EmailRequest,
    request: Request,
    user: AuthUser = Depends(require_auth),
):
    if not body.to or "@" not in body.to:
        raise HTTPException(status_code=400, detail="Valid email address required.")

    # Extract Auth0 token from Authorization header for Token Vault
    auth_header = request.headers.get("Authorization", "")
    user_access_token = auth_header.replace("Bearer ", "") if auth_header else None

    try:
        result = await send_explanation_email(
            to=body.to,
            subject=body.subject,
            body=body.body,
            user_access_token=user_access_token,
            sender_email=body.sender_email,
        )
        await log_action(
            "email_sent",
            user_id=user.user_id,
            resource=body.to,
            ip_address=request.client.host if request.client else None,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar")
async def create_event(
    body: CalendarRequest,
    request: Request,
    user: AuthUser = Depends(require_auth),
):
    if not body.title or not body.date:
        raise HTTPException(status_code=400, detail="Title and date required.")

    # Extract Auth0 token for Token Vault
    auth_header = request.headers.get("Authorization", "")
    user_access_token = auth_header.replace("Bearer ", "") if auth_header else None

    try:
        result = await create_calendar_event(
            title=body.title,
            date=body.date,
            notes=body.notes,
            user_access_token=user_access_token,
        )
        await log_action(
            "calendar_event_created",
            user_id=user.user_id,
            resource=body.title,
            ip_address=request.client.host if request.client else None,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))