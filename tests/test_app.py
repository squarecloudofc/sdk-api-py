import pytest

from . import client


@pytest.mark.asyncio
class TestClient:
    async def test_basic_usage(self):
        app = await client.all_apps()
        app = app[0]
        await app.status()
        await app.logs()
        await app.backup()
        await app.data()
