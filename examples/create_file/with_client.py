import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    await client.create_app_file(
        app_id='application_id', path='/file.txt', file=square.File('file.txt')
    )


asyncio.run(example())
