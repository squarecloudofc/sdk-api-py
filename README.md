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

<h1>How to use logs listener</h1>
<h2>This is a low-level decorator that allow you to receive and handle logs in your code</h2>
<h3>We have two ways to use this function</h3>

First - Specifying the app_ids in **client object**
````py
from squarecloud import square
client = square.Client(api_key='YOUR KEY', app_ids=['SquareID 1', 'SquareID 2', 'SquareID 3', ...])

@client.capture_logs(just_last=True)
async def capturar_logs(logs, app):
    print(logs)
    print(app)
    #Hello, i'm Wumpus!
    #Wumpus Bot
````

Second - Specifying the app_ids in the **decorator**
````py
from squarecloud import square
client = square.Client(api_key='YOUR KEY')

@client.capture_logs(apps=['SquareID 1', 'SquareID 2', 'SquareID 3', ...], just_last=True)
async def capturar_logs(logs, app):
    print(logs)
    print(app)
    #Hello, i'm Wumpus!
    #Wumpus Bot
````

<h1>How it works?</h1>
<h3>The terminals are updated on average every 10 seconds, please note that they will not be updated in real time due to API limitations (hence it is called a low-level function)</h3>
<h3>Your function will receive the logs and the nametag of the application who invoked the terminal.</h3>
<h4>
Also note that this may consume some number of requests depending on the number of applications you entered in the app_ids parameter.</h4>

<h1>The parameters</h1>
<h3>The two possible parameter in this listener is <b>app_ids</b> and <b>just_last</b></h3>
<h3>If <b>just_last</b> is <b>True</b>, just last logs will be sended to your function (No repeated logs).</h3>
<h3>Else, it will return the full terminal with repeated logs</h3>
<h3>The <b>app_ids</b> parameter will be a list with the id(s) of the application(s) that will be pulled in the listener/event, note that it is possible to register an id in more than one listener at the same time, it will only be possible to use the id in one listener at a time. If you try to register the same id in several listeners it will return a warning</h3>



### Debug mode
Every time a request is made logs are displayed in the terminal containing useful informations, You can disable this by setting the `debug` parameter to False for the client, this value by default is True.
````py
import squarecloud as square

client = square.Client(api_key='API KEY', debug=False) # no logs
````

## License
MIT License
