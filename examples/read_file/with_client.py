import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    file_bytes = await client.read_app_file(
        app_id='application_id', path='main.py'
    )

    print(file_bytes)  # b'01101000 01101001'


asyncio.run(example)
