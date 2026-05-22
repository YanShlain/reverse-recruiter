from enum import StrEnum


class LifecycleState(StrEnum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    SKIPPED = "skipped"
    REJECTED = "rejected"


class ProgressStage(StrEnum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    WITHDRAWN = "withdrawn"


class InterviewType(StrEnum):
    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    OTHER = "other"
