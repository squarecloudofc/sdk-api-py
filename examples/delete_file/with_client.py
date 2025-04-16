import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    await client.delete_app_file(app_id='application_id', path='/file.txt')


asyncio.run(example())
