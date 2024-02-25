import pytest

from squarecloud import Endpoint
from squarecloud.app import Application
from squarecloud.data import BackupData, LogsData, StatusData


@pytest.mark.asyncio(scope='session')
@pytest.mark.listeners
@pytest.mark.capture_listener
class TestRequestListeners:
    async def test_capture_status(self, app: Application):
        @app.capture(Endpoint.app_status())
        async def capture_status(before, after):
            assert before is None
            assert isinstance(after, StatusData)

        await app.status()

    async def test_capture_backup(self, app: Application):
        @app.capture(Endpoint.backup())
        async def capture_backup(before, after):
            assert before is None
            assert isinstance(after, BackupData)

        await app.backup()

    async def test_capture_logs(self, app: Application):
        @app.capture(Endpoint.logs())
        async def capture_status(before, after):
            assert before is None
            assert isinstance(after, LogsData)

        await app.logs()
