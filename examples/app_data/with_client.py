import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    data = await client.app_data('application_id')
    print(data)  # AppData(...)


asyncio.run(example)
