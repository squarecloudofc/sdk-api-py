import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')
    data = await app.data()
    print(data)  # AppData(...)


asyncio.run(example)
