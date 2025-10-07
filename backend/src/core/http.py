"""HTTP configuration: middleware, security headers, and rate limiting."""

from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from .settings import Settings


def _limiter_key(request: Request) -> str:
    principal = getattr(request.state, "principal", None)
    if principal and getattr(principal, "sub", None):
        return principal.sub
    return get_remote_address(request)


limiter = Limiter(key_func=_limiter_key, default_limits=[])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add opinionated security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "no-referrer-when-downgrade")
        response.headers.setdefault("Permissions-Policy", "microphone=(), camera=()")
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def setup_http(app: FastAPI, settings: Settings) -> None:
    """Configure middlewares for the FastAPI application."""
    limiter.init_app(app)
    app.state.rate_limit_queries_per_min = settings.rate_limit_queries_per_min

    app.add_middleware(SecurityHeadersMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
