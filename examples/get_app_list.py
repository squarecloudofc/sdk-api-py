import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    apps = await client.all_apps()
    print(apps)  # list[<Application tag='example' id='application_id'>]


asyncio.run(example)
