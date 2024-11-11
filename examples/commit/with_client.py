import asyncio

import squarecloud as square

client = square.Client('API_KEY')


async def example() -> None:
    file = square.File('path/to/you/file.zip')
    await client.commit(file=file, app_id='application_id')


asyncio.run(example)
