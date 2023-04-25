# Client

## Fetching app information

````python
import squarecloud as square

client = square.Client(api_key='API KEY')

app_id = 'application_id'


async def example():
    logs = await client.get_logs(app_id)
    print(logs)  # LogsData(logs='Hello World!')
    print(logs.logs)  # 'Hello World'

    status = await client.app_status(app_id)  # StatusData(...)

    print(status.ram)  # '70MB'
    print(status.cpu)  # '5%'
    print(status.requests)  # 0
    print(status.network)  # {'total': '0 KB ↑ 0 KB ↓', 'now': '0 KB ↑ 0 KB ↓'}
    print(status.running)  # True | False
    print(status.storage)  # '0MB'

````

## Managing your application

````python
import squarecloud as square

# you can define if you want debug logs to be shown or not
# this value by default is True
client = square.Client(api_key='API KEY')

app_id = 'application id'


async def example():
    start = await client.start_app(app_id)
    print(start)  # Response(success)

    stop = await client.stop_app(app_id)
    print(stop)  # Response(success)

    restart = await client.restart_app(app_id)
    print(restart)  # Response(success)

    commit = await client.commit(app_id, file=square.File('path/to/your/file'))

    backup = await client.backup(app_id)  # BackupData(downloadURL='https://squarecloud.app/dashboard/backup/123.zip')
    print(backup.downloadURL)  # 'https://squarecloud.app/dashboard/backup/123.zip'

    # [WARNING] this will delete your app, remember to have some backup saved
    delete = await client.delete_app(app_id)  # Response(success)
````

## Files managing

you can manage your application files easily, let's see some examples

### Obtaining file list:

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    files_list = await client.app_files_list(app_id='application_id', path='/')  # [FileInfo(...), FileInfo(...), FileInfo(...)]

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
    file_bytes = await client.read_app_file(app_id='application_id', path='main.py')
    print(file_bytes)  # b'01101111 01101001'
```

### Creating a file:

`await app.create_file()` creates a file in the specified directory

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    await client.create_app_file(
        app_id='application_id',
        path='/file.txt',
        file=square.File('file.txt')
    )
```

### Deleting a file:

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    await client.delete_app_file(app_id='application_id', path='/file.txt')
```

---

### Squarecloud Statistics

you can get the squarecloud statistics using `Client.statistics()`

```python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    statistics = await client.statistics()
    print(statistics)  # StatisticsData(...)
```

___

### Debug mode

Every time a request is made logs are displayed in the terminal containing
useful information, You can disable this by setting the `debug` parameter to
False for the client, this value by default is True.

````py
import squarecloud as square

client = square.Client(api_key='API KEY', debug=False)  # no logs
````