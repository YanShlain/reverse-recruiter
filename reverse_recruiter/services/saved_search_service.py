from datetime import datetime, timezone
from uuid import uuid4

from reverse_recruiter.domain.entities import ProfileSnapshot, SavedSearch
from reverse_recruiter.domain.gateways import ILinkedInGateway
from reverse_recruiter.domain.repositories import ISavedSearchStore


class SavedSearchService:
    def __init__(
        self, saved_store: ISavedSearchStore, gateway: ILinkedInGateway
    ) -> None:
        self._saved = saved_store
        self._gateway = gateway

    async def list(self) -> list[SavedSearch]:
        return await self._saved.list()

    async def save(
        self, name: str, filters: dict, profile: ProfileSnapshot | None = None
    ) -> SavedSearch:
        prof = profile or await self._gateway.get_my_profile()
        saved = SavedSearch(
            id=str(uuid4()),
            name=name or filters.get("keywords", "Saved search"),
            filters=filters,
            profile_snapshot=prof,
            created_at=datetime.now(timezone.utc),
        )
        return await self._saved.save(saved)
