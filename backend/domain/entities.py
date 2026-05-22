from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.domain.enums import InterviewType, LifecycleState, ProgressStage


class InterviewEvent(BaseModel):
    id: str
    datetime: datetime
    with_whom: str = ""
    interview_type: InterviewType = InterviewType.OTHER
    notes: str = ""


class Job(BaseModel):
    job_id: str
    company: str = ""
    position: str = ""
    published: str = ""
    applicant_count: str | None = None
    location: str = ""
    work_type: str = ""
    salary: str | None = None
    url: str = ""
    description: str = ""
    easy_apply: bool = False
    already_applied: bool | None = None
    match_score: float | None = None
    lifecycle_status: LifecycleState | None = None
    progress_stage: ProgressStage | None = None


class PipelineJob(BaseModel):
    job_id: str
    company: str = ""
    position: str = ""
    published: str = ""
    applicant_count: str | None = None
    location: str = ""
    work_type: str = ""
    salary: str | None = None
    url: str = ""
    description: str = ""
    easy_apply: bool = False
    already_applied: bool | None = None
    match_score: float | None = None
    lifecycle_status: LifecycleState | None = None
    progress_stage: ProgressStage | None = None
    submitted_at: datetime | None = None
    interviews: list[InterviewEvent] = Field(default_factory=list)
    last_search_run_id: str | None = None


class ProfileSnapshot(BaseModel):
    headline: str = ""
    location: str = ""
    skills: list[str] = Field(default_factory=list)
    experience_titles: list[str] = Field(default_factory=list)
    preferred_work_types: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class SavedSearch(BaseModel):
    id: str
    name: str = ""
    filters: dict[str, Any] = Field(default_factory=dict)
    profile_snapshot: ProfileSnapshot
    created_at: datetime
