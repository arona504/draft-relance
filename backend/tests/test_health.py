import pytest
from httpx import AsyncClient

from src.app import create_app


@pytest.mark.asyncio
async def test_healthz() -> None:
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

