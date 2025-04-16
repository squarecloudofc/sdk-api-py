import asyncio

import squarecloud as square

client = square.Client('API_KEY')


async def example() -> None:
    app = await client.app('application_id')

    # below we are setting "update_cache" to False,
    # so the cache will not be updated when the command is called,
    # thus remaining with the old cache
    await app.status(update_cache=False)
    await app.logs(update_cache=False)
    await app.backup(update_cache=False)

    print(app.cache.status)  # None
    print(app.cache.logs)  # None
    print(app.cache.backup)  # None


asyncio.run(example())
