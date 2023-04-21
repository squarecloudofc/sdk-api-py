### Application object

Using the client you can also get an application or a list of applications and
use them to manage your application.

````python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application id')

    # app information
    status = await app.status()  # StatusData(...)

    print(status.ram)  # '70MB'
    print(status.cpu)  # '5%'
    print(status.requests)  # 0
    print(status.network)  # {'total': '0 KB ↑ 0 KB ↓', 'now': '0 KB ↑ 0 KB ↓'}
    print(status.running)  # True | False
    print(status.storage)  # '0MB'

    # managing
    start = await app.start()  # Response(success)
    stop = await app.stop()  # Response(success)
    restart = await app.restart()  # Response(success)

    backup = await app.backup()  # BackupData(downloadURL='https://squarecloud.app/dashboard/backup/123.zip')
    print(
        backup.downloadURL)  # 'https://squarecloud.app/dashboard/backup/123.zip'

    # [WARNING] this will delete your app, remember to have some backup saved
    delete = await app.delete()  # Response(success)

    apps_list = await client.all_apps()
    for app in apps_list:
        print(app)  # <Application tag='my_cool_bot' id='12345678abcde'>
````

___

## Caching

When a request is made it returns information from the application and caches
it in the application itself. In case you need to access this information again
in a considerable amount of time, that is, if it is not worth making a new
request to have updated data. In cases like this you can
access `Application.cache`

```python
import squarecloud as square
from squarecloud.app import Application

client = square.Client('API_KEY')


async def example():
    app = await client.app('application_id')

    # See that since no request was made, the cache is empty
    print(app.cache.status)  # None
    print(app.cache.logs)  # None
    print(app.cache.full_logs)  # None
    print(app.cache.backup)  # None

    # Now, lets make some requests
    await app.status()
    await app.logs()
    await app.full_logs()
    await app.backup()

    # Now the cache is updated
    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
    print(app.cache.full_logs)  # FullLogsData(...)
    print(app.cache.backup)  # BackupData(...)
```

if for someone reason you don't want to update the cache, you can pass the
argument `update_cache=False`

```python
import squarecloud as square

client = square.Client('API_KEY')


async def example():
    app = await client.app('application_id')

    # below we are setting "update_cache" to False,
    # so the cache will not be updated when the command is called,
    # thus remaining with the old cache
    await app.status(update_cache=False)
    await app.logs(update_cache=False)
    await app.full_logs(update_cache=False)
    await app.backup(update_cache=False)

    print(app.cache.status)  # None
    print(app.cache.logs)  # None
    print(app.cache.full_logs)  # None
    print(app.cache.backup)  # None
```

you can also clear and update the cache manually using `cache.clear()` and `
cache.update()`

if the arguments you pass to `cache.update()` are not an instance
of `StatusData`, `LogsData`, `FullLogsData` or `BackupData` a SquareException
error will be raised

```python
import squarecloud as square

client = square.Client('API_KEY')


async def example():
    app = await client.app('application_id')

    status = await app.status()
    logs = await app.logs()
    full_logs = await app.full_logs()
    backup = await app.backup()

    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
    print(app.cache.full_logs)  # FullLogsData(...)
    print(app.cache.backup)  # BackupData(...)

    app.cache.clear()  # Clear cache

    print(app.cache.status)  # None
    print(app.cache.logs)  # None
    print(app.cache.full_logs)  # None
    print(app.cache.backup)  # None

    app.cache.update(status, logs, full_logs, backup)  # Update cache

    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
    print(app.cache.full_logs)  # FullLogsData(...)
    print(app.cache.backup)  # BackupData(...)
```
