import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    app = await client.app('application_id')
    await app.move_file(
        origin='path/to/origin/file.py',
        dest='path/to/destination/file.py'
    )
