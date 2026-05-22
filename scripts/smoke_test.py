import asyncio
import os

os.environ.setdefault("MOCK_MCP", "true")
os.environ.setdefault("DATA_DIR", "data")

from backend.api.dependencies import get_search_service


async def main() -> None:
    jobs = await get_search_service(False).run_search({"keywords": "engineer"})
    print(f"ok: {len(jobs)} jobs, top score {jobs[0].match_score}")


if __name__ == "__main__":
    asyncio.run(main())
