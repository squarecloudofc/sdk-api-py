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
    def print_cache(app: Application):
        cache = app.cache
        print(cache.status)
        print(cache.logs)
        print(cache.full_logs)
        print(cache.backup)
    
    app = await client.app('application_id')
    await app.status()
    print_cache(app)
```