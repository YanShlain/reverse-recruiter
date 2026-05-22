from fastapi import APIRouter, Depends, HTTPException

from reverse_recruiter.api.dependencies import (
    get_saved_search_service,
    get_search_service,
    get_settings_store,
)
from reverse_recruiter.api.models import (
    JobRow,
    SavedSearchCreateRequest,
    SearchRequest,
    SettingsResponse,
)
from reverse_recruiter.domain.entities import Job
from reverse_recruiter.infrastructure.json.settings_store import JsonSettingsStore
from reverse_recruiter.services.saved_search_service import SavedSearchService
from reverse_recruiter.services.search_service import SearchService, SearchServiceError

router = APIRouter(prefix="/search", tags=["search"])


def _to_row(job: Job) -> JobRow:
    dimmed = job.lifecycle_status is not None
    return JobRow(
        job_id=job.job_id,
        company=job.company,
        position=job.position,
        published=job.published,
        applicant_count=job.applicant_count,
        match_score=job.match_score,
        location=job.location,
        work_type=job.work_type,
        salary=job.salary or "—",
        url=job.url,
        lifecycle_status=job.lifecycle_status.value if job.lifecycle_status else None,
        progress_stage=job.progress_stage.value if job.progress_stage else None,
        already_applied=job.already_applied,
        dimmed=dimmed,
    )


@router.post("/", response_model=list[JobRow])
async def run_search(body: SearchRequest) -> list[JobRow]:
    svc = get_search_service(body.use_llm)
    try:
        jobs = await svc.run_search(
            body.model_dump(exclude={"use_llm"}),
            use_llm=body.use_llm,
        )
        store = get_settings_store()
        await store.update({"use_llm_scoring": body.use_llm})
        return [_to_row(j) for j in jobs]
    except SearchServiceError as e:
        status = 401 if e.code == "session_expired" else 503
        raise HTTPException(
            status_code=status,
            detail={"error": e.code, "message": e.message},
        ) from e


@router.get("/saved")
async def list_saved(
    svc: SavedSearchService = Depends(get_saved_search_service),
) -> list[dict]:
    items = await svc.list()
    return [s.model_dump(mode="json") for s in items]


@router.post("/saved")
async def save_search(
    body: SavedSearchCreateRequest,
    svc: SavedSearchService = Depends(get_saved_search_service),
) -> dict:
    saved = await svc.save(body.name, body.filters)
    return saved.model_dump(mode="json")


@router.post("/saved/{saved_id}/run", response_model=list[JobRow])
async def run_saved(saved_id: str, use_llm: bool = False) -> list[JobRow]:
    svc = get_search_service(use_llm)
    try:
        jobs = await svc.run_saved(saved_id, use_llm=use_llm)
        return [_to_row(j) for j in jobs]
    except SearchServiceError as e:
        status = 401 if e.code == "session_expired" else 503
        raise HTTPException(
            status_code=status,
            detail={"error": e.code, "message": e.message},
        ) from e


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    store: JsonSettingsStore = Depends(get_settings_store),
) -> SettingsResponse:
    data = await store.get()
    return SettingsResponse(use_llm_scoring=data.get("use_llm_scoring", False))
