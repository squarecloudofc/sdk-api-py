from importlib.util import find_spec
from io import BytesIO

import pytest

if using_pydantic := bool(find_spec('pydantic')):
    from pydantic import BaseModel

from squarecloud import Client, Endpoint, File
from squarecloud.app import Application
from squarecloud.data import (
    Backup,
    BackupInfo,
    DeployData,
    DomainAnalytics,
    FileInfo,
    LogsData,
    ResumedStatus,
    StatusData,
    UserData,
)
from squarecloud.http import Response

from . import GITHUB_ACCESS_TOKEN


def _clear_listener_on_rerun(endpoint: Endpoint):
    def decorator(func):
        async def wrapper(self, client: Client, app: Application):
            if client.get_listener(endpoint):
                client.remove_listener(endpoint)
            return await func(self, client, app)

        return wrapper

    return decorator


@pytest.mark.asyncio(scope='session')
@pytest.mark.listeners
@pytest.mark.request_listener
class TestRequestListeners:
    @_clear_listener_on_rerun(Endpoint.logs())
    async def test_request_logs(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.logs()
        expected_result: LogsData | None
        expected_response: LogsData | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.get_logs(app.id)
        assert isinstance(expected_result, LogsData)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.app_status())
    async def test_request_app_status(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.app_status()
        expected_result: StatusData | None
        expected_response: StatusData | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.app_status(app.id)
        assert isinstance(expected_result, StatusData)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.backup())
    async def test_request_backup(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.backup()
        expected_result: Backup | None
        expected_response: Backup | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.backup(app.id)
        assert isinstance(expected_result, Backup)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.start())
    async def test_request_start_app(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.start()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.start_app(app.id)
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.stop())
    async def test_request_stop_app(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.stop()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.stop_app(app.id)
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.restart())
    async def test_request_restart_app(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.restart()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.restart_app(app.id)
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.files_list())
    async def test_request_app_files_list(
        self, client: Client, app: Application
    ):
        endpoint: Endpoint = Endpoint.files_list()
        expected_result: list[FileInfo] | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.app_files_list(app.id, path='/')
        assert isinstance(expected_result, list)
        assert isinstance(expected_result[0], FileInfo)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.files_read())
    async def test_request_read_file(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.files_read()
        expected_result: BytesIO | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.read_app_file(app.id, '/main.py')
        assert isinstance(expected_result, BytesIO)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.files_create())
    async def test_request_create_file(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.files_create()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.create_app_file(
            app.id, File('tests/test.txt'), '/test.txt'
        )
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.files_delete())
    async def test_request_delete_file(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.files_delete()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.delete_app_file(app.id, '/test.txt')
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.commit())
    async def test_request_commit(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.commit()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.commit(app.id, File('tests/test.txt'))
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.user())
    async def test_request_user(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.user()
        expected_result: UserData | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.user()
        assert isinstance(expected_result, UserData)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.last_deploys())
    async def test_last_deploys(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.last_deploys()
        expected_result: list[list[DeployData]] | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.last_deploys(app.id)
        assert isinstance(expected_result, list)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.github_integration())
    async def test_github_integration(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.github_integration()
        expected_result: str | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.github_integration(
            app.id,
            GITHUB_ACCESS_TOKEN,
        )
        assert isinstance(expected_result, str)
        assert isinstance(expected_response, Response)

    @pytest.mark.skipif(
        lambda app: not app.is_website, reason='application is not website'
    )
    @_clear_listener_on_rerun(Endpoint.domain_analytics())
    async def test_domain_analytics(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.domain_analytics()
        expected_result: DomainAnalytics | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.domain_analytics(app.id)
        assert isinstance(expected_result, DomainAnalytics)
        assert isinstance(expected_response, Response)

    @pytest.mark.skipif(
        lambda app: not app.is_website, reason='application is not website'
    )
    @_clear_listener_on_rerun(Endpoint.custom_domain())
    async def test_set_custom_domain(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.github_integration()
        expected_result: str | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.github_integration(
            app.id,
            GITHUB_ACCESS_TOKEN,
        )
        assert isinstance(expected_result, str)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.all_backups())
    async def test_all_backups(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.all_backups()
        expected_result: list[BackupInfo] | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.all_app_backups(app.id)
        assert isinstance(expected_result, list)
        assert isinstance(expected_result[0], BackupInfo)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.all_apps_status())
    async def test_all_apps_status(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.all_apps_status()
        expected_result: list[ResumedStatus] | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.all_apps_status()
        assert isinstance(expected_result, list)
        assert isinstance(expected_result[0], ResumedStatus)
        assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.move_file())
    async def test_move_app_file(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.move_file()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.move_app_file(
            app.id, 'test.txt', 'test_move.txt'
        )
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    # @_clear_listener_on_rerun(Endpoint.dns_records())
    # @pytest.mark.skipif(
    #     lambda app: not app.custom,
    #     reason='app have not custom domain',
    # )
    # async def test_dns_records(self, client: Client, app: Application):
    #     endpoint: Endpoint = Endpoint.dns_records()
    #     expected_result: list[DNSRecord] | None
    #     expected_response: Response | None = None
    #
    #     @client.on_request(endpoint)
    #     async def test_listener(response: Response):
    #         nonlocal expected_response
    #         expected_response = response
    #
    #     expected_result = await client.dns_records(app.id)
    #     assert isinstance(expected_result, list)
    #     assert isinstance(expected_result[0], DNSRecord)
    #     assert isinstance(expected_response, Response)

    @_clear_listener_on_rerun(Endpoint.current_integration())
    async def test_current(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.current_integration()
        expected_result: str | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.current_app_integration(app.id)
        assert isinstance(expected_result, str)
        assert isinstance(expected_response, Response)

    @pytest.mark.skipif('not using_pydantic', reason='pydantic not installed')
    @_clear_listener_on_rerun(endpoint=Endpoint.app_status())
    async def test_pydantic_cast(self, client: Client, app: Application):
        class Person(BaseModel):
            name: str
            age: int

        class Car(BaseModel):
            year: int

        @client.on_request(Endpoint.app_status(), force_raise=True)
        async def capture_status(extra: Person | Car | dict):
            assert isinstance(extra, Car) or isinstance(extra, Person)
            return extra

        await client.app_status(
            app_id=app.id, extra={'name': 'Jhon', 'age': 18}
        )
        await client.app_status(app_id=app.id, extra={'year': 1969})
