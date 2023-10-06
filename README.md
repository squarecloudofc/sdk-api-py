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

> ## [Documentation](docs/)
> - [application](https://github.com/squarecloudofc/wrapper-api-py/blob/main/docs/application.md)
> - [capture_listeners](https://github.com/squarecloudofc/wrapper-api-py/blob/main/docs/capture_listeners.md)
> - [client](https://github.com/squarecloudofc/wrapper-api-py/blob/main/docs/client.md)
> - [commit_and_upload](https://github.com/squarecloudofc/wrapper-api-py/blob/main/docs/commit_and_upload.md)
> - [request_listeners](https://github.com/squarecloudofc/wrapper-api-py/blob/main/docs/request_listeners.md)

## Basic usage
```python
import squarecloud as square
import asyncio

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
