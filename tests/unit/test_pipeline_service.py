from datetime import datetime, timezone

import pytest

from backend.domain.entities import PipelineJob
from backend.domain.enums import LifecycleState, ProgressStage
from backend.services.pipeline_service import PipelineService, PipelineServiceError


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, PipelineJob] = {}

    async def get_by_job_id(self, job_id: str) -> PipelineJob | None:
        return self._jobs.get(job_id)

    async def list_by_lifecycle(
        self, state: str | None = None, include_rejected: bool = False
    ) -> list[PipelineJob]:
        jobs = [j for j in self._jobs.values() if j.lifecycle_status]
        if state is None:
            return jobs
        if state == LifecycleState.SUBMITTED.value and include_rejected:
            return [
                j
                for j in jobs
                if j.lifecycle_status
                in (LifecycleState.SUBMITTED, LifecycleState.REJECTED)
            ]
        return [j for j in jobs if j.lifecycle_status and j.lifecycle_status.value == state]

    async def upsert_pipeline(self, job: PipelineJob) -> None:
        self._jobs[job.job_id] = job

    async def merge_search_snapshot(self, jobs, search_run_id: str):
        raise NotImplementedError


@pytest.fixture
def store() -> InMemoryJobStore:
    return InMemoryJobStore()


@pytest.fixture
def svc(store: InMemoryJobStore) -> PipelineService:
    return PipelineService(store)


@pytest.mark.asyncio
async def test_mark_in_progress_sets_lifecycle(svc: PipelineService, store: InMemoryJobStore):
    job = PipelineJob(job_id="j1", url="https://example.com/j1")
    await store.upsert_pipeline(job)
    result = await svc.mark_in_progress(["j1"])
    assert result == [{"job_id": "j1", "url": "https://example.com/j1"}]
    updated = await store.get_by_job_id("j1")
    assert updated is not None
    assert updated.lifecycle_status == LifecycleState.IN_PROGRESS
    assert updated.progress_stage == ProgressStage.APPLIED


@pytest.mark.asyncio
async def test_confirm_submitted(svc: PipelineService, store: InMemoryJobStore):
    job = PipelineJob(
        job_id="j1",
        lifecycle_status=LifecycleState.IN_PROGRESS,
        url="https://example.com/j1",
    )
    await store.upsert_pipeline(job)
    updated = await svc.confirm(["j1"], "submitted")
    assert updated[0].lifecycle_status == LifecycleState.SUBMITTED
    assert updated[0].submitted_at is not None


@pytest.mark.asyncio
async def test_get_details_not_found(svc: PipelineService):
    with pytest.raises(PipelineServiceError) as exc:
        await svc.get_details("missing")
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_update_rejected(svc: PipelineService, store: InMemoryJobStore):
    job = PipelineJob(
        job_id="j1",
        lifecycle_status=LifecycleState.SUBMITTED,
        url="https://example.com/j1",
    )
    await store.upsert_pipeline(job)
    updated = await svc.update("j1", rejected=True)
    assert updated.lifecycle_status == LifecycleState.REJECTED
