import pytest

from squarecloud import Endpoint
from squarecloud.app import Application
from squarecloud.data import BackupData, StatusData, LogsData
from . import client

apps: list[Application] = []


@pytest.mark.asyncio
class TestRequestListeners:
    async def test_startup(self):
        global apps
        apps = await client.all_apps()

    async def test_capture_status(self):
        app = apps[0]

        @app.capture(Endpoint.app_status())
        async def capture_status(before, after):
            assert before is None
            assert isinstance(after, StatusData)

        await app.status()

    async def test_capture_backup(self):
        app = apps[0]

        @app.capture(Endpoint.backup())
        async def capture_backup(before, after):
            assert before is None
            assert isinstance(after, BackupData)

        await app.backup()

    async def test_capture_logs(self):
        app = apps[0]

        @app.capture(Endpoint.logs())
        async def capture_status(before, after):
            assert before is None
            assert isinstance(after, LogsData)

        await app.logs()
