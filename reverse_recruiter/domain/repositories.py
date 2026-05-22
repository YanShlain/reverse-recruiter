from typing import Protocol

from reverse_recruiter.domain.entities import Job, PipelineJob, ProfileSnapshot, SavedSearch


class IJobStore(Protocol):
    async def get_by_job_id(self, job_id: str) -> PipelineJob | None: ...

    async def list_by_lifecycle(
        self, state: str | None = None, include_rejected: bool = False
    ) -> list[PipelineJob]: ...

    async def upsert_pipeline(self, job: PipelineJob) -> None: ...

    async def merge_search_snapshot(
        self, jobs: list[Job], search_run_id: str
    ) -> list[Job]: ...


class ISavedSearchStore(Protocol):
    async def list(self) -> list[SavedSearch]: ...

    async def save(self, saved: SavedSearch) -> SavedSearch: ...

    async def get(self, saved_search_id: str) -> SavedSearch | None: ...
