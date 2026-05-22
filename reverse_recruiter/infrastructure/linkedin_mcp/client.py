import json
import logging
import uuid
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class McpClientError(Exception):
    def __init__(self, message: str, code: str = "mcp_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


def _transport_error(exc: httpx.RequestError, url: str) -> McpClientError:
    logger.error(
        "MCP request failed url=%s error=%s",
        url,
        exc,
        exc_info=True,
    )
    return McpClientError(
        f"MCP server unreachable at {url}. "
        "Ensure LinkedIn MCP is running and MCP_BASE_URL is correct.",
        code="mcp_unavailable",
    )


class McpHttpClient:
    """JSON-RPC client for MCP Streamable HTTP transport."""

    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session_id: str | None = None

    async def _initialize(self, client: httpx.AsyncClient) -> None:
        logger.info("MCP initialize url=%s", self._base_url)
        try:
            resp = await client.post(
                self._base_url,
                json={
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "reverse-recruiter", "version": "1.0"},
                    },
                },
                headers={"Accept": "application/json, text/event-stream"},
            )
        except httpx.RequestError as exc:
            raise _transport_error(exc, self._base_url) from exc
        logger.info("MCP initialize status=%s", resp.status_code)
        if resp.status_code >= 400:
            logger.error(
                "MCP initialize failed status=%s body=%s",
                resp.status_code,
                resp.text[:500],
            )
            raise McpClientError(f"MCP initialize failed: {resp.status_code}")
        self._session_id = resp.headers.get("mcp-session-id")

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            if not self._session_id:
                await self._initialize(client)
            headers = {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            }
            if self._session_id:
                headers["mcp-session-id"] = self._session_id
            logger.info(
                "MCP tools/call url=%s tool=%s args_keys=%s",
                self._base_url,
                name,
                sorted(arguments.keys()),
            )
            try:
                resp = await client.post(
                    self._base_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": str(uuid.uuid4()),
                        "method": "tools/call",
                        "params": {"name": name, "arguments": arguments},
                    },
                    headers=headers,
                )
            except httpx.RequestError as exc:
                raise _transport_error(exc, self._base_url) from exc
            logger.info("MCP tools/call tool=%s status=%s", name, resp.status_code)
            if resp.status_code >= 400:
                logger.error(
                    "MCP tool call failed tool=%s status=%s body=%s",
                    name,
                    resp.status_code,
                    resp.text[:500],
                )
                raise McpClientError(f"MCP tool call failed: {resp.status_code}")
            return _parse_mcp_response(resp)

    async def ping(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url.rsplit('/', 1)[0]}/health")
                return resp.status_code < 500
        except Exception:
            return False


def _parse_mcp_response(resp: httpx.Response) -> Any:
    content_type = resp.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        return _parse_sse(resp.text)
    data = resp.json()
    if "error" in data:
        err = data["error"]
        raise McpClientError(err.get("message", "MCP error"), code=str(err.get("code", "mcp_error")))
    result = data.get("result", data)
    if isinstance(result, dict) and "content" in result:
        texts = [
            c.get("text", "")
            for c in result["content"]
            if c.get("type") == "text"
        ]
        combined = "\n".join(texts)
        try:
            return json.loads(combined)
        except json.JSONDecodeError:
            return combined
    return result


def _parse_sse(body: str) -> Any:
    for line in body.splitlines():
        if line.startswith("data: "):
            payload = line[6:]
            try:
                data = json.loads(payload)
                if "result" in data:
                    return _parse_mcp_response_result(data["result"])
                if "error" in data:
                    err = data["error"]
                    raise McpClientError(err.get("message", "MCP error"))
            except json.JSONDecodeError:
                continue
    raise McpClientError("No valid SSE data in MCP response")


def _parse_mcp_response_result(result: Any) -> Any:
    if isinstance(result, dict) and "content" in result:
        texts = [c.get("text", "") for c in result["content"] if c.get("type") == "text"]
        combined = "\n".join(texts)
        try:
            return json.loads(combined)
        except json.JSONDecodeError:
            return combined
    return result
