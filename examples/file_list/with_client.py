import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    files_list = await client.app_files_list(app_id='application_id', path='/')

    for file in files_list:
        print(file.name)  # 'main.py'

        print(file.type)  # 'directory' or 'file'

        print(file.size)  # 2140

        print(file.lastModified)  # 1677112835000


asyncio.run(example)
