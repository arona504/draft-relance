"""Prometheus metrics and optional OpenTelemetry instrumentation."""

from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .settings import Settings

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code", "tenant"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Collect simple HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start_time

        path = request.url.path
        method = request.method
        status_code = response.status_code
        tenant = getattr(getattr(request.state, "principal", None), "tenant_id", "anonymous")

        REQUEST_COUNT.labels(method=method, path=path, status_code=status_code, tenant=tenant).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)

        return response


def _setup_tracing(settings: Settings) -> None:
    """Initialise OTLP tracing if configured."""
    if not settings.otel_exporter_otlp_endpoint:
        return

    resource = Resource.create({"service.name": settings.service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def setup_observability(app: FastAPI, settings: Settings) -> None:
    """Configure metrics endpoint and tracing."""
    _setup_tracing(settings)

    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
