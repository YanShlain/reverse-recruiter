import os
from typing import Any

from backend.domain.entities import Job, ProfileSnapshot
from backend.infrastructure.linkedin_mcp.client import McpClientError, McpHttpClient


def _profile_from_raw(raw: dict[str, Any]) -> ProfileSnapshot:
    skills: list[str] = []
    experience_titles: list[str] = []
    if isinstance(raw.get("skills"), list):
        for s in raw["skills"]:
            if isinstance(s, str):
                skills.append(s)
            elif isinstance(s, dict) and s.get("name"):
                skills.append(str(s["name"]))
    if isinstance(raw.get("experience"), list):
        for exp in raw["experience"]:
            if isinstance(exp, dict) and exp.get("title"):
                experience_titles.append(str(exp["title"]))
    headline = str(raw.get("headline") or raw.get("name") or "")
    location = str(raw.get("location") or "")
    return ProfileSnapshot(
        headline=headline,
        location=location,
        skills=skills,
        experience_titles=experience_titles,
        preferred_work_types=[],
        raw=raw,
    )


def _job_from_raw(job_id: str, raw: dict[str, Any]) -> Job:
    salary = raw.get("salary") or raw.get("salary_range")
    applicants = raw.get("applicant_count") or raw.get("applicants")
    return Job(
        job_id=job_id,
        company=str(raw.get("company") or raw.get("company_name") or ""),
        position=str(raw.get("title") or raw.get("position") or ""),
        published=str(raw.get("posted") or raw.get("published") or raw.get("date_posted") or ""),
        applicant_count=str(applicants) if applicants is not None else None,
        location=str(raw.get("location") or ""),
        work_type=str(raw.get("work_type") or raw.get("workplace_type") or ""),
        salary=str(salary) if salary else None,
        url=str(raw.get("url") or raw.get("job_url") or f"https://www.linkedin.com/jobs/view/{job_id}"),
        description=str(raw.get("description") or ""),
        easy_apply=bool(raw.get("easy_apply")),
        already_applied=raw.get("already_applied") if "already_applied" in raw else None,
    )


class McpLinkedInGateway:
    def __init__(self, base_url: str | None = None) -> None:
        url = base_url or os.getenv("MCP_BASE_URL", "http://linkedin-mcp:3000/mcp")
        self._client = McpHttpClient(url)

    async def ensure_session(self) -> None:
        await self.get_my_profile()

    async def get_my_profile(self) -> ProfileSnapshot:
        try:
            raw = await self._client.call_tool(
                "get_my_profile", {"sections": "experience,skills"}
            )
        except McpClientError as e:
            if "session" in e.message.lower() or "auth" in e.message.lower():
                raise McpClientError(
                    "LinkedIn session expired; re-authenticate via MCP",
                    code="session_expired",
                ) from e
            raise
        if isinstance(raw, dict):
            return _profile_from_raw(raw)
        return ProfileSnapshot()

    async def search_jobs(self, filters: dict) -> list[str]:
        args = {k: v for k, v in filters.items() if v is not None and k != "use_llm"}
        args.setdefault("max_pages", 1)
        result = await self._client.call_tool("search_jobs", args)
        if isinstance(result, dict):
            ids = result.get("job_ids") or result.get("jobs") or []
            if ids and isinstance(ids[0], dict):
                return [str(j.get("job_id") or j.get("id")) for j in ids]
            return [str(i) for i in ids]
        if isinstance(result, list):
            return [str(x) if not isinstance(x, dict) else str(x.get("job_id", x.get("id", ""))) for x in result]
        return []

    async def get_job_details(self, job_id: str) -> Job:
        raw = await self._client.call_tool("get_job_details", {"job_id": job_id})
        if isinstance(raw, dict):
            return _job_from_raw(job_id, raw)
        return Job(job_id=job_id)

    async def ping(self) -> bool:
        return await self._client.ping()


class MockLinkedInGateway:
    """Development gateway when MCP is unavailable."""

    _JOB_IDS = ["1001", "1002", "1003", "1004", "1005"]

    async def ensure_session(self) -> None:
        return

    async def get_my_profile(self) -> ProfileSnapshot:
        return ProfileSnapshot(
            headline="Software Engineer",
            location="San Francisco, CA",
            skills=["Python", "FastAPI", "React", "TypeScript"],
            experience_titles=["Senior Software Engineer", "Backend Developer"],
            preferred_work_types=["remote", "hybrid"],
        )

    async def search_jobs(self, filters: dict) -> list[str]:
        return self._JOB_IDS

    async def get_job_details(self, job_id: str) -> Job:
        keywords = "engineer"
        idx = self._JOB_IDS.index(job_id) if job_id in self._JOB_IDS else 0
        companies = ["Acme Corp", "TechStart", "BigCo", "StartupXYZ", "CloudNine"]
        return Job(
            job_id=job_id,
            company=companies[idx % len(companies)],
            position=f"{keywords.title()} — Role {job_id}",
            published="2 days ago",
            applicant_count="47 applicants",
            location="Remote",
            work_type="Remote",
            salary="$120,000 - $160,000" if idx % 2 == 0 else None,
            url=f"https://www.linkedin.com/jobs/view/{job_id}",
            description=f"Looking for a {keywords} with Python and API experience.",
            easy_apply=idx % 3 == 0,
        )

    async def ping(self) -> bool:
        return True
