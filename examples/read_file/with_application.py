import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    file_bytes = await app.read_file(path='main.py')

    print(file_bytes)  # b'01101000 01101001'
