import pytest

from squarecloud.app import Application
from tests import GITHUB_ACCESS_TOKEN


@pytest.mark.asyncio(scope='session')
@pytest.mark.app
class TestApp:
    async def test_app_data(self, app: Application):
        await app.data()

    async def test_app_status(self, app: Application):
        await app.status()

    async def test_app_logs(self, app: Application):
        await app.logs()

    async def test_app_backup(self, app: Application):
        await app.backup()

    async def test_app_github_integration(self, app: Application):
        await app.github_integration(GITHUB_ACCESS_TOKEN)

    async def test_app_last_deploys(self, app: Application):
        await app.last_deploys()

    @pytest.mark.skipif(
        lambda app: not app.is_website,
        reason='application is not website'
    )
    async def test_domain_analytics(self, app: Application):
        await app.domain_analytics()

    @pytest.mark.skipif(
        lambda app: not app.is_website,
        reason='application is not website'
    )
    async def test_set_custom_domain(self, app: Application):
        await app.set_custom_domain('test.com.br')
