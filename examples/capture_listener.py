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
