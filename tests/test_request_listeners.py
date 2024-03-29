from io import BytesIO

import pytest

from squarecloud import Client, Endpoint, File
from squarecloud.app import Application
from squarecloud.data import (
    AppData,
    BackupData,
    DeployData,
    DomainAnalytics,
    FileInfo,
    LogsData,
    StatisticsData,
    StatusData,
    UserData,
)
from squarecloud.http import Response

from . import GITHUB_ACCESS_TOKEN


@pytest.mark.asyncio(scope='session')
@pytest.mark.listeners
@pytest.mark.request_listener
class TestRequestListeners:
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

    async def test_request_backup(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.backup()
        expected_result: BackupData | None
        expected_response: BackupData | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.backup(app.id)
        assert isinstance(expected_result, BackupData)
        assert isinstance(expected_response, Response)

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

    async def test_request_app_data(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.app_data()
        expected_result: AppData | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.app_data(app.id)
        assert isinstance(expected_result, AppData)
        assert isinstance(expected_response, Response)

    async def test_request_statistics(self, client: Client):
        endpoint: Endpoint = Endpoint.statistics()
        expected_result: StatisticsData | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.statistics()
        assert isinstance(expected_result, StatisticsData)
        assert isinstance(expected_response, Response)

    async def test_request_app_files_list(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.files_list()
        expected_result: StatisticsData | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.app_files_list(app.id, path='/')
        assert isinstance(expected_result, list)
        assert isinstance(expected_result[0], FileInfo)
        assert isinstance(expected_response, Response)

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

    async def test_request_delete_file(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.files_delete()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.delete_app_file(
            app.id, '/test.txt'
        )
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    async def test_request_commit(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.commit()
        expected_result: Response | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.commit(
            app.id, File('tests/test.txt')
        )
        assert isinstance(expected_result, Response)
        assert isinstance(expected_response, Response)

    @pytest.mark.skip
    async def test_request_user_info(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.user_info()
        expected_result: UserData | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.user_info(573657767496253451)
        assert isinstance(expected_result, UserData)
        assert isinstance(expected_response, Response)

    async def test_request_me(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.user_me()
        expected_result: UserData | None
        expected_response: Response | None = None

        @client.on_request(endpoint)
        async def test_listener(response: Response):
            nonlocal expected_response
            expected_response = response

        expected_result = await client.me()
        assert isinstance(expected_result, UserData)
        assert isinstance(expected_response, Response)

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
        lambda app: not app.is_website,
        reason='application is not website'
    )
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
        lambda app: not app.is_website,
        reason='application is not website'
    )
    async def test_set_custom_domain(self, client: Client, app: Application):
        endpoint: Endpoint = Endpoint.custom_domain()

        if not client.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.set_custom_domain(
            '6c8e9b785cce4f99984f9ca1c5470d51', 'test.com.br'
        )
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
