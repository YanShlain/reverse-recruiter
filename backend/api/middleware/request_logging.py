import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every inbound HTTP API request and response at the presentation boundary."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # --- Record request ---
        start = time.perf_counter()
        path = request.url.path
        method = request.method
        query = request.url.query
        logger.info(
            "API request method=%s path=%s query=%s",
            method,
            path,
            query or "-",
        )

        # --- Invoke handler ---
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "API request failed method=%s path=%s duration_ms=%.1f",
                method,
                path,
                duration_ms,
                exc_info=True,
            )
            raise

        # --- Record response ---
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "API response method=%s path=%s status=%s duration_ms=%.1f",
            method,
            path,
            response.status_code,
            duration_ms,
        )
        return response
