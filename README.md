[Square Cloud]: https://squarecloud.app

[Square Cloud API]: https://docs.squarecloud.app/api-reference/

[@allma]: https://github.com/Robert-Nogueira


<div align="center">
  <img alt="Square Cloud Banner" src="https://cdn.squarecloud.app/png/github-readme.png">
</div>

<h1 align="center">squarecloud-api</h1>

<p align="center">A Python SDK for consuming the <a href="https://squarecloud.app" target="_blank">Square Cloud</a> API.</p>

## Installation

````shell
pip install squarecloud-api
````

If you intend to use this SDK for command-line interface (CLI) operations, consider
installing it with pipx:
````shell
pipx install squarecloud-api
````

## Getting api key

to get your api key/token just go to the [Square Cloud] website and
register/login, after that go
to `dashboard` > `my account` > `Regenerate API/CLI KEY` and copy the key.

## Documentation
Visit our [official documentation](https://docs.squarecloud.app/sdks/py) for more information about how to use this library.

## Getting started

```python
import asyncio
import squarecloud as square

client = square.Client('API_KEY')

async def main():
    status = await client.app_status(app_id='application_id')
    print(status)
    print(status.ram)
    print(status.cpu)

asyncio.run(main())
```

## Contributing

Feel free to contribute with suggestions or bug reports at our [GitHub repository](https://github.com/squarecloudofc/wrapper-api-py).

## Authors

- [@allma]
