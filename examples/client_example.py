import asyncio

import squarecloud as square
from squarecloud.data import StatusData

client = square.Client(api_key='API_KEY')


async def example() -> None:
    app_status: StatusData = await client.app_status('application_id')
    print(app_status)


asyncio.run(example)
