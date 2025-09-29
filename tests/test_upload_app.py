import asyncio
import time

import pytest

from squarecloud import Client, File, errors
from squarecloud.data import UploadData
from squarecloud.utils import ConfigFile

from . import create_zip

_last_upload_time = 0
UPLOAD_RATELIMIT_IN_SECONDS = 3

async def upload_app(client: Client, config: ConfigFile | str) -> UploadData:
    global _last_upload_time
    elapsed = time.time() - _last_upload_time

    if elapsed < UPLOAD_RATELIMIT_IN_SECONDS:
        await asyncio.sleep(UPLOAD_RATELIMIT_IN_SECONDS - elapsed)

    _last_upload_time = time.time()
    return await client.upload_app(
        File(create_zip(config), filename='file.zip')
    )



@pytest.mark.asyncio(scope='session')
@pytest.mark.upload
class TestRequestListeners:
    async def test_normal_upload(self, client: Client):
        config = ConfigFile(
            display_name='normal_test',
            main='main.py',
            memory=256,
        )

        upload_data: UploadData = await upload_app(client, config)
        await client.delete_app(upload_data.id)

    async def test_invalid_main_upload(self, client: Client):
        config = ConfigFile(
            display_name='invalid_main',
            main='invalid_main.py',
            memory=256,
        )
        with pytest.raises(errors.InvalidMain):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    async def test_missing_main_upload(self, client: Client):
        config = ConfigFile(
            display_name='missing_main',
            main='',
            memory=256,
        )
        with pytest.raises(errors.MissingMainFile):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    @pytest.mark.skip
    async def test_few_memory_upload(self, client: Client):
        config = ConfigFile(
            display_name='few_memory_test',
            main='main.py',
            memory=9999,
        )
        with pytest.raises(errors.FewMemory):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    async def test_invalid_display_name_upload(self, client: Client):
        config = ConfigFile(
            display_name='test_' * 200,
            main='main.py',
            memory=256,
        )
        with pytest.raises(errors.InvalidDisplayName):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    async def test_missing_display_name_upload(self, client: Client):
        config = ConfigFile(
            display_name='',
            main='main.py',
            memory=256,
        )
        with pytest.raises(errors.MissingDisplayName):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    async def test_bad_memory_upload(self, client: Client):
        config = ConfigFile(
            display_name='memory_test',
            main='main.py',
            memory=256,
        ).content()
        with pytest.raises(errors.BadMemory):
            config = config.replace('256', '1')
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    async def test_missing_memory_upload(self, client: Client):
        config = ConfigFile(
            display_name='memory_test', main='main.py', memory=256
        ).content()
        config = config.replace('256', '')
        with pytest.raises(errors.MissingMemory):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    async def test_invalid_version_upload(self, client: Client):
        config = ConfigFile(
            display_name='version_test',
            main='main.py',
            memory=256,
        ).content()
        config = config.replace('recommended', 'invalid_version')
        with pytest.raises(errors.InvalidVersion):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)

    async def test_missing_version_upload(self, client: Client):
        config = ConfigFile(
            display_name='version_test',
            main='main.py',
            memory=256,
        ).content()
        config = config.replace('recommended', '')
        with pytest.raises(errors.MissingVersion):
            upload_data: UploadData = await upload_app(client, config)
            await client.delete_app(upload_data.id)
