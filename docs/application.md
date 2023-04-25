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

    # managing application
    start = await app.start()
    print(start)  # Response(success)

    stop = await app.stop()
    print(stop)  # Response(success)

    restart = await app.restart()
    print(restart)  # Response(success)
    
    app_data = await app.data()
    print(app_data)  # AppData(...)

    backup = await app.backup()  # BackupData(downloadURL='https://squarecloud.app/dashboard/backup/123.zip')
    print(backup.downloadURL)  # 'https://squarecloud.app/dashboard/backup/123.zip'

    # [WARNING] this will delete your app, remember to have some backup saved
    delete = await app.delete()
    print(delete)  # Response(success)

    apps_list = await client.all_apps()
    for app in apps_list:
        print(app)  # <Application tag='my_cool_bot' id='12345678abcde'>
````

___

## Files managing

you can manage your application files easily, let's see some examples

### Obtaining file list:

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    files_list = await app.files_list(
        path='/')  # [FileInfo(...), FileInfo(...), FileInfo(...)]

    first_file = files_list[0]
    print(first_file.name)  # 'main.py'
    print(first_file.type)  # 'directory' or 'file'
    print(first_file.size)  # 2140
    print(first_file.lastModified)  # 1677112835000
```

### Reading a file:

`await app.read_file(path)` returns the bytes of your file

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    file_bytes = await app.read_file(path='main.py')
    print(file_bytes)  # b'01101111 01101001'
```

### Creating a file:

`await app.create_file()` creates a file in the specified directory

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    await app.create_file(
        path='/file.txt',
        file=square.File('file.txt')
    )
```

### Deleting a file:

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    await app.delete_file(path='/file.txt')
```

---

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
    print(app.cache.backup)  # None

    # Now, lets make some requests
    await app.status()
    await app.logs()
    await app.backup()

    # Now the cache is updated
    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
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
    await app.backup(update_cache=False)

    print(app.cache.status)  # None
    print(app.cache.logs)  # None
    print(app.cache.backup)  # None
```

you can also clear and update the cache manually using `cache.clear()` and `
cache.update()`

if the arguments you pass to `cache.update()` are not an instance
of `StatusData`, `LogsData`, or `BackupData` a SquareException
error will be raised

```python
import squarecloud as square

client = square.Client('API_KEY')


async def example():
    app = await client.app('application_id')

    status = await app.status()
    logs = await app.logs()
    backup = await app.backup()

    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
    print(app.cache.backup)  # BackupData(...)

    app.cache.clear()  # Clear cache

    print(app.cache.status)  # None
    print(app.cache.logs)  # None
    print(app.cache.backup)  # None

    app.cache.update(status, logs, backup)  # Update cache

    print(app.cache.status)  # StatusData(...)
    print(app.cache.logs)  # LogsData(...)
    print(app.cache.backup)  # BackupData(...)
```
