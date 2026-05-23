"""One-off MCP verification: initialize + get_my_profile."""
import asyncio
import os
import sys

from backend.infrastructure.linkedin_mcp.client import McpClientError, McpHttpClient


async def main() -> int:
    base = os.getenv("MCP_BASE_URL", "http://127.0.0.1:3000/mcp")
    print(f"MCP_BASE_URL={base}")

    client = McpHttpClient(base, timeout=120.0)
    ping_ok = await client.ping()
    print(f"ping (/health): {ping_ok}")

    try:
        raw = await client.call_tool("get_my_profile", {"sections": "experience,skills"})
        print("get_my_profile: OK")
        if isinstance(raw, dict):
            for key in ("headline", "name", "location", "skills"):
                if key in raw:
                    val = raw[key]
                    if key == "skills" and isinstance(val, list):
                        print(f"  {key}: {val[:5]}...")
                    else:
                        print(f"  {key}: {str(val)[:120]}")
        else:
            print(f"  raw type={type(raw).__name__}: {str(raw)[:300]}")
        return 0
    except McpClientError as e:
        print(f"get_my_profile FAILED code={e.code} message={e.message}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
