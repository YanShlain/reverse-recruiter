from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_pipeline_service
from backend.api.models import (
    ConfirmRequest,
    InterviewCreateRequest,
    InterviewUpdateRequest,
    PipelineUpdateRequest,
)
from backend.domain.enums import InterviewType, LifecycleState, ProgressStage
from backend.services.pipeline_service import PipelineService, PipelineServiceError

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("")
async def list_pipeline(
    lifecycle: str | None = None,
    include_rejected: bool = False,
    svc: PipelineService = Depends(get_pipeline_service),
) -> list[dict]:
    jobs = await svc.list_pipeline(lifecycle, include_rejected)
    return [j.model_dump(mode="json") for j in jobs]


@router.post("/confirm")
async def confirm(
    body: ConfirmRequest,
    svc: PipelineService = Depends(get_pipeline_service),
) -> list[dict]:
    try:
        jobs = await svc.confirm(body.job_ids, body.action)
        return [j.model_dump(mode="json") for j in jobs]
    except PipelineServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": e.code, "message": e.message},
        ) from e


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    svc: PipelineService = Depends(get_pipeline_service),
) -> dict:
    try:
        job = await svc.get_details(job_id)
        return job.model_dump(mode="json")
    except PipelineServiceError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": e.code, "message": e.message},
        ) from e


@router.patch("/{job_id}")
async def update_job(
    job_id: str,
    body: PipelineUpdateRequest,
    svc: PipelineService = Depends(get_pipeline_service),
) -> dict:
    lifecycle = LifecycleState(body.lifecycle_status) if body.lifecycle_status else None
    stage = ProgressStage(body.progress_stage) if body.progress_stage else None
    try:
        job = await svc.update(job_id, lifecycle, stage, body.rejected)
        return job.model_dump(mode="json")
    except PipelineServiceError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": e.code, "message": e.message},
        ) from e


@router.post("/{job_id}/interviews")
async def add_interview(
    job_id: str,
    body: InterviewCreateRequest,
    svc: PipelineService = Depends(get_pipeline_service),
) -> dict:
    try:
        job = await svc.add_interview(
            job_id,
            body.datetime,
            body.with_whom,
            InterviewType(body.interview_type),
            body.notes,
        )
        return job.model_dump(mode="json")
    except PipelineServiceError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": e.code, "message": e.message},
        ) from e


@router.patch("/{job_id}/interviews/{event_id}")
async def update_interview(
    job_id: str,
    event_id: str,
    body: InterviewUpdateRequest,
    svc: PipelineService = Depends(get_pipeline_service),
) -> dict:
    patch = body.model_dump(exclude_none=True)
    if "interview_type" in patch:
        patch["interview_type"] = InterviewType(patch["interview_type"])
    try:
        job = await svc.update_interview(job_id, event_id, patch)
        return job.model_dump(mode="json")
    except PipelineServiceError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": e.code, "message": e.message},
        ) from e


@router.delete("/{job_id}/interviews/{event_id}")
async def delete_interview(
    job_id: str,
    event_id: str,
    svc: PipelineService = Depends(get_pipeline_service),
) -> dict:
    try:
        job = await svc.delete_interview(job_id, event_id)
        return job.model_dump(mode="json")
    except PipelineServiceError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": e.code, "message": e.message},
        ) from e
