import io
import os
import zipfile

from dotenv import load_dotenv

import squarecloud

load_dotenv()
client = squarecloud.Client(os.getenv('KEY'))


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
