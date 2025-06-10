import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')
    webhook_url = await app.current_integration()
    print(webhook_url)


asyncio.run(example())
