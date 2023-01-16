# Request Listeners

**read first [capture_listeners](capture_listeners.md)**

request listeners do pretty much the same thing
as [capture listeners](capture_listeners.md). But here you
use [Client](client.md), and the returns of all endpoints
are `squarecloud.http.Response` objects
```python
import squarecloud as square
from squarecloud import Endpoint

client = square.Client('API_KEY', debug=False)


@client.on_request(endpoint=Endpoint.logs())
async def on_logs_request(response):
    print(1, response)

    
@client.on_request(endpoint=Endpoint.user_me())
async def on_info_me_request(response):
    print(2, response)


async def example():
    await client.get_logs(app_id='abcdxyz')  # 1, Response(success)
    await client.me()  # 2, UserData(...)
    await client.me(avoid_listener=True)  # the listener is not called
```