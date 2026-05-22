import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from reverse_recruiter.api.routers import apply, health, pipeline, search, session
from reverse_recruiter.config import settings
from reverse_recruiter.logging_config import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ReverseRecruiter API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception path=%s",
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred",
            },
        )

    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(session.router, prefix=prefix)
    app.include_router(search.router, prefix=prefix)
    app.include_router(apply.router, prefix=prefix)
    app.include_router(pipeline.router, prefix=prefix)
    return app


app = create_app()
