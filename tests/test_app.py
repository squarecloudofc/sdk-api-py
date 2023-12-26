import pytest

from . import GITHUB_ACCESS_TOKEN, client


@pytest.mark.asyncio
class TestClient:
    async def test_basic_usage(self):
        app = await client.app('6c8e9b785cce4f99984f9ca1c5470d51')
        await app.data()
        await app.status()
        await app.logs()
        await app.backup()
        await app.data()
        await app.github_integration(GITHUB_ACCESS_TOKEN)
        await app.last_deploys()
        await app.domain_analytics()
        await app.set_custom_domain('test.com.br')
