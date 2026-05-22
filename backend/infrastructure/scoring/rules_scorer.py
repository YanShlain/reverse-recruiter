import re

from backend.domain.entities import Job, ProfileSnapshot
from backend.domain.gateways import IMatchScorer


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9+#]+", text) if len(t) > 2}


class RulesMatchScorer:
    async def score(self, profile: ProfileSnapshot, job: Job) -> float:
        score = 0.0
        title_tokens = _tokenize(job.position)
        profile_tokens = _tokenize(
            " ".join(profile.experience_titles + [profile.headline])
        )
        skill_tokens = {s.lower() for s in profile.skills}
        keyword_tokens = _tokenize(job.description)

        if title_tokens and profile_tokens:
            overlap = len(title_tokens & profile_tokens) / len(title_tokens)
            score += overlap * 40

        if skill_tokens and keyword_tokens:
            skill_overlap = len(skill_tokens & keyword_tokens) / max(len(skill_tokens), 1)
            score += skill_overlap * 25

        if profile.location and job.location:
            pl, jl = profile.location.lower(), job.location.lower()
            if pl in jl or jl in pl or "remote" in jl:
                score += 15

        if profile.preferred_work_types and job.work_type:
            jw = job.work_type.lower()
            if any(p.lower() in jw for p in profile.preferred_work_types):
                score += 10

        if job.easy_apply:
            score += 5

        return min(round(score, 1), 100.0)
