import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/testdb")
os.environ.setdefault("CASBIN_DB_URL", os.environ["DATABASE_URL"])
os.environ.setdefault("KC_URL", "http://localhost:8081")
os.environ.setdefault("KC_REALM", "test-realm")
os.environ.setdefault("KC_AUDIENCE", "test-audience")
os.environ.setdefault("KC_CLIENT_ID", "keur-backend")

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.app import create_app


@pytest.mark.asyncio
async def test_healthz() -> None:
    app = create_app()
    transport = ASGITransport(app=app, lifespan="off")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
