import asyncio
import os

import pytest
from dotenv import load_dotenv
from rich.status import Status

from squarecloud import Client, File, FileInfo, UploadData
from squarecloud.app import Application
from squarecloud.utils import ConfigFile
from tests import create_zip


@pytest.fixture(scope='session')
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def client() -> Client:
    load_dotenv()
    return Client(os.getenv('KEY'), log_level='DEBUG')


@pytest.fixture(scope='session')
async def app(client: Client) -> Application:
    config = ConfigFile(
        display_name='normal_test',
        main='main.py',
        memory=256,
    )
    with Status('uploading test application...', spinner='point'):
        upload_data: UploadData = await client.upload_app(
            File(create_zip(config), filename='file.zip')
        )
    yield await client.app(upload_data.id)
    await client.delete_app(upload_data.id)


@pytest.fixture(scope='module')
async def app_files(app: Application) -> list[FileInfo]:
    return await app.files_list(path='/')
