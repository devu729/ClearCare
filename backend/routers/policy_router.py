from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from security.auth_guard import require_clinician, AuthUser
from security.audit_logger import log_action
from agents.policy_parser import parse_policy_pdf, list_docs

router = APIRouter(prefix="/api/policy", tags=["Policy"])


@router.post("/upload")
async def upload_policy(
    request: Request,
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_clinician),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Max file size is 20MB.")

    await log_action("pdf_upload", user_id=user.user_id, resource=file.filename,
                     ip_address=request.client.host if request.client else None)

    result = await parse_policy_pdf(data, file.filename or "policy.pdf", user.user_id)

    await log_action(
        "policy_parse_complete" if result["status"] == "success" else "policy_parse_failed",
        user_id=user.user_id, resource=result.get("document_id"),
    )
    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["message"])
    return JSONResponse(content=result)


@router.get("/documents")
async def get_documents(user: AuthUser = Depends(require_clinician)):
    return {"documents": list_docs(user.user_id)}
