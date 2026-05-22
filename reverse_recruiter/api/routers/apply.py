from fastapi import APIRouter, HTTPException

from reverse_recruiter.api.dependencies import get_pipeline_service
from reverse_recruiter.api.models import ApplyRequest, ApplyResponse
from reverse_recruiter.services.pipeline_service import PipelineServiceError

router = APIRouter(tags=["apply"])


@router.post("/apply", response_model=ApplyResponse)
async def apply(body: ApplyRequest) -> ApplyResponse:
    svc = get_pipeline_service()
    try:
        jobs = await svc.mark_in_progress(body.job_ids)
        return ApplyResponse(jobs=jobs)
    except PipelineServiceError as e:
        raise HTTPException(status_code=404, detail={"error": e.code, "message": e.message}) from e
