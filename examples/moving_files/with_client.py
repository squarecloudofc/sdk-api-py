import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    await client.move_app_file(
        app_id='application_id',
        origin='path/to/origin/file.py',
        dest='path/to/destination/file.py'
    )
