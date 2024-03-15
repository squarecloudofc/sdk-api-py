import pytest

from squarecloud import Endpoint, errors
from squarecloud.app import Application
from squarecloud.data import AppData, BackupData, LogsData, StatusData
from squarecloud.listeners import CaptureListener


@pytest.mark.asyncio(scope='class')
@pytest.mark.listeners
@pytest.mark.capture_listener
class TestGeneralUse:
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

    async def test_app_data(self, app: Application):

        @app.capture(Endpoint('APP_DATA'))
        async def capture_data(before, after):
            assert before is None
            assert isinstance(after, AppData)
        await app.data()

    async def test_extra(self, app: Application):
        metadata: dict[str, int] = {'metadata': 69}
        app.remove_listener(Endpoint.app_status())

        @app.capture(Endpoint.app_status())
        async def capture_status(extra):
            assert isinstance(extra, dict)
            assert extra == metadata

        await app.status(extra=metadata)
        app.remove_listener(Endpoint.app_status())

    async def test_extra_is_none(self, app: Application):
        @app.capture(Endpoint.app_status())
        async def capture_status(extra):
            assert extra is None

        await app.status()
        app.remove_listener(Endpoint.app_status())

    async def test_manage_listeners(self, app: Application):
        listener: CaptureListener

        def callback_one(): pass

        listener = app.include_listener(
            Endpoint.app_status(), callback_one
        )

        assert app.get_listener(Endpoint.app_status()).callback is callback_one
        assert app.get_listener(
            Endpoint.app_status()
        ).endpoint == Endpoint.app_status()
        assert not app.get_listener(Endpoint.app_status()).callback_args
        assert listener.callback is callback_one
        assert listener.endpoint == Endpoint.app_status()

        def callback_two(): pass

        with pytest.raises(errors.InvalidListener):
            app.include_listener(Endpoint.app_status(), callback_two)

        app.remove_listener(Endpoint.app_status())
        assert app.get_listener(Endpoint.app_status()) is None

        listener = app.include_listener(
            Endpoint.app_status(), callback_two
        )

        assert listener.callback is callback_two
        assert listener.endpoint == Endpoint.app_status()
