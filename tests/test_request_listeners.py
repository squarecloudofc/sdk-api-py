import pytest

import squarecloud
from squarecloud import Endpoint, File
from squarecloud.data import UploadData
from squarecloud.http import Response

from . import GITHUB_ACCESS_TOKEN, client, create_zip


@pytest.mark.asyncio
class TestRequestListeners:
    APP_ID: str

    async def test_upload(self):
        @client.on_request(Endpoint.upload())
        async def test(response: Response):
            assert isinstance(response, Response)

        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='normal_test',
            main='main.py',
            memory=100,
        )
        upload_data: UploadData = await client.upload_app(
            File(create_zip(), filename='file.zip')
        )
        TestRequestListeners.APP_ID = upload_data.id

    async def test_request_logs(self):
        @client.on_request(Endpoint.logs())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.get_logs(TestRequestListeners.APP_ID)

    async def test_request_app_status(self):
        @client.on_request(Endpoint.app_status())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.app_status(TestRequestListeners.APP_ID)

    async def test_request_backup(self):
        @client.on_request(Endpoint.backup())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.backup(TestRequestListeners.APP_ID)

    async def test_request_start_app(self):
        @client.on_request(Endpoint.start())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.start_app(TestRequestListeners.APP_ID)

    async def test_request_stop_app(self):
        @client.on_request(Endpoint.stop())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.stop_app(TestRequestListeners.APP_ID)

    async def test_request_restart_app(self):
        @client.on_request(Endpoint.restart())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.restart_app(TestRequestListeners.APP_ID)

    async def test_request_app_data(self):
        @client.on_request(Endpoint.app_data())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.app_data(TestRequestListeners.APP_ID)

    async def test_request_statistics(self):
        @client.on_request(Endpoint.statistics())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.statistics()

    async def test_request_app_files_list(self):
        @client.on_request(Endpoint.files_list())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.app_files_list(TestRequestListeners.APP_ID, path='/')

    async def test_request_read_file(self):
        @client.on_request(Endpoint.files_read())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.read_app_file(TestRequestListeners.APP_ID, '/main.py')

    async def test_request_create_file(self):
        @client.on_request(Endpoint.files_create())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.create_app_file(
            TestRequestListeners.APP_ID, File('tests/test.txt'), '/test.txt'
        )

    async def test_request_delete_file(self):
        @client.on_request(Endpoint.files_delete())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.delete_app_file(TestRequestListeners.APP_ID, '/test.txt')

    async def test_request_commit(self):
        @client.on_request(Endpoint.commit())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.commit(
            TestRequestListeners.APP_ID, File('tests/test.txt')
        )

    async def test_request_user_info(self):
        @client.on_request(Endpoint.user_info())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.user_info()

    async def test_request_me(self):
        @client.on_request(Endpoint.user_me())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.me()

    async def test_last_deploys(self):
        @client.on_request(Endpoint.last_deploys())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.last_deploys(TestRequestListeners.APP_ID)

    async def test_github_integration(self):
        @client.on_request(Endpoint.github_integration())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.github_integration(
            TestRequestListeners.APP_ID,
            GITHUB_ACCESS_TOKEN,
        )

    async def test_domain_analytics(self):
        @client.on_request(Endpoint.domain_analytics())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.domain_analytics('6c8e9b785cce4f99984f9ca1c5470d51')

    async def test_set_custom_domain(self):
        @client.on_request(Endpoint.custom_domain())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.set_custom_domain(
            '6c8e9b785cce4f99984f9ca1c5470d51', 'test.com.br'
        )

    async def test_delete_app(self):
        @client.on_request(Endpoint.delete_app())
        async def test(response: Response):
            assert isinstance(response, Response)

        await client.delete_app(TestRequestListeners.APP_ID)
