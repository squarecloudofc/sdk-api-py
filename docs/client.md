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

    full_logs = await client.get_logs(app_id)
    print(full_logs)  # FullLogsData(logs='https://squarecloud.app/dashboard/logs/...')
    print(full_logs.logs)  # 'https://squarecloud.app/dashboard/logs/...'

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
    start = await client.start_app(app_id)  # Response(success)
    stop = await client.stop_app(app_id)  # Response(success)
    restart = await client.restart_app(app_id)  # Response(success)
    commit = await client.commit(app_id, file=square.File('path/to/your/file'))
    
    backup = await client.backup(app_id)  # BackupData(downloadURL='https://squarecloud.app/dashboard/backup/123.zip')
    print(backup.downloadURL)  # 'https://squarecloud.app/dashboard/backup/123.zip'
    
    
    # [WARNING] this will delete your app, remember to have some backup saved
    delete = await client.delete_app(app_id)  # Response(success)
````
___
### Debug mode
Every time a request is made logs are displayed in the terminal containing
useful information, You can disable this by setting the `debug` parameter to
False for the client, this value by default is True.
````py
import squarecloud as square

client = square.Client(api_key='API KEY', debug=False)  # no logs
````