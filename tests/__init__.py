import io
import os
import zipfile

from dotenv import load_dotenv

from squarecloud import Client, Endpoint
from squarecloud.app import Application
from squarecloud.utils import ConfigFile

load_dotenv()

GITHUB_ACCESS_TOKEN: str = os.getenv('GITHUB_ACCESS_TOKEN')


def create_zip(config: ConfigFile | str):
    buffer = io.BytesIO()
    if isinstance(config, ConfigFile):
        config = config.content()

    with zipfile.ZipFile(buffer, 'w') as zip_file:
        zip_file.writestr('requirements.txt', 'discord.py')

        zip_file.writestr('main.py', "print('ok')")

        zip_file.writestr('squarecloud.app', config)

    buffer.seek(0)

    return buffer.getvalue()


def _clear_listener_on_rerun(endpoint: Endpoint):
    def decorator(func):
        async def wrapper(self, app: Application | Client, *args, **kwargs):
            if app.get_listener(endpoint):
                app.remove_listener(endpoint)
            return await func(self, app=app)

        return wrapper

    return decorator
