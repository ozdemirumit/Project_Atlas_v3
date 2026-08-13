from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    # Constructing Settings() here forces ADR-003's production/development-identity
    # guard to run at import time, so a misconfigured production process fails to
    # start rather than serving requests with the guard silently bypassed.
    settings = get_settings()

    app = FastAPI(
        title="Project Atlas API",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
    )
    app.include_router(api_router)
    return app


app = create_app()
