import squarecloud as square

client = square.Client(api_key='API KEY')


async def example():
    await client.start_app('application_id')
