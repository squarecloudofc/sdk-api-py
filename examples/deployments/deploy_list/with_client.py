import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    deploys = await client.last_deploys('application_id')
    print(deploys)  # [[DeployData(...), DeployData(...), DeployData(...)]]


asyncio.run(example())
