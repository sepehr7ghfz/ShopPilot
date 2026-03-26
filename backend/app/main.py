from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

app.include_router(health_router)
app.include_router(assistant_router, prefix=settings.api_prefix)
