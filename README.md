[SquareCloud]: https://squarecloud.app

[SquareCloudAPI]: https://docs.squarecloud.app/api/introducao

[@alma]: https://github.com/Robert-Nogueira

# squarecloud-api

squarecloud-api is a wrapper for the [SquareCloudAPI] mainted by [@alma]


## Installing

````
pip install squarecloud-api
````


## Getting api key

to get your api key/token just go to the [SquareCloud] website and
register/login, after that go
to `dashboard` > `my account` > `Regenerate API/CLI KEY` and copy the key.

> ## [Documentation](docs/)
> - [application](docs/application.md)
> - [capture_listeners](docs/capture_listeners.md)
> - [client](docs/client.md)
> - [commit_and_upload](docs/commit_and_upload.md)
> - [request_listeners](docs/request_listeners.md)

## Basict usage
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
