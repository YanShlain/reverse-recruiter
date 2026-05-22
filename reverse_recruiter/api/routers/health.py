from fastapi import APIRouter

from reverse_recruiter.api.dependencies import get_gateway

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    gateway = get_gateway()
    mcp_ok = await gateway.ping()
    return {"status": "ok", "mcp": mcp_ok}
