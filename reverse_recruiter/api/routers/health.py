from fastapi import APIRouter, Depends

from reverse_recruiter.domain.gateways import ILinkedInGateway
from reverse_recruiter.api.dependencies import get_gateway

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready(gateway: ILinkedInGateway = Depends(get_gateway)) -> dict:
    mcp_ok = await gateway.ping()
    return {"status": "ok", "mcp": mcp_ok}
