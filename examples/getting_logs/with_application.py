import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')
    logs = await app.logs()

    print(logs)  # LogsData(logs='Hello World!')
    print(logs.logs)  # 'Hello World'


asyncio.run(example)
