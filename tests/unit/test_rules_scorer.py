import pytest

from reverse_recruiter.domain.entities import Job, ProfileSnapshot
from reverse_recruiter.infrastructure.scoring.rules_scorer import RulesMatchScorer


@pytest.mark.asyncio
async def test_score_returns_bounded_float():
    profile = ProfileSnapshot(
        headline="Software Engineer",
        location="San Francisco",
        skills=["Python", "FastAPI"],
        experience_titles=["Senior Software Engineer"],
        preferred_work_types=["remote"],
    )
    job = Job(
        job_id="1",
        position="Senior Software Engineer",
        location="Remote",
        work_type="Remote",
        description="Python FastAPI backend role",
        easy_apply=True,
    )
    score = await RulesMatchScorer().score(profile, job)
    assert 0 <= score <= 100
