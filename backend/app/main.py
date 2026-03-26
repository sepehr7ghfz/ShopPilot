from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles

from app.api.routes.assistant import router as assistant_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info("starting %s v%s", settings.app_name, settings.app_version)
    yield
    logger.info("shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

backend_root = Path(__file__).resolve().parents[1]
data_dir = backend_root / "data"


@app.middleware("http")
async def request_trace_middleware(request: Request, call_next):
    started_at = perf_counter()
    print(
        "[backend.http] incoming",
        {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
        },
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = round((perf_counter() - started_at) * 1000, 1)
        print(
            "[backend.http] error",
            {
                "method": request.method,
                "path": request.url.path,
                "elapsed_ms": elapsed_ms,
                "error": str(exc),
            },
        )
        raise

    elapsed_ms = round((perf_counter() - started_at) * 1000, 1)
    print(
        "[backend.http] outgoing",
        {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response

app.include_router(health_router)
app.include_router(assistant_router, prefix=settings.api_prefix)
app.mount("/media", StaticFiles(directory=str(data_dir)), name="media")
