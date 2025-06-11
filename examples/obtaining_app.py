import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application id')
    print(app)  # <Application tag='example' id='application_id'>


asyncio.run(example())
