from fastapi import APIRouter, HTTPException
from app.services.auditor_service import AuditorService
from app.schemas.auditor import AuditRequest, AuditResponse

router = APIRouter()
auditor_service = AuditorService()

@router.post("/audit", response_model=AuditResponse)
async def run_brand_audit(request: AuditRequest):
    try:
        result = await auditor_service.audit_content(request.content_to_audit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))