import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    app = await client.app('application_id')  # StatusData(...)
    status = await app.status()

    print(status.ram)  # '70MB'
    print(status.cpu)  # '5%'
    print(status.requests)  # 0
    print(status.network)  # {'total': '0 KB ↑ 0 KB ↓', 'now': '0 KB ↑ 0 KB ↓'}
    print(status.running)  # True | False
    print(status.storage)  # '0MB'


asyncio.run(example)
