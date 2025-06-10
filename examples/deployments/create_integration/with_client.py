import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    webhook_url = await client.github_integration(
        'application_id', access_token='access_token'
    )
    print(webhook_url)


asyncio.run(example())