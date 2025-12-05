from zipfile import ZipFile

import pytest

import squarecloud
from squarecloud import SnapshotInfo
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

    async def test_app_status(self, app: Application):
        assert isinstance(await app.status(), squarecloud.StatusData)

    async def test_app_logs(self, app: Application):
        assert isinstance(await app.logs(), squarecloud.LogsData)

    async def test_app_snapshot(self, app: Application):
        assert isinstance(await app.snapshot(), squarecloud.Snapshot)

    async def test_download_snapshot(self, app: Application):
        snapshot = await app.snapshot()
        zip_file = await snapshot.download()
        assert isinstance(zip_file, ZipFile)

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

    async def test_get_all_snapshots(self, app: Application):
        snapshots = await app.all_snapshots()
        assert isinstance(snapshots, list)
        assert isinstance(snapshots[0], SnapshotInfo)

    async def test_move_file(self, app: Application):
        response = await app.move_file('main.py', 'test.py')
        assert isinstance(response, Response)
        assert response.status == 'success'
