from datetime import datetime, timezone
from uuid import uuid4

from reverse_recruiter.domain.entities import Job, PipelineJob, ProfileSnapshot
from reverse_recruiter.domain.gateways import ILinkedInGateway, IMatchScorer
from reverse_recruiter.domain.repositories import IJobStore, ISavedSearchStore
from reverse_recruiter.infrastructure.linkedin_mcp.client import McpClientError
from reverse_recruiter.services.pipeline_service import PipelineService


class SearchServiceError(Exception):
    def __init__(self, message: str, code: str = "search_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class SearchService:
    def __init__(
        self,
        job_store: IJobStore,
        saved_store: ISavedSearchStore,
        gateway: ILinkedInGateway,
        scorer: IMatchScorer,
        pipeline: PipelineService,
    ) -> None:
        self._jobs = job_store
        self._saved = saved_store
        self._gateway = gateway
        self._scorer = scorer
        self._pipeline = pipeline

    async def run_search(
        self, filters: dict, use_llm: bool = False, profile: ProfileSnapshot | None = None
    ) -> list[Job]:
        search_run_id = str(uuid4())
        try:
            await self._gateway.ensure_session()
            prof = profile or await self._gateway.get_my_profile()
            job_ids = await self._gateway.search_jobs(filters)
            results: list[Job] = []
            for job_id in job_ids[:25]:
                job = await self._gateway.get_job_details(job_id)
                job.match_score = await self._scorer.score(prof, job)
                await self._pipeline.upsert_from_search(job.model_dump())
                results.append(job)
            results.sort(key=lambda j: j.match_score or 0, reverse=True)
            return await self._jobs.merge_search_snapshot(results, search_run_id)
        except McpClientError as e:
            if e.code == "session_expired":
                raise SearchServiceError(e.message, code="session_expired") from e
            raise SearchServiceError(e.message, code="mcp_unavailable") from e

    async def run_saved(self, saved_search_id: str, use_llm: bool = False) -> list[Job]:
        saved = await self._saved.get(saved_search_id)
        if not saved:
            raise SearchServiceError("Saved search not found", code="not_found")
        return await self.run_search(
            saved.filters, use_llm=use_llm, profile=saved.profile_snapshot
        )
