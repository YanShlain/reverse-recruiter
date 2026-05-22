import asyncio
from pathlib import Path

from reverse_recruiter.domain.entities import Job, PipelineJob
from reverse_recruiter.domain.enums import LifecycleState
from reverse_recruiter.infrastructure.json.atomic import read_json, write_json_atomic


class JsonJobStore:
    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "pipeline_jobs.json"
        self._lock = asyncio.Lock()

    async def _read_map(self) -> dict[str, dict]:
        async with self._lock:
            return read_json(self._path, {})

    async def _write_map(self, data: dict[str, dict]) -> None:
        async with self._lock:
            write_json_atomic(self._path, data)

    async def get_by_job_id(self, job_id: str) -> PipelineJob | None:
        data = await self._read_map()
        row = data.get(job_id)
        return PipelineJob.model_validate(row) if row else None

    async def list_by_lifecycle(
        self, state: str | None = None, include_rejected: bool = False
    ) -> list[PipelineJob]:
        data = await self._read_map()
        jobs = [
            PipelineJob.model_validate(v)
            for v in data.values()
            if v.get("lifecycle_status")
        ]
        if state is None:
            return sorted(jobs, key=lambda j: j.position)
        if state == LifecycleState.SUBMITTED.value and include_rejected:
            return [
                j
                for j in jobs
                if j.lifecycle_status
                in (LifecycleState.SUBMITTED, LifecycleState.REJECTED)
            ]
        return [j for j in jobs if j.lifecycle_status and j.lifecycle_status.value == state]

    async def upsert_pipeline(self, job: PipelineJob) -> None:
        data = await self._read_map()
        data[job.job_id] = job.model_dump(mode="json")
        await self._write_map(data)

    async def merge_search_snapshot(
        self, jobs: list[Job], search_run_id: str
    ) -> list[Job]:
        data = await self._read_map()
        merged: list[Job] = []
        for job in jobs:
            existing = data.get(job.job_id)
            if existing:
                pj = PipelineJob.model_validate(existing)
                job.lifecycle_status = pj.lifecycle_status
                job.progress_stage = pj.progress_stage
                pj.last_search_run_id = search_run_id
                pj.match_score = job.match_score
                data[job.job_id] = pj.model_dump(mode="json")
            merged.append(job)
        await self._write_map(data)
        return merged
