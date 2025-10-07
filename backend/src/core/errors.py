"""Consistent error responses."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded


def _format_error(detail: str, status_code: int) -> JSONResponse:
    return JSONResponse({"error": detail}, status_code=status_code)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers to the FastAPI application."""

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        return _format_error(str(exc.detail), exc.status_code)

    @app.exception_handler(ValidationError)
    async def handle_validation_exception(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse({"errors": exc.errors()}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate_limit(_: Request, exc: RateLimitExceeded) -> JSONResponse:
        return _format_error("Rate limit exceeded", status.HTTP_429_TOO_MANY_REQUESTS)

