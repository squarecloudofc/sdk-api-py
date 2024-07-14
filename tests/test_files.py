from io import BytesIO
from time import sleep

import pytest

import squarecloud as square
from squarecloud import Client
from squarecloud.app import Application
from squarecloud.data import FileInfo


@pytest.mark.asyncio(scope='session')
@pytest.mark.files
class TestFileClient:
    async def test_files_type(self, app_files: list[FileInfo]):
        assert isinstance(app_files, list)
        for file in app_files:
            assert isinstance(file, FileInfo)

            assert isinstance(file.name, str)
            assert isinstance(file.size, float)
            assert isinstance(file.lastModified, int | float)

            assert file.type in ('file', 'directory')

    async def test_read_file(
        self, client: Client, app: Application, app_files: list[FileInfo]
    ):
        file_read = await client.read_app_file(app.id, app_files[0].path)
        assert isinstance(file_read, BytesIO)

    async def test_create_file(self, client: Client, app: Application):
        await client.create_app_file(
            app.id, file=square.File('tests/test.txt'), path='/test.txt'
        )

    async def test_delete_file(self, client: Client, app: Application):
        sleep(3)
        await client.delete_app_file(app.id, path='/test.txt')


@pytest.mark.asyncio(scope='session')
@pytest.mark.files
class TestsApplication:
    async def test_files_list(
        self, app: Application, app_files: list[FileInfo]
    ):
        TestsApplication.TEST_FILES = await app.files_list(path='/')

        assert isinstance(app_files, list)
        for file in app_files:
            assert isinstance(file, FileInfo)

            assert isinstance(file.name, str)
            assert isinstance(file.size, float)
            assert isinstance(file.lastModified, int | float)

            assert file.type in ('file', 'directory')

    async def test_read_file(
        self, app: Application, app_files: list[FileInfo]
    ):
        file_read = await app.read_file(app_files[0].path)
        assert isinstance(file_read, BytesIO)

    async def test_create_file(self, app: Application):
        await app.create_file(
            file=square.File('tests/test.txt'), path='test.txt'
        )

    async def test_delete_file(self, app: Application):
        sleep(3)
        await app.delete_file(path='/test.txt')
