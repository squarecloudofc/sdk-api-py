from importlib.util import find_spec

import pytest

if using_pydantic := find_spec('pydantic'):
    from pydantic import BaseModel

from squarecloud import Endpoint, errors
from squarecloud.app import Application
from squarecloud.data import AppData, Backup, LogsData, StatusData
from squarecloud.listeners import Listener


def _clear_listener_on_rerun(endpoint: Endpoint):
    def decorator(func):
        async def wrapper(self, app: Application):
            if app.get_listener(endpoint):
                app.remove_listener(endpoint)
            return await func(self, app=app)

        return wrapper

    return decorator


@pytest.mark.asyncio(scope='class')
@pytest.mark.listeners
@pytest.mark.capture_listener
class TestGeneralUse:
    @_clear_listener_on_rerun(Endpoint.app_status())
    async def test_capture_status(self, app: Application):
        @app.capture(Endpoint.app_status(), force_raise=True)
        async def capture_status(before, after):
            assert before is None
            assert isinstance(after, StatusData)

        await app.status()

    @_clear_listener_on_rerun(Endpoint.backup())
    async def test_capture_backup(self, app: Application):
        @app.capture(Endpoint.backup(), force_raise=True)
        async def capture_backup(before, after):
            assert before is None
            assert isinstance(after, Backup)

        await app.backup()

    @_clear_listener_on_rerun(Endpoint.logs())
    async def test_capture_logs(self, app: Application):
        @app.capture(Endpoint.logs(), force_raise=True)
        async def capture_logs(before, after):
            assert before is None
            assert isinstance(after, LogsData)

        await app.logs()

    @_clear_listener_on_rerun(Endpoint.app_data())
    async def test_app_data(self, app: Application):
        @app.capture(Endpoint('APP_DATA'), force_raise=True)
        async def capture_data(before, after):
            assert before is None
            assert isinstance(after, AppData)

        await app.data()

    @_clear_listener_on_rerun(Endpoint.app_status())
    async def test_extra(self, app: Application):
        metadata: dict[str, int] = {'metadata': 69}

        @app.capture(Endpoint.app_status(), force_raise=True)
        async def capture_status(extra):
            assert isinstance(extra, dict)
            assert extra == metadata

        await app.status(extra=metadata)

    @_clear_listener_on_rerun(Endpoint.app_status())
    async def test_extra_is_none(self, app: Application):
        @app.capture(Endpoint.app_status(), force_raise=True)
        async def capture_status(extra):
            assert extra is None

        await app.status()

    @_clear_listener_on_rerun(Endpoint.app_status())
    async def test_manage_listeners(self, app: Application):
        listener: Listener

        def callback_one():
            pass

        listener = app.include_listener(
            Listener(
                app=app,
                endpoint=Endpoint.app_status(),
                callback=callback_one,
            )
        )

        assert app.get_listener(Endpoint.app_status()).callback is callback_one
        assert (
            app.get_listener(Endpoint.app_status()).endpoint
            == Endpoint.app_status()
        )
        assert not app.get_listener(Endpoint.app_status()).callback_params
        assert listener.callback is callback_one
        assert listener.endpoint == Endpoint.app_status()

        def callback_two():
            pass

        with pytest.raises(errors.InvalidListener):
            app.include_listener(
                Listener(
                    app=app,
                    endpoint=Endpoint.app_status(),
                    callback=callback_two,
                )
            )

        app.remove_listener(Endpoint.app_status())
        assert app.get_listener(Endpoint.app_status()) is None

        listener = app.include_listener(
            Listener(
                app=app,
                endpoint=Endpoint.app_status(),
                callback=callback_two,
            )
        )
        assert listener.callback is callback_two
        assert listener.endpoint == Endpoint.app_status()

    @pytest.mark.skipif(
        'not using_pydantic', reason='pydantic not installed'
    )
    @_clear_listener_on_rerun(endpoint=Endpoint.app_status())
    async def test_pydantic_cast(self, app: Application):
        class Person(BaseModel):
            name: str
            age: int

        class Car(BaseModel):
            year: int

        @app.capture(Endpoint.app_status(), force_raise=True)
        async def capture_status(extra: Person | Car | dict):
            assert isinstance(extra, Car) or isinstance(extra, Person)
            return extra

        await app.status(extra={'name': 'Jhon', 'age': 18})
        await app.status(extra={'year': 1969})
