import pytest

from . import client, GITHUB_ACCESS_TOKEN


@pytest.mark.asyncio
class TestClient:
    async def test_basic_usage(self):
        app = await client.all_apps()
        app = app[0]
        await app.data()
        await app.status()
        await app.logs()
        await app.backup()
        await app.data()
        await app.github_integration(GITHUB_ACCESS_TOKEN)
        await app.last_deploys()
