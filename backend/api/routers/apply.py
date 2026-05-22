from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_pipeline_service
from backend.api.models import ApplyRequest, ApplyResponse
from backend.services.pipeline_service import PipelineService, PipelineServiceError

router = APIRouter(tags=["apply"])


@router.post("/apply", response_model=ApplyResponse)
async def apply(
    body: ApplyRequest,
    svc: PipelineService = Depends(get_pipeline_service),
) -> ApplyResponse:
    try:
        jobs = await svc.mark_in_progress(body.job_ids)
        return ApplyResponse(jobs=jobs)
    except PipelineServiceError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": e.code, "message": e.message},
        ) from e
