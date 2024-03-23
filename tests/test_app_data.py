from time import sleep

import pytest

from squarecloud.app import Application
from squarecloud.data import BackupData, LogsData, StatusData


@pytest.mark.asyncio(scope='session')
@pytest.mark.app_data
class Tests:
    async def test_status(self, app: Application):
        cache = app.cache
        cache.clear()

        assert cache.status is None

        status = await app.status(update_cache=False)
        assert cache.status is None

        cache.update(status)
        assert isinstance(cache.status, StatusData)

        cache.clear()
        assert cache.status is None
        sleep(10)

    async def test_backup(self, app: Application):
        cache = app.cache

        assert cache.backup is None

        backup = await app.backup(update_cache=False)
        assert cache.backup is None

        cache.update(backup)
        assert isinstance(cache.backup, BackupData)

        cache.clear()
        assert cache.backup is None

    async def test_logs(self, app: Application):
        cache = app.cache

        assert cache.logs is None

        logs = await app.logs(update_cache=False)
        assert cache.logs is None

        cache.update(logs)
        assert isinstance(cache.logs, LogsData)

        cache.clear()
        assert cache.logs is None
