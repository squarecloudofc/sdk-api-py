import asyncio

import squarecloud as square

client = square.Client('API_KEY')


async def example() -> None:
    app = await client.app('application_id')

    await app.status()
    await app.logs()
    await app.backup()

    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
    print(app.cache.backup)  # BackupData(...)

    app.cache.clear()  # Clear cache

    print(app.cache.status)  # None
    print(app.cache.logs)  # None
    print(app.cache.backup)  # None


asyncio.run(example)
