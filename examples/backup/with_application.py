import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')
    backup = await app.backup()
    print(backup.url)  # https://squarecloud.app/dashboard/backup/f.zip


asyncio.run(example())
