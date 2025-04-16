import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')
    analytics = await app.domain_analytics()
    print(analytics)  # DomainAnalytics(...)


asyncio.run(example)
