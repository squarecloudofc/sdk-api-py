[SquareCloud]: https://squarecloud.app
[API]: https://docs.squarecloud.app/api/introducao
[@alma]: https://github.com/Robert-Nogueira


# squarecloud-api
### squarecloud-api is a wrapper of the [API] of [SquareCloud] made by [@alma]
## Installing
````
pip install squarecloud-api
````

## Starting
### Where to get my api key?
to get your api key/token just go to the [SquareCloud] website and register/login, after that go to `dashboard` > `my account` > `Regenerate API/CLI KEY` and copy the key.

## Getting information from your application

````python
import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    logs = await client.get_logs(app_id='id of your application')
    print(logs)

    complete_logs = await client.get_logs(app_id='id of your application')
    print(complete_logs)

    status = await client.app_status(app_id='id of your application')
    print(status.ram)
    print(status.cpu)
    print(status.requests)
    print(status.network)
    print(status.running)
    print(status.storage)

````
### Managing your application

````python
import squarecloud as square

# you can define if you want debug logs to be shown or not
# this value by default is True
client = square.Client(api_key='API KEY', debug=False)


async def example():
    await client.backup(app_id='id of your application')
    await client.start_app(app_id='id of your application')
    await client.stop_app(app_id='id of your application')
    await client.restart_app(app_id='id of your application')
    await client.delete_app(app_id='id of your application')
    await client.commit(app_id='id of your application', file=square.File('path/to/your/file'))
````

## License
MIT License
