import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    logs = await client.get_logs('application_id')

    print(logs)  # LogsData(logs='Hello World!')
    print(logs.logs)  # 'Hello World'


asyncio.run(example)
