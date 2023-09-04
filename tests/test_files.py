from io import BytesIO
from time import sleep

import pytest

import squarecloud as square
from squarecloud.data import FileInfo

from . import client

created_file = None


@pytest.mark.asyncio
class TestFileClient:
    TEST_FILES: list[FileInfo]

    async def test_files_list(self):
        apps = await client.all_apps()
        app = apps[0]
        TestFileClient.TEST_FILES = await client.app_files_list(
            app.id, path='/'
        )

        assert isinstance(TestFileClient.TEST_FILES, list)
        for file in TestFileClient.TEST_FILES:
            assert isinstance(file, FileInfo)

            assert isinstance(file.name, str)
            assert isinstance(file.size, int)
            assert isinstance(file.lastModified, int | float)

            assert file.type in ('file', 'directory')

    async def test_read_file(self):
        apps = await client.all_apps()
        app = apps[0]
        file_read = await app.read_file(TestFileClient.TEST_FILES[0].path)
        assert isinstance(file_read, BytesIO)

    async def test_create_file(self):
        apps = await client.all_apps()
        app = apps[0]
        await client.create_app_file(
            app_id=app.id, file=square.File('test.txt'), path='/test.txt'
        )

    async def test_delete_file(self):
        apps = await client.all_apps()
        app = apps[0]
        sleep(3)
        await client.delete_app_file(app_id=app.id, path='/test.txt')


@pytest.mark.asyncio
class TestsApplication:
    TEST_FILES: list[FileInfo]

    async def test_files_list(self):
        apps = await client.all_apps()
        app = apps[0]
        TestsApplication.TEST_FILES = await app.files_list(path='/')

        assert isinstance(TestsApplication.TEST_FILES, list)
        for file in TestsApplication.TEST_FILES:
            assert isinstance(file, FileInfo)

            assert isinstance(file.name, str)
            assert isinstance(file.size, int)
            assert isinstance(file.lastModified, int | float)

            assert file.type in ('file', 'directory')

    async def test_read_file(self):
        apps = await client.all_apps()
        app = apps[0]
        file_read = await app.read_file(TestsApplication.TEST_FILES[0].path)
        assert isinstance(file_read, BytesIO)

    async def test_create_file(self):
        apps = await client.all_apps()
        app = apps[0]
        await app.create_file(file=square.File('test.txt'), path='test.txt')

    async def test_delete_file(self):
        sleep(3)
        apps = await client.all_apps()
        app = apps[0]
        await app.delete_file(path='/test.txt')
