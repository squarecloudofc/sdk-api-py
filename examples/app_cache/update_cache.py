import squarecloud as square

client = square.Client('API_KEY')


async def example():
    app = await client.app('application_id')

    status = await app.status()
    logs = await app.logs()
    backup = await app.backup()

    app.cache.clear()  # Clear cache

    app.cache.update(status, logs, backup)  # Update cache

    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
    print(app.cache.backup)  # BackupData(...)
