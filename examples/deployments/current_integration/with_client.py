import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    webhook_url = await client.current_app_integration(
        'application_id',
    )
    print(webhook_url)


asyncio.run(example)
