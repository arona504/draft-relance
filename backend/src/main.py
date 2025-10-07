"""Application entrypoint for running with `python -m` or uvicorn."""

from __future__ import annotations

import uvicorn

from .app import create_app
from .core.settings import get_settings

settings = get_settings()
app = create_app(settings)


def run() -> None:
    """Run the ASGI server."""
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        factory=False,
    )


if __name__ == "__main__":
    run()

