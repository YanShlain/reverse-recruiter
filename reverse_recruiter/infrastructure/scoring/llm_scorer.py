import os

import httpx

from reverse_recruiter.domain.entities import Job, ProfileSnapshot
from reverse_recruiter.infrastructure.scoring.rules_scorer import RulesMatchScorer


class LlmMatchScorer:
    def __init__(self, rules: RulesMatchScorer | None = None) -> None:
        self._rules = rules or RulesMatchScorer()
        self._api_key = os.getenv("LLM_API_KEY", "")
        self._model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def score(self, profile: ProfileSnapshot, job: Job) -> float:
        if not self._api_key:
            return await self._rules.score(profile, job)
        prompt = (
            f"Rate job fit 0-100. Profile: {profile.headline}, skills: {profile.skills[:10]}. "
            f"Job: {job.position} at {job.company}, {job.location}. Reply with number only."
        )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self._model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 10,
                    },
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"].strip()
                return min(max(float(text.split()[0]), 0.0), 100.0)
        except Exception:
            return await self._rules.score(profile, job)
