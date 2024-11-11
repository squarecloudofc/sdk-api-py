import asyncio

import squarecloud as square
from squarecloud import Endpoint

client = square.Client('API_KEY', debug=False)


async def example() -> None:
    app = await client.app('application_id')

    @app.capture(endpoint=Endpoint.logs())
    async def on_logs_request(
        before: square.LogsData, after: square.LogsData
    ) -> None:
        if after != before:
            print(f'New logs!!! {after}')

    await app.logs()  # True
    await app.logs()  # False


asyncio.run(example)
