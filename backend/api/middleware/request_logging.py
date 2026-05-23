import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_MAX_BODY_LOG = 4096


def _body_for_log(body: bytes) -> str:
    if not body:
        return "-"
    text = body.decode("utf-8", errors="replace")
    if len(text) > _MAX_BODY_LOG:
        return f"{text[:_MAX_BODY_LOG]}...(truncated)"
    return text


def _request_with_body(request: Request, body: bytes) -> Request:
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(request.scope, receive)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every inbound HTTP API request and response at the presentation boundary."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # --- Record request ---
        start = time.perf_counter()
        path = request.url.path
        method = request.method
        query = request.url.query
        handler_request = request
        body_log = "-"
        if method == "POST":
            body = await request.body()
            body_log = _body_for_log(body)
            handler_request = _request_with_body(request, body)
        logger.info(
            "API request method=%s path=%s query=%s body=%s",
            method,
            path,
            query or "-",
            body_log,
        )

        # --- Invoke handler ---
        try:
            response = await call_next(handler_request)
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
