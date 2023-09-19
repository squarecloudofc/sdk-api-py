from time import sleep

import pytest

from squarecloud.data import BackupData, LogsData, StatusData

from . import client


@pytest.mark.asyncio
class Tests:
    async def test_status(self):
        apps = await client.all_apps()
        app = apps[0]
        cache = app.cache

        assert cache.status is None

        status = await app.status(update_cache=False)
        assert cache.status is None

        cache.update(status)
        assert isinstance(cache.status, StatusData)

        cache.clear()
        assert cache.status is None
        sleep(10)

    async def test_backup(self):
        apps = await client.all_apps()
        app = apps[0]
        cache = app.cache

        assert cache.backup is None

        backup = await app.backup(update_cache=False)
        assert cache.backup is None

        cache.update(backup)
        assert isinstance(cache.backup, BackupData)

        cache.clear()
        assert cache.backup is None

    async def test_logs(self):
        apps = await client.all_apps()
        app = apps[0]
        cache = app.cache

        assert cache.logs is None

        logs = await app.logs(update_cache=False)
        assert cache.logs is None

        cache.update(logs)
        assert isinstance(cache.logs, LogsData)

        cache.clear()
        assert cache.logs is None
