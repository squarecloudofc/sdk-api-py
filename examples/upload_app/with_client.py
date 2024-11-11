import asyncio

import squarecloud as square

client = square.Client(...)


async def example() -> None:
    file = square.File('path/to/you/file.zip')
    await client.upload_app(file=file)


asyncio.run(example)
