from time import sleep

import pytest

from squarecloud.app import Application
from squarecloud.data import Snapshot, LogsData, StatusData


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

    async def test_snapshot(self, app: Application):
        cache = app.cache

        assert cache.snapshot is None

        snapshot = await app.snapshot(update_cache=False)
        assert cache.snapshot is None

        cache.update(snapshot)
        assert isinstance(cache.snapshot, Snapshot)

        cache.clear()
        assert cache.snapshot is None

    async def test_logs(self, app: Application):
        cache = app.cache

        assert cache.logs is None

        logs = await app.logs(update_cache=False)
        assert cache.logs is None

        cache.update(logs)
        assert isinstance(cache.logs, LogsData)

        cache.clear()
        assert cache.logs is None
