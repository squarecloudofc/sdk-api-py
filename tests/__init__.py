import io
import os
import zipfile

from dotenv import load_dotenv

from squarecloud.utils import ConfigFile

load_dotenv()

GITHUB_ACCESS_TOKEN: str = os.getenv('GITHUB_ACCESS_TOKEN')


def create_zip(config: ConfigFile | str):
    buffer = io.BytesIO()
    if isinstance(config, ConfigFile):
        config = config.content()

    with zipfile.ZipFile(buffer, 'w') as zip_file:
        zip_file.writestr(
           'requirements.txt', 'discord.py'
        )

        zip_file.writestr('main.py', "print('ok')")

        zip_file.writestr(
            'squarecloud.app', config
        )

    buffer.seek(0)

    return buffer.getvalue()
