import asyncio

import squarecloud as square

client = square.Client(...)


async def example() -> None:
    app = await client.app(app_id='application_id')
    file = square.File('path/to/you/file.zip')
    await app.commit(file=file)


asyncio.run(example)
