import asyncio
from pathlib import Path

from reverse_recruiter.infrastructure.json.atomic import read_json, write_json_atomic


class JsonSettingsStore:
    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "settings.json"
        self._lock = asyncio.Lock()

    async def get(self) -> dict:
        async with self._lock:
            return read_json(self._path, {"use_llm_scoring": False})

    async def update(self, patch: dict) -> dict:
        async with self._lock:
            current = read_json(self._path, {"use_llm_scoring": False})
            current.update(patch)
            write_json_atomic(self._path, current)
            return current
