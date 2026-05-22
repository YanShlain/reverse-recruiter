from datetime import datetime, timezone
from uuid import uuid4

from reverse_recruiter.domain.entities import InterviewEvent, PipelineJob
from reverse_recruiter.domain.enums import InterviewType, LifecycleState, ProgressStage
from reverse_recruiter.domain.repositories import IJobStore


class PipelineServiceError(Exception):
    def __init__(self, message: str, code: str = "pipeline_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class PipelineService:
    def __init__(self, job_store: IJobStore) -> None:
        self._jobs = job_store

    async def list_pipeline(
        self, lifecycle: str | None = None, include_rejected: bool = False
    ) -> list[PipelineJob]:
        return await self._jobs.list_by_lifecycle(lifecycle, include_rejected)

    async def get_details(self, job_id: str) -> PipelineJob:
        job = await self._jobs.get_by_job_id(job_id)
        if not job:
            raise PipelineServiceError("Job not found", code="not_found")
        return job

    async def mark_in_progress(self, job_ids: list[str]) -> list[dict]:
        urls: list[dict] = []
        for job_id in job_ids:
            job = await self._jobs.get_by_job_id(job_id)
            if not job:
                raise PipelineServiceError(f"Job {job_id} not found", code="not_found")
            if job.lifecycle_status in (
                LifecycleState.SUBMITTED,
                LifecycleState.SKIPPED,
                LifecycleState.REJECTED,
            ):
                urls.append({"job_id": job_id, "url": job.url, "dimmed": True})
                continue
            job.lifecycle_status = LifecycleState.IN_PROGRESS
            if not job.progress_stage:
                job.progress_stage = ProgressStage.APPLIED
            await self._jobs.upsert_pipeline(job)
            urls.append({"job_id": job_id, "url": job.url})
        return urls

    async def confirm(
        self, job_ids: list[str], action: str
    ) -> list[PipelineJob]:
        if action not in ("submitted", "skipped"):
            raise PipelineServiceError("Invalid action", code="invalid_action")
        updated: list[PipelineJob] = []
        for job_id in job_ids:
            job = await self._jobs.get_by_job_id(job_id)
            if not job:
                continue
            if action == "submitted":
                job.lifecycle_status = LifecycleState.SUBMITTED
                job.submitted_at = datetime.now(timezone.utc)
            else:
                job.lifecycle_status = LifecycleState.SKIPPED
            await self._jobs.upsert_pipeline(job)
            updated.append(job)
        return updated

    async def update(
        self,
        job_id: str,
        lifecycle_status: LifecycleState | None = None,
        progress_stage: ProgressStage | None = None,
        rejected: bool | None = None,
    ) -> PipelineJob:
        job = await self._jobs.get_by_job_id(job_id)
        if not job:
            raise PipelineServiceError("Job not found", code="not_found")
        if lifecycle_status is not None:
            job.lifecycle_status = lifecycle_status
            if lifecycle_status == LifecycleState.SUBMITTED and not job.submitted_at:
                job.submitted_at = datetime.now(timezone.utc)
        if progress_stage is not None:
            job.progress_stage = progress_stage
        if rejected:
            job.lifecycle_status = LifecycleState.REJECTED
        await self._jobs.upsert_pipeline(job)
        return job

    async def add_interview(
        self,
        job_id: str,
        dt: datetime,
        with_whom: str,
        interview_type: InterviewType,
        notes: str,
    ) -> PipelineJob:
        job = await self._jobs.get_by_job_id(job_id)
        if not job:
            raise PipelineServiceError("Job not found", code="not_found")
        event = InterviewEvent(
            id=str(uuid4()),
            datetime=dt,
            with_whom=with_whom,
            interview_type=interview_type,
            notes=notes,
        )
        job.interviews.append(event)
        await self._jobs.upsert_pipeline(job)
        return job

    async def update_interview(
        self, job_id: str, event_id: str, patch: dict
    ) -> PipelineJob:
        job = await self._jobs.get_by_job_id(job_id)
        if not job:
            raise PipelineServiceError("Job not found", code="not_found")
        for ev in job.interviews:
            if ev.id == event_id:
                if "datetime" in patch:
                    ev.datetime = patch["datetime"]
                if "with_whom" in patch:
                    ev.with_whom = patch["with_whom"]
                if "interview_type" in patch:
                    ev.interview_type = patch["interview_type"]
                if "notes" in patch:
                    ev.notes = patch["notes"]
                break
        else:
            raise PipelineServiceError("Interview not found", code="not_found")
        await self._jobs.upsert_pipeline(job)
        return job

    async def delete_interview(self, job_id: str, event_id: str) -> PipelineJob:
        job = await self._jobs.get_by_job_id(job_id)
        if not job:
            raise PipelineServiceError("Job not found", code="not_found")
        job.interviews = [e for e in job.interviews if e.id != event_id]
        await self._jobs.upsert_pipeline(job)
        return job

    async def upsert_from_search(self, job_data: dict) -> PipelineJob:
        existing = await self._jobs.get_by_job_id(job_data["job_id"])
        if existing:
            for key in ("company", "position", "published", "location", "work_type", "salary", "url", "match_score"):
                if job_data.get(key) is not None:
                    setattr(existing, key, job_data[key])
            await self._jobs.upsert_pipeline(existing)
            return existing
        pj = PipelineJob(**job_data)
        await self._jobs.upsert_pipeline(pj)
        return pj
