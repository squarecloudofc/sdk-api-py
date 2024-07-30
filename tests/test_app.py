import pytest

import squarecloud
from squarecloud import BackupInfo
from squarecloud.app import Application
from squarecloud.http import Response
from tests import GITHUB_ACCESS_TOKEN


@pytest.mark.asyncio(scope='session')
@pytest.mark.app
class TestApp:
    async def test_magic_methods(self, app: Application):
        assert (
            app.__repr__()
            == f'<{Application.__name__} tag={app.name} id={app.id}>'
        )

    async def test_app_data(self, app: Application):
        assert isinstance(await app.data(), squarecloud.AppData)

    async def test_app_status(self, app: Application):
        assert isinstance(await app.status(), squarecloud.StatusData)

    async def test_app_logs(self, app: Application):
        assert isinstance(await app.logs(), squarecloud.LogsData)

    async def test_app_backup(self, app: Application):
        assert isinstance(await app.backup(), squarecloud.Backup)

    async def test_app_github_integration(self, app: Application):
        assert isinstance(
            await app.github_integration(GITHUB_ACCESS_TOKEN), str
        )

    async def test_app_last_deploys(self, app: Application):
        assert isinstance(await app.last_deploys(), list)

    async def test_domain_analytics(self, app: Application):
        assert isinstance(
            await app.domain_analytics(), squarecloud.DomainAnalytics
        )

    @pytest.mark.skip
    async def test_set_custom_domain(self, app: Application):
        assert isinstance(await app.set_custom_domain('test.com.br'), str)

    async def test_get_all_backups(self, app: Application):
        backups = await app.all_backups()
        assert isinstance(backups, list)
        assert isinstance(backups[0], BackupInfo)

    async def test_move_file(self, app: Application):
        response = await app.move_file('main.py', 'test.py')
        assert isinstance(response, Response)
        assert response.status == 'success'
