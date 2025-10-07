"""Application factory for the FastAPI backend."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.casbin_enforcer import get_enforcer
from .core.db import dispose_engine
from .core.errors import register_exception_handlers
from .core.http import setup_http
from .core.logging import configure_logging
from .core.observability import setup_observability
from .core.settings import Settings, get_settings
from .features.scheduling.interfaces.router_commands import router as scheduling_commands_router
from .features.dictation.interfaces.router import router as dictation_router
from .features.scheduling.interfaces.router_queries import router as scheduling_queries_router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    await get_enforcer(settings)
    yield
    await dispose_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Instantiate the FastAPI application."""
    settings = settings or get_settings()
    app = FastAPI(
        title="Keur Doctor Backend",
        version="0.1.0",
        lifespan=_lifespan,
    )

    setup_http(app, settings)
    setup_observability(app, settings)
    register_exception_handlers(app)

    @app.get("/healthz", tags=["meta"], summary="Health check")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(scheduling_queries_router)
    app.include_router(scheduling_commands_router)
    app.include_router(dictation_router)

    return app
