import asyncio
import io
import zipfile

import pytest

import squarecloud
from squarecloud import File, errors
from squarecloud.data import UploadData

from . import client


def create_zip(include_squarecloud_app: bool = True):
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w') as zip_file:
        zip_file.write(
            r'tests\test_upload\requirements.txt', 'requirements.txt'
        )

        zip_file.write(r'tests\test_upload\main.py', 'main.py')

        if include_squarecloud_app:
            zip_file.write(
                r'tests\test_upload\squarecloud.app', 'squarecloud.app'
            )

    buffer.seek(0)

    return buffer.getvalue()


@pytest.mark.asyncio
class TestRequestListeners:
    async def test_normal_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='normal_test',
            main='main.py',
            memory=100,
        )
        await asyncio.sleep(10)
        upload_data: UploadData = await client.upload_app(
            File(create_zip(), filename='file.zip')
        )
        await client.delete_app(upload_data.id)

    async def test_invalid_main_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='invalid_main',
            main='index.js',
            memory=100,
        )
        with pytest.raises(errors.InvalidMain):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_missing_main_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='missing_main',
            main='',
            memory=100,
        )
        with pytest.raises(errors.MissingMainFile):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_few_memory_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='few_memory_test',
            main='main.py',
            memory=3999,
        )
        with pytest.raises(errors.FewMemory):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_invalid_display_name_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='test_' * 200,
            main='main.py',
            memory=100,
        )
        with pytest.raises(errors.InvalidDisplayName):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_missing_display_name_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='',
            main='main.py',
            memory=100,
        )
        with pytest.raises(errors.MissingDisplayName):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_bad_memory_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='memory_test',
            main='main.py',
            memory=1,
        )
        with pytest.raises(errors.BadMemory):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_missing_memory_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='memory_test',
            main='main.py',
            memory='',  # type: ignore
        )
        with pytest.raises(errors.MissingMemory):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_invalid_version_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='version_test',
            main='main.py',
            memory=100,
            version='invalid_version',  # type: ignore
        )
        with pytest.raises(errors.InvalidVersion):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)

    async def test_missing_version_upload(self):
        squarecloud.create_config_file(
            r'tests\test_upload',
            display_name='version_test',
            main='main.py',
            memory=100,
            version='',  # type: ignore
        )
        with pytest.raises(errors.MissingVersion):
            await asyncio.sleep(10)
            upload_data: UploadData = await client.upload_app(
                File(create_zip(), filename='file.zip')
            )
            await client.delete_app(upload_data.id)
