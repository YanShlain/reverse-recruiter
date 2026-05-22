import asyncio
from pathlib import Path
from uuid import uuid4

from reverse_recruiter.domain.entities import SavedSearch
from reverse_recruiter.infrastructure.json.atomic import read_json, write_json_atomic


class JsonSavedSearchStore:
    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "saved_searches.json"
        self._lock = asyncio.Lock()

    async def _read_list(self) -> list[dict]:
        async with self._lock:
            return read_json(self._path, [])

    async def _write_list(self, data: list[dict]) -> None:
        async with self._lock:
            write_json_atomic(self._path, data)

    async def list(self) -> list[SavedSearch]:
        rows = await self._read_list()
        return [SavedSearch.model_validate(r) for r in rows]

    async def save(self, saved: SavedSearch) -> SavedSearch:
        rows = await self._read_list()
        if not saved.id:
            saved.id = str(uuid4())
        payload = saved.model_dump(mode="json")
        idx = next((i for i, r in enumerate(rows) if r.get("id") == saved.id), None)
        if idx is not None:
            rows[idx] = payload
        else:
            rows.append(payload)
        await self._write_list(rows)
        return saved

    async def get(self, saved_search_id: str) -> SavedSearch | None:
        rows = await self._read_list()
        for row in rows:
            if row.get("id") == saved_search_id:
                return SavedSearch.model_validate(row)
        return None
