import pytest

from backend.infrastructure.linkedin_mcp.client import McpClientError, McpHttpClient


@pytest.mark.asyncio
async def test_call_tool_maps_connect_error_to_mcp_unavailable():
    client = McpHttpClient("http://127.0.0.1:1/mcp", timeout=1.0)
    with pytest.raises(McpClientError) as exc_info:
        await client.call_tool("get_my_profile", {})
    err = exc_info.value
    assert err.code == "mcp_unavailable"
    assert "127.0.0.1:1" in err.message
