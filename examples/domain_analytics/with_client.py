import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    analytics = await client.last_deploys('application_id')
    print(analytics)  # DomainAnalytics(...)


asyncio.run(example)
