import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.scheduler.health import run_forever


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    task: asyncio.Task[None] | None = None
    if settings.health_check_interval_seconds > 0:
        task = asyncio.create_task(run_forever(settings.health_check_interval_seconds))
    yield
    if task is not None:
        task.cancel()


def create_app() -> FastAPI:
    # Constructing Settings() here forces ADR-003's production/development-identity
    # guard to run at import time, so a misconfigured production process fails to
    # start rather than serving requests with the guard silently bypassed.
    settings = get_settings()

    app = FastAPI(
        title="Project Atlas API",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
