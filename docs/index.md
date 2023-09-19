[SquareCloud]: https://squarecloud.app

[SquareCloud API]: https://docs.squarecloud.app/api-reference

[@alma]: https://github.com/Robert-Nogueira

<h1 align="center"> squarecloud-api</h1>

![Image title](./assets/banner-light.png#only-light)
![Image title](./assets/banner-dark.png#only-dark)

:simple-python: squarecloud-api é um wrapper/cli feita em python [SquareCloud API]
mantida por [@alma]

## Installing

<!-- termynal -->

````bash
$ pip install squarecloud-api
---> 100%
Successfully installed squarecloud-api
````

## :computer: Basic usage

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

