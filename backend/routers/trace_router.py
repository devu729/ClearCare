from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from security.auth_guard import require_auth, AuthUser
from security.audit_logger import log_action
from agents.decision_tracer import trace_denial

router = APIRouter(prefix="/api/trace", tags=["Denial Tracer"])


class TraceRequest(BaseModel):
    query:           str
    document_id:     str | None = None
    generate_appeal: bool       = False
    patient_name:    str | None = None


@router.post("/denial")
async def trace_denial_endpoint(
    body: TraceRequest,
    request: Request,
    user: AuthUser = Depends(require_auth),
):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    await log_action("denial_trace", user_id=user.user_id, resource=body.document_id,
                     ip_address=request.client.host if request.client else None)

    try:
        result = await trace_denial(
            query=body.query,
            document_id=body.document_id,
            generate_appeal=body.generate_appeal,
            patient_name=body.patient_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if body.generate_appeal and result.get("appeal_letter"):
        await log_action("appeal_draft", user_id=user.user_id)

    return result
