[SquareCloud]: https://squarecloud.app
[API]: https://docs.squarecloud.app/api/introducao
[@alma]: https://github.com/Robert-Nogueira


# squarecloud-api
squarecloud-api is a wrapper of the [API] of [SquareCloud] made by [@alma]

## Installing
````
pip install squarecloud-api
````

## Starting
### Where to get my api key?
to get your api key/token just go to the [SquareCloud] website and register/login, after that go to `dashboard` > `my account` > `Regenerate API/CLI KEY` and copy the key.

### The client instance
with the client you can get information about your application
````python
import squarecloud as square

client = square.Client(api_key='API KEY')

app_id = 'application id'
async def example():
    logs = await client.get_logs(app_id)
    print(logs)

    complete_logs = await client.get_logs(app_id)
    print(complete_logs)

    status = await client.app_status(app_id)
    print(status.ram)
    print(status.cpu)
    print(status.requests)
    print(status.network)
    print(status.running)
    print(status.storage)

````
you can also manage your application
````python
import squarecloud as square

# you can define if you want debug logs to be shown or not
# this value by default is True
client = square.Client(api_key='API KEY')

app_id = 'application id'
async def example():
    await client.backup(app_id)
    await client.start_app(app_id)
    await client.stop_app(app_id)
    await client.restart_app(app_id)
    await client.delete_app(app_id)
    await client.commit(app_id, file=square.File('path/to/your/file'))

````
### Application object
Using the client you can also get an application or a list of applications and use them to manage your application.
````python
import squarecloud as square

client = square.Client(api_key='API KEY')

async def example():
    app = await client.app('application id')

    # app information
    status = await app.status()
    print(status.ram)
    print(status.cpu)
    print(status.requests)
    print(status.network)
    print(status.running)
    print(status.storage)
    
    # managing
    await app.stop()
    await app.start()
    await app.restart()
    await app.backup()
    await app.delete()
    await app.backup()
    await app.commit(square.File('path/to/your/file'))
    
    apps_list = await client.all_apps()
    for app in apps_list:
        print(app)

````
### Debug mode
Every time a request is made logs are displayed in the terminal containing useful informations, You can disable this by setting the `debug` parameter to False for the client, this value by default is True.
````py
import squarecloud as square

client = square.Client(api_key='API KEY', debug=False) # no logs
````

## License
MIT License
