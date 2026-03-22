from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from security.auth_guard import require_auth, AuthUser
from security.audit_logger import log_action
from agents.mcp_agent import send_explanation_email, create_calendar_event

router = APIRouter(prefix="/api/mcp", tags=["MCP"])


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class CalendarRequest(BaseModel):
    title: str
    date:  str
    notes: str = ""


@router.post("/email")
async def send_email(body: EmailRequest, request: Request, user: AuthUser = Depends(require_auth)):
    if not body.to or "@" not in body.to:
        raise HTTPException(status_code=400, detail="Valid email address required.")
    try:
        result = await send_explanation_email(body.to, body.subject, body.body)
        await log_action("email_sent", user_id=user.user_id, resource=body.to,
                         ip_address=request.client.host if request.client else None)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar")
async def create_event(body: CalendarRequest, request: Request, user: AuthUser = Depends(require_auth)):
    if not body.title or not body.date:
        raise HTTPException(status_code=400, detail="Title and date required.")
    try:
        result = await create_calendar_event(body.title, body.date, body.notes)
        await log_action("calendar_event_created", user_id=user.user_id, resource=body.title,
                         ip_address=request.client.host if request.client else None)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
