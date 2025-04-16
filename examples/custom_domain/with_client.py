import asyncio

import squarecloud as square

client = square.Client(api_key='API KEY')


async def example() -> None:
    await client.set_custom_domain(
        'application_id', 'my_custom_domain.example.br'
    )


asyncio.run(example())
