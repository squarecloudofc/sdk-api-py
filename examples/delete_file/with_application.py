import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')

    await app.delete_file(path='/file.txt')


asyncio.run(example())
