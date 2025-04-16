import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    await client.restart_app('application_id')


asyncio.run(example)
