from fastapi import APIRouter, HTTPException

from reverse_recruiter.api.dependencies import get_gateway
from reverse_recruiter.infrastructure.linkedin_mcp.client import McpClientError

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/ensure")
async def ensure_session() -> dict:
    try:
        await get_gateway().ensure_session()
        return {"status": "ok"}
    except McpClientError as e:
        raise HTTPException(
            status_code=401,
            detail={"error": "session_expired", "message": e.message},
        ) from e
