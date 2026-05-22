import logging

from fastapi import APIRouter, Depends, HTTPException

from reverse_recruiter.api.dependencies import get_gateway
from reverse_recruiter.domain.gateways import ILinkedInGateway
from reverse_recruiter.infrastructure.linkedin_mcp.client import McpClientError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/ensure")
async def ensure_session(
    gateway: ILinkedInGateway = Depends(get_gateway),
) -> dict:
    try:
        await gateway.ensure_session()
        return {"status": "ok"}
    except McpClientError as e:
        logger.error("ensure_session failed: %s", e.message, exc_info=True)
        raise HTTPException(
            status_code=401,
            detail={"error": "session_expired", "message": e.message},
        ) from e
