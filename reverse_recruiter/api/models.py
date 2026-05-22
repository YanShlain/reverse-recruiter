from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Any | None = None


class SearchRequest(BaseModel):
    keywords: str
    location: str | None = None
    date_posted: str | None = None
    job_type: str | None = None
    experience_level: str | None = None
    work_type: str | None = None
    easy_apply: bool = False
    sort_by: str | None = None
    max_pages: int = 1
    use_llm: bool = False


class JobRow(BaseModel):
    job_id: str
    company: str
    position: str
    published: str
    applicant_count: str | None = None
    match_score: float | None = None
    location: str
    work_type: str
    salary: str | None = None
    url: str
    lifecycle_status: str | None = None
    progress_stage: str | None = None
    already_applied: bool | None = None
    dimmed: bool = False


class ApplyRequest(BaseModel):
    job_ids: list[str] = Field(min_length=1)


class ApplyResponse(BaseModel):
    jobs: list[dict]


class ConfirmRequest(BaseModel):
    job_ids: list[str] = Field(min_length=1)
    action: str


class PipelineUpdateRequest(BaseModel):
    lifecycle_status: str | None = None
    progress_stage: str | None = None
    rejected: bool | None = None


class InterviewCreateRequest(BaseModel):
    datetime: datetime
    with_whom: str = ""
    interview_type: str = "other"
    notes: str = ""


class InterviewUpdateRequest(BaseModel):
    datetime: datetime | None = None
    with_whom: str | None = None
    interview_type: str | None = None
    notes: str | None = None


class SavedSearchCreateRequest(BaseModel):
    name: str = ""
    filters: dict[str, Any]


class SettingsResponse(BaseModel):
    use_llm_scoring: bool = False
