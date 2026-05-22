from backend.api.dependencies import get_gateway
from backend.infrastructure.linkedin_mcp.gateway import McpLinkedInGateway
from backend.main import app


def test_session_ensure_mcp_unavailable(client):
    app.dependency_overrides[get_gateway] = lambda: McpLinkedInGateway(
        "http://127.0.0.1:1/mcp"
    )
    try:
        resp = client.post("/api/v1/session/ensure")
    finally:
        app.dependency_overrides.pop(get_gateway, None)
    assert resp.status_code == 503
    body = resp.json()
    assert body["detail"]["error"] == "mcp_unavailable"
    assert "127.0.0.1:1" in body["detail"]["message"]
