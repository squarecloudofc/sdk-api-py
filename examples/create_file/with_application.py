import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')

    await app.create_file(path='/file.txt', file=square.File('file.txt'))


asyncio.run(example())
