import pytest

from squarecloud import Client, Endpoint, File
from squarecloud.data import UploadData
from squarecloud.http import Response

from . import GITHUB_ACCESS_TOKEN


@pytest.mark.asyncio(scope='session')
@pytest.mark.listeners
@pytest.mark.request_listener
class TestRequestListeners:
    async def test_request_logs(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.logs()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.get_logs(app.id)

    async def test_request_app_status(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.app_status()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.app_status(app.id)

    async def test_request_backup(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.backup()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.backup(app.id)

    async def test_request_start_app(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.start()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.start_app(app.id)

    async def test_request_stop_app(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.stop()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.stop_app(app.id)

    async def test_request_restart_app(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.restart()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.restart_app(app.id)

    async def test_request_app_data(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.app_data()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.app_data(app.id)

    async def test_request_statistics(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.statistics()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.statistics()

    async def test_request_app_files_list(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.files_list()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.app_files_list(app.id, path='/')

    async def test_request_read_file(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.files_read()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.read_app_file(app.id, '/main.py')

    async def test_request_create_file(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.files_create()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.create_app_file(
            app.id, File('tests/test.txt'), '/test.txt'
        )

    async def test_request_delete_file(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.files_delete()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.delete_app_file(app.id, '/test.txt')

    async def test_request_commit(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.commit()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.commit(
            app.id, File('tests/test.txt')
        )

    async def test_request_user_info(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.user_info()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.user_info()

    async def test_request_me(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.user_me()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.me()

    async def test_last_deploys(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.last_deploys()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.last_deploys(app.id)

    async def test_github_integration(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.github_integration()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.github_integration(
            app.id,
            GITHUB_ACCESS_TOKEN,
        )

    @pytest.mark.skipif(
        lambda app: not app.is_website,
        reason='application is not website'
    )
    async def test_domain_analytics(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.domain_analytics()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.domain_analytics(app.id)

    @pytest.mark.skipif(
        lambda app: not app.is_website,
        reason='application is not website'
    )
    async def test_set_custom_domain(self, client: Client, app: UploadData):
        endpoint: Endpoint = Endpoint.custom_domain()

        if not client._listener.get_request_listener(endpoint):
            @client.on_request(endpoint)
            async def test(response: Response):
                assert isinstance(response, Response)

        await client.set_custom_domain(
            '6c8e9b785cce4f99984f9ca1c5470d51', 'test.com.br'
        )
