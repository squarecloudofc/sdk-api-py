# Capture Listeners

_this implementation is based on a [suggestion](https://github.com/squarecloudofc/wrapper-api-py/pull/1) made
by [@Mudinho](https://github.com/zRickz), thanks for contributing_

Sometimes it's very useful to have listeners, with them, you can implement
features that need to be called whenever "something" is done in your
application.

For example, imagine that every time a request for the '/logs' route is made,
my application executes some task that checks if the new logs are different
from the old ones. Well, let's see how this could be done:

```python
import squarecloud as square
from squarecloud import Endpoint

client = square.Client('API_KEY', debug=False)
apps = await client.all_apps()
app = apps[0]


@app.capture(endpoint=Endpoint.logs())
async def on_logs_request(before, after):
    if after != before:
        print(f'New logs!!! {after}')


async def example():
    await app.logs()  # True
    await app.logs()  # False
    await app.logs(avoid_listener=True)  # the listener is not called
```

As you may have noticed, the first time the comparison between the logs
happens `after != before` returns `True`, this happens precisely
because `after` is equal to `LogsData(logs=None)`, as there is nothing yet
stored in internal cache.

**Another information about this decorator**

- if you use discord.py or some fork (most likely you do), you should
  be familiar with the fact that what differentiates events is the name
  of the functions that the decorator involves, but here it differs, to know
  which
  api route the decorator needs to "watch" the endpoint parameter is used which
  takes an `Endpoint` class, so the name of the function that the decorator
  wraps
  It's up to you.
- the function that the decorator wraps can actually be anything you
  be a callable. This includes normal functions, coroutines, and even
  classes(`__init__` will be called)
- if the endpoint is not an `Endpoint.app_status()`
  , `Endpoints.logs()`, `Endpoints.full_logs()` or `Endpoints.backup()`
  only one `response` parameter (of type `squarecloud.http.Response`) will be
  returned
