from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from security.auth_guard import require_clinician, AuthUser
from evals.eval_runner import run_eval_suite

router = APIRouter(prefix="/api/evals", tags=["Evals"])


class EvalRequest(BaseModel):
    document_id: str | None = None


@router.post("/run")
async def run_evals(body: EvalRequest, user: AuthUser = Depends(require_clinician)):
    try:
        return await run_eval_suite(document_id=body.document_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
