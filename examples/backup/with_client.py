import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    backup = await client.backup('application_id')
    print(backup.downloadURL)  # https://squarecloud.app/dashboard/backup/f.zip


asyncio.run(example)
