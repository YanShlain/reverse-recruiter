import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    mcp_base_url: str = os.getenv("MCP_BASE_URL", "http://linkedin-mcp:3000/mcp")
    mock_mcp: bool = os.getenv("MOCK_MCP", "false").lower() in ("1", "true", "yes")
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]
    log_level: str = os.getenv("LOG_LEVEL", "info")


settings = Settings()
