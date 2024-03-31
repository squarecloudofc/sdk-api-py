import os

from dotenv import load_dotenv

from scripts import run_async_script
import squarecloud
from squarecloud import *

load_dotenv()
client = squarecloud.Client(os.getenv('KEY'))


@run_async_script
async def delete_test_apps():
    for app in await client.all_apps():
        if 'test' in app.tag:
            await app.delete()
            print(f'\U0001F5D1 Deleted app {app.tag}, with id {app.id}...')
