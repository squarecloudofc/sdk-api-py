import asyncio

import squarecloud as square
from squarecloud import Endpoint

client = square.Client('API_KEY')


@client.on_request(endpoint=Endpoint.logs())
async def on_logs_request(response: square.Response) -> None:
    print(1, response)


@client.on_request(endpoint=Endpoint.user())
async def on_user_info_request(response: square.Response) -> None:
    print(2, response)


async def example() -> None:
    await client.get_logs(app_id='application_id')  # 1, Response(success)
    await client.user()  # 2, UserData(...)
    await client.user(avoid_listener=True)  # the listener is not called


asyncio.run(example())
