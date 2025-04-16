import os

from dotenv import load_dotenv

import squarecloud
from scripts import run_async_script

load_dotenv()
client = squarecloud.Client(os.getenv('KEY'))


@run_async_script
async def delete_test_apps() -> None:
    for app in await client.all_apps():
        if '_test' in app.name:
            await app.delete()
            print(f'\U0001f5d1 Deleted app {app.name}, with id {app.id}...')


if __name__ == '__main__':
    delete_test_apps()
