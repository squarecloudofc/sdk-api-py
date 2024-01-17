[Square Cloud]: https://squarecloud.app

[Square Cloud API]: https://docs.squarecloud.app/api-reference/

[@alma]: https://github.com/Robert-Nogueira

# squarecloud-api

squarecloud-api is a wrapper for the [Square Cloud API] mainted by [@alma]


## Installing

````
pip install squarecloud-api
````


## Getting api key

to get your api key/token just go to the [Square Cloud] website and
register/login, after that go
to `dashboard` > `my account` > `Regenerate API/CLI KEY` and copy the key.

> ## [Documentation](https://docs.squarecloud.app/sdks/py)
> you can read the documentation [**here**](https://docs.squarecloud.app/sdks/py).

## Basic usage
```python
import asyncio

import squarecloud as square

client = square.Client('API_KEY', debug=True)

async def main():
    status = await client.app_status(app_id='application_id')
    print(status)
    print(status.ram)
    print(status.cpu)

asyncio.run(main())
```

## License

MIT License
